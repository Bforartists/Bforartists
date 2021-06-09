/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Copyright 2021, Blender Foundation.
 */

#include "COM_FullFrameExecutionModel.h"
#include "COM_Debug.h"
#include "COM_ExecutionGroup.h"
#include "COM_ReadBufferOperation.h"
#include "COM_WorkScheduler.h"

#include "BLT_translation.h"

#ifdef WITH_CXX_GUARDEDALLOC
#  include "MEM_guardedalloc.h"
#endif

namespace blender::compositor {

FullFrameExecutionModel::FullFrameExecutionModel(CompositorContext &context,
                                                 SharedOperationBuffers &shared_buffers,
                                                 Span<NodeOperation *> operations)
    : ExecutionModel(context, operations),
      active_buffers_(shared_buffers),
      num_operations_finished_(0),
      work_mutex_(),
      work_finished_cond_()
{
  priorities_.append(eCompositorPriority::High);
  if (!context.isFastCalculation()) {
    priorities_.append(eCompositorPriority::Medium);
    priorities_.append(eCompositorPriority::Low);
  }

  BLI_mutex_init(&work_mutex_);
  BLI_condition_init(&work_finished_cond_);
}

FullFrameExecutionModel::~FullFrameExecutionModel()
{
  BLI_condition_end(&work_finished_cond_);
  BLI_mutex_end(&work_mutex_);
}

void FullFrameExecutionModel::execute(ExecutionSystem &exec_system)
{
  const bNodeTree *node_tree = this->context_.getbNodeTree();
  node_tree->stats_draw(node_tree->sdh, TIP_("Compositing | Initializing execution"));

  DebugInfo::graphviz(&exec_system);

  determine_areas_to_render_and_reads();
  render_operations(exec_system);
}

void FullFrameExecutionModel::determine_areas_to_render_and_reads()
{
  const bool is_rendering = context_.isRendering();
  const bNodeTree *node_tree = context_.getbNodeTree();

  rcti area;
  for (eCompositorPriority priority : priorities_) {
    for (NodeOperation *op : operations_) {
      op->setbNodeTree(node_tree);
      if (op->isOutputOperation(is_rendering) && op->getRenderPriority() == priority) {
        get_output_render_area(op, area);
        determine_areas_to_render(op, area);
        determine_reads(op);
      }
    }
  }
}

Vector<MemoryBuffer *> FullFrameExecutionModel::get_input_buffers(NodeOperation *op)
{
  const int num_inputs = op->getNumberOfInputSockets();
  Vector<MemoryBuffer *> inputs_buffers(num_inputs);
  for (int i = 0; i < num_inputs; i++) {
    NodeOperation *input_op = op->get_input_operation(i);
    inputs_buffers[i] = active_buffers_.get_rendered_buffer(input_op);
  }
  return inputs_buffers;
}

MemoryBuffer *FullFrameExecutionModel::create_operation_buffer(NodeOperation *op)
{
  rcti op_rect;
  BLI_rcti_init(&op_rect, 0, op->getWidth(), 0, op->getHeight());

  const DataType data_type = op->getOutputSocket(0)->getDataType();
  /* TODO: We should check if the operation is constant instead of is_set_operation. Finding a way
   * to know if an operation is constant has to be implemented yet. */
  const bool is_a_single_elem = op->get_flags().is_set_operation;
  return new MemoryBuffer(data_type, op_rect, is_a_single_elem);
}

void FullFrameExecutionModel::render_operation(NodeOperation *op, ExecutionSystem &exec_system)
{
  Vector<MemoryBuffer *> input_bufs = get_input_buffers(op);

  const bool has_outputs = op->getNumberOfOutputSockets() > 0;
  MemoryBuffer *op_buf = has_outputs ? create_operation_buffer(op) : nullptr;
  Span<rcti> areas = active_buffers_.get_areas_to_render(op);
  op->render(op_buf, areas, input_bufs, exec_system);
  active_buffers_.set_rendered_buffer(op, std::unique_ptr<MemoryBuffer>(op_buf));

  operation_finished(op);
}

/**
 * Render output operations in order of priority.
 */
void FullFrameExecutionModel::render_operations(ExecutionSystem &exec_system)
{
  const bool is_rendering = context_.isRendering();

  WorkScheduler::start(this->context_);
  for (eCompositorPriority priority : priorities_) {
    for (NodeOperation *op : operations_) {
      if (op->isOutputOperation(is_rendering) && op->getRenderPriority() == priority) {
        render_output_dependencies(op, exec_system);
        render_operation(op, exec_system);
      }
    }
  }
  WorkScheduler::stop();
}

/**
 * Returns all dependencies from inputs to outputs. A dependency may be repeated when
 * several operations depend on it.
 */
static Vector<NodeOperation *> get_operation_dependencies(NodeOperation *operation)
{
  /* Get dependencies from outputs to inputs. */
  Vector<NodeOperation *> dependencies;
  Vector<NodeOperation *> next_outputs;
  next_outputs.append(operation);
  while (next_outputs.size() > 0) {
    Vector<NodeOperation *> outputs(next_outputs);
    next_outputs.clear();
    for (NodeOperation *output : outputs) {
      for (int i = 0; i < output->getNumberOfInputSockets(); i++) {
        next_outputs.append(output->get_input_operation(i));
      }
    }
    dependencies.extend(next_outputs);
  }

  /* Reverse to get dependencies from inputs to outputs. */
  std::reverse(dependencies.begin(), dependencies.end());

  return dependencies;
}

void FullFrameExecutionModel::render_output_dependencies(NodeOperation *output_op,
                                                         ExecutionSystem &exec_system)
{
  BLI_assert(output_op->isOutputOperation(context_.isRendering()));
  Vector<NodeOperation *> dependencies = get_operation_dependencies(output_op);
  for (NodeOperation *op : dependencies) {
    if (!active_buffers_.is_operation_rendered(op)) {
      render_operation(op, exec_system);
    }
  }
}

/**
 * Determines all operations areas needed to render given output area.
 */
void FullFrameExecutionModel::determine_areas_to_render(NodeOperation *output_op,
                                                        const rcti &output_area)
{
  BLI_assert(output_op->isOutputOperation(context_.isRendering()));

  Vector<std::pair<NodeOperation *, const rcti>> stack;
  stack.append({output_op, output_area});
  while (stack.size() > 0) {
    std::pair<NodeOperation *, rcti> pair = stack.pop_last();
    NodeOperation *operation = pair.first;
    const rcti &render_area = pair.second;
    if (active_buffers_.is_area_registered(operation, render_area)) {
      continue;
    }

    active_buffers_.register_area(operation, render_area);

    const int num_inputs = operation->getNumberOfInputSockets();
    for (int i = 0; i < num_inputs; i++) {
      NodeOperation *input_op = operation->get_input_operation(i);
      rcti input_op_rect, input_area;
      BLI_rcti_init(&input_op_rect, 0, input_op->getWidth(), 0, input_op->getHeight());
      operation->get_area_of_interest(input_op, render_area, input_area);

      /* Ensure area of interest is within operation bounds, cropping areas outside. */
      BLI_rcti_isect(&input_area, &input_op_rect, &input_area);

      stack.append({input_op, input_area});
    }
  }
}

/**
 * Determines reads to receive by operations in output operation tree (i.e: Number of dependent
 * operations each operation has).
 */
void FullFrameExecutionModel::determine_reads(NodeOperation *output_op)
{
  BLI_assert(output_op->isOutputOperation(context_.isRendering()));

  Vector<NodeOperation *> stack;
  stack.append(output_op);
  while (stack.size() > 0) {
    NodeOperation *operation = stack.pop_last();
    const int num_inputs = operation->getNumberOfInputSockets();
    for (int i = 0; i < num_inputs; i++) {
      NodeOperation *input_op = operation->get_input_operation(i);
      if (!active_buffers_.has_registered_reads(input_op)) {
        stack.append(input_op);
      }
      active_buffers_.register_read(input_op);
    }
  }
}

/**
 * Calculates given output operation area to be rendered taking into account viewer and render
 * borders.
 */
void FullFrameExecutionModel::get_output_render_area(NodeOperation *output_op, rcti &r_area)
{
  BLI_assert(output_op->isOutputOperation(context_.isRendering()));

  /* By default return operation bounds (no border). */
  const int op_width = output_op->getWidth();
  const int op_height = output_op->getHeight();
  BLI_rcti_init(&r_area, 0, op_width, 0, op_height);

  const bool has_viewer_border = border_.use_viewer_border &&
                                 (output_op->get_flags().is_viewer_operation ||
                                  output_op->get_flags().is_preview_operation);
  const bool has_render_border = border_.use_render_border;
  if (has_viewer_border || has_render_border) {
    /* Get border with normalized coordinates. */
    const rctf *norm_border = has_viewer_border ? border_.viewer_border : border_.render_border;

    /* Return de-normalized border. */
    BLI_rcti_init(&r_area,
                  norm_border->xmin * op_width,
                  norm_border->xmax * op_width,
                  norm_border->ymin * op_height,
                  norm_border->ymax * op_height);
  }
}

/**
 * Multi-threadedly execute given work function passing work_rect splits as argument.
 */
void FullFrameExecutionModel::execute_work(const rcti &work_rect,
                                           std::function<void(const rcti &split_rect)> work_func)
{
  if (is_breaked()) {
    return;
  }

  /* Split work vertically to maximize continuous memory. */
  const int work_height = BLI_rcti_size_y(&work_rect);
  const int num_sub_works = MIN2(WorkScheduler::get_num_cpu_threads(), work_height);
  const int split_height = num_sub_works == 0 ? 0 : work_height / num_sub_works;
  int remaining_height = work_height - split_height * num_sub_works;

  Vector<WorkPackage> sub_works(num_sub_works);
  int sub_work_y = work_rect.ymin;
  int num_sub_works_finished = 0;
  for (int i = 0; i < num_sub_works; i++) {
    int sub_work_height = split_height;

    /* Distribute remaining height between sub-works. */
    if (remaining_height > 0) {
      sub_work_height++;
      remaining_height--;
    }

    WorkPackage &sub_work = sub_works[i];
    sub_work.type = eWorkPackageType::CustomFunction;
    sub_work.execute_fn = [=, &work_func, &work_rect]() {
      if (is_breaked()) {
        return;
      }
      rcti split_rect;
      BLI_rcti_init(
          &split_rect, work_rect.xmin, work_rect.xmax, sub_work_y, sub_work_y + sub_work_height);
      work_func(split_rect);
    };
    sub_work.executed_fn = [&]() {
      BLI_mutex_lock(&work_mutex_);
      num_sub_works_finished++;
      if (num_sub_works_finished == num_sub_works) {
        BLI_condition_notify_one(&work_finished_cond_);
      }
      BLI_mutex_unlock(&work_mutex_);
    };
    WorkScheduler::schedule(&sub_work);
    sub_work_y += sub_work_height;
  }
  BLI_assert(sub_work_y == work_rect.ymax);

  WorkScheduler::finish();

  /* Ensure all sub-works finished.
   * TODO: This a workaround for WorkScheduler::finish() not waiting all works on queue threading
   * model. Sync code should be removed once it's fixed. */
  BLI_mutex_lock(&work_mutex_);
  if (num_sub_works_finished < num_sub_works) {
    BLI_condition_wait(&work_finished_cond_, &work_mutex_);
  }
  BLI_mutex_unlock(&work_mutex_);
}

void FullFrameExecutionModel::operation_finished(NodeOperation *operation)
{
  /* Report inputs reads so that buffers may be freed/reused. */
  const int num_inputs = operation->getNumberOfInputSockets();
  for (int i = 0; i < num_inputs; i++) {
    active_buffers_.read_finished(operation->get_input_operation(i));
  }

  num_operations_finished_++;
  update_progress_bar();
}

void FullFrameExecutionModel::update_progress_bar()
{
  const bNodeTree *tree = context_.getbNodeTree();
  if (tree) {
    const float progress = num_operations_finished_ / static_cast<float>(operations_.size());
    tree->progress(tree->prh, progress);

    char buf[128];
    BLI_snprintf(buf,
                 sizeof(buf),
                 TIP_("Compositing | Operation %i-%li"),
                 num_operations_finished_ + 1,
                 operations_.size());
    tree->stats_draw(tree->sdh, buf);
  }
}

}  // namespace blender::compositor
