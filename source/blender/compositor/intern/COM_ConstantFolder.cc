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

#include "BLI_rect.h"

#include "COM_ConstantFolder.h"
#include "COM_ConstantOperation.h"
#include "COM_SetColorOperation.h"
#include "COM_SetValueOperation.h"
#include "COM_SetVectorOperation.h"
#include "COM_WorkScheduler.h"

namespace blender::compositor {

using Link = NodeOperationBuilder::Link;

/**
 * \param operations_builder: Contains all operations to fold.
 * \param exec_system: Execution system.
 */
ConstantFolder::ConstantFolder(NodeOperationBuilder &operations_builder)
    : operations_builder_(operations_builder)
{
  BLI_rcti_init(&max_area_, INT_MIN, INT_MAX, INT_MIN, INT_MAX);
  BLI_rcti_init(&first_elem_area_, 0, 1, 0, 1);
}

static bool is_constant_foldable(NodeOperation *operation)
{
  if (operation->get_flags().can_be_constant && !operation->get_flags().is_constant_operation) {
    for (int i = 0; i < operation->getNumberOfInputSockets(); i++) {
      if (!operation->get_input_operation(i)->get_flags().is_constant_operation) {
        return false;
      }
    }
    return true;
  }
  return false;
}

static Vector<NodeOperation *> find_constant_foldable_operations(Span<NodeOperation *> operations)
{
  Vector<NodeOperation *> foldable_ops;
  for (NodeOperation *op : operations) {
    if (is_constant_foldable(op)) {
      foldable_ops.append(op);
    }
  }
  return foldable_ops;
}

static ConstantOperation *create_constant_operation(DataType data_type, const float *constant_elem)
{
  switch (data_type) {
    case DataType::Color: {
      SetColorOperation *color_op = new SetColorOperation();
      color_op->setChannels(constant_elem);
      return color_op;
    }
    case DataType::Vector: {
      SetVectorOperation *vector_op = new SetVectorOperation();
      vector_op->setVector(constant_elem);
      return vector_op;
    }
    case DataType::Value: {
      SetValueOperation *value_op = new SetValueOperation();
      value_op->setValue(*constant_elem);
      return value_op;
    }
    default: {
      BLI_assert_msg(0, "Non implemented data type");
      return nullptr;
    }
  }
}

ConstantOperation *ConstantFolder::fold_operation(NodeOperation *operation)
{
  const DataType data_type = operation->getOutputSocket()->getDataType();
  MemoryBuffer fold_buf(data_type, first_elem_area_);
  Vector<MemoryBuffer *> input_bufs = get_constant_input_buffers(operation);
  operation->render(&fold_buf, {first_elem_area_}, input_bufs);

  MemoryBuffer *constant_buf = create_constant_buffer(data_type);
  constant_buf->copy_from(&fold_buf, first_elem_area_);
  ConstantOperation *constant_op = create_constant_operation(data_type, constant_buf->getBuffer());
  operations_builder_.replace_operation_with_constant(operation, constant_op);
  constant_buffers_.add_new(constant_op, constant_buf);
  return constant_op;
}

MemoryBuffer *ConstantFolder::create_constant_buffer(const DataType data_type)
{
  /* Create a single elem buffer with maximum area possible so readers can read any coordinate
   * returning always same element. */
  return new MemoryBuffer(data_type, max_area_, true);
}

Vector<MemoryBuffer *> ConstantFolder::get_constant_input_buffers(NodeOperation *operation)
{
  const int num_inputs = operation->getNumberOfInputSockets();
  Vector<MemoryBuffer *> inputs_bufs(num_inputs);
  for (int i = 0; i < num_inputs; i++) {
    BLI_assert(operation->get_input_operation(i)->get_flags().is_constant_operation);
    ConstantOperation *constant_op = static_cast<ConstantOperation *>(
        operation->get_input_operation(i));
    MemoryBuffer *constant_buf = constant_buffers_.lookup_or_add_cb(constant_op, [=] {
      MemoryBuffer *buf = create_constant_buffer(constant_op->getOutputSocket()->getDataType());
      constant_op->render(buf, {first_elem_area_}, {});
      return buf;
    });
    inputs_bufs[i] = constant_buf;
  }
  return inputs_bufs;
}

/** Returns constant operations resulted from folded operations. */
Vector<ConstantOperation *> ConstantFolder::try_fold_operations(Span<NodeOperation *> operations)
{
  Vector<NodeOperation *> foldable_ops = find_constant_foldable_operations(operations);
  if (foldable_ops.size() == 0) {
    return Vector<ConstantOperation *>();
  }

  Vector<ConstantOperation *> new_folds;
  for (NodeOperation *op : foldable_ops) {
    ConstantOperation *constant_op = fold_operation(op);
    new_folds.append(constant_op);
  }
  return new_folds;
}

/**
 * Evaluate operations with constant elements into primitive constant operations.
 */
int ConstantFolder::fold_operations()
{
  WorkScheduler::start(operations_builder_.context());
  Vector<ConstantOperation *> last_folds = try_fold_operations(
      operations_builder_.get_operations());
  int folds_count = last_folds.size();
  while (last_folds.size() > 0) {
    Vector<NodeOperation *> ops_to_fold;
    for (ConstantOperation *fold : last_folds) {
      get_operation_output_operations(fold, ops_to_fold);
    }
    last_folds = try_fold_operations(ops_to_fold);
    folds_count += last_folds.size();
  }
  WorkScheduler::stop();

  delete_constant_buffers();

  return folds_count;
}

void ConstantFolder::delete_constant_buffers()
{
  for (MemoryBuffer *buf : constant_buffers_.values()) {
    delete buf;
  }
  constant_buffers_.clear();
}

void ConstantFolder::get_operation_output_operations(NodeOperation *operation,
                                                     Vector<NodeOperation *> &r_outputs)
{
  const Vector<Link> &links = operations_builder_.get_links();
  for (const Link &link : links) {
    if (&link.from()->getOperation() == operation) {
      r_outputs.append(&link.to()->getOperation());
    }
  }
}

}  // namespace blender::compositor
