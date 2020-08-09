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
 */

/** \file
 * \ingroup fn
 *
 * The `MFNetworkEvaluator` class is a multi-function that consists of potentially many smaller
 * multi-functions. When called, it traverses the underlying MFNetwork and executes the required
 * function nodes.
 *
 * There are many possible approaches to evaluate a function network. The approach implemented
 * below has the following features:
 * - It does not use recursion. Those could become problematic with long node chains.
 * - It can handle all existing parameter types (including mutable parameters).
 * - Avoids data copies in many cases.
 * - Every node is executed at most once.
 * - Can compute sub-functions on a single element, when the result is the same for all elements.
 *
 * Possible improvements:
 * - Cache and reuse buffers.
 * - Use "deepest depth first" heuristic to decide which order the inputs of a node should be
 *   computed. This reduces the number of required temporary buffers when they are reused.
 */

#include "FN_multi_function_network_evaluation.hh"

#include "BLI_stack.hh"

namespace blender::fn {

struct Value;

/**
 * This keeps track of all the values that flow through the multi-function network. Therefore it
 * maintains a mapping between output sockets and their corresponding values. Every `value`
 * references some memory, that is owned either by the caller or this storage.
 *
 * A value can be owned by different sockets over time to avoid unnecessary copies.
 */
class MFNetworkEvaluationStorage {
 private:
  LinearAllocator<> allocator_;
  IndexMask mask_;
  Array<Value *> value_per_output_id_;
  int64_t min_array_size_;

 public:
  MFNetworkEvaluationStorage(IndexMask mask, int socket_id_amount);
  ~MFNetworkEvaluationStorage();

  /* Add the values that have been provided by the caller of the multi-function network. */
  void add_single_input_from_caller(const MFOutputSocket &socket, GVSpan virtual_span);
  void add_vector_input_from_caller(const MFOutputSocket &socket, GVArraySpan virtual_array_span);
  void add_single_output_from_caller(const MFOutputSocket &socket, GMutableSpan span);
  void add_vector_output_from_caller(const MFOutputSocket &socket, GVectorArray &vector_array);

  /* Get input buffers for function node evaluations. */
  GVSpan get_single_input__full(const MFInputSocket &socket);
  GVSpan get_single_input__single(const MFInputSocket &socket);
  GVArraySpan get_vector_input__full(const MFInputSocket &socket);
  GVArraySpan get_vector_input__single(const MFInputSocket &socket);

  /* Get output buffers for function node evaluations. */
  GMutableSpan get_single_output__full(const MFOutputSocket &socket);
  GMutableSpan get_single_output__single(const MFOutputSocket &socket);
  GVectorArray &get_vector_output__full(const MFOutputSocket &socket);
  GVectorArray &get_vector_output__single(const MFOutputSocket &socket);

  /* Get mutable buffers for function node evaluations. */
  GMutableSpan get_mutable_single__full(const MFInputSocket &input, const MFOutputSocket &output);
  GMutableSpan get_mutable_single__single(const MFInputSocket &input,
                                          const MFOutputSocket &output);
  GVectorArray &get_mutable_vector__full(const MFInputSocket &input, const MFOutputSocket &output);
  GVectorArray &get_mutable_vector__single(const MFInputSocket &input,
                                           const MFOutputSocket &output);

  /* Mark a node as being done with evaluation. This might free temporary buffers that are no
   * longer needed. */
  void finish_node(const MFFunctionNode &node);
  void finish_output_socket(const MFOutputSocket &socket);
  void finish_input_socket(const MFInputSocket &socket);

  IndexMask mask() const;
  bool socket_is_computed(const MFOutputSocket &socket);
  bool is_same_value_for_every_index(const MFOutputSocket &socket);
  bool socket_has_buffer_for_output(const MFOutputSocket &socket);
};

MFNetworkEvaluator::MFNetworkEvaluator(Vector<const MFOutputSocket *> inputs,
                                       Vector<const MFInputSocket *> outputs)
    : inputs_(std::move(inputs)), outputs_(std::move(outputs))
{
  BLI_assert(outputs_.size() > 0);
  MFSignatureBuilder signature = this->get_builder("Function Tree");

  for (const MFOutputSocket *socket : inputs_) {
    BLI_assert(socket->node().is_dummy());

    MFDataType type = socket->data_type();
    switch (type.category()) {
      case MFDataType::Single:
        signature.single_input(socket->name(), type.single_type());
        break;
      case MFDataType::Vector:
        signature.vector_input(socket->name(), type.vector_base_type());
        break;
    }
  }

  for (const MFInputSocket *socket : outputs_) {
    BLI_assert(socket->node().is_dummy());

    MFDataType type = socket->data_type();
    switch (type.category()) {
      case MFDataType::Single:
        signature.single_output(socket->name(), type.single_type());
        break;
      case MFDataType::Vector:
        signature.vector_output(socket->name(), type.vector_base_type());
        break;
    }
  }
}

void MFNetworkEvaluator::call(IndexMask mask, MFParams params, MFContext context) const
{
  if (mask.size() == 0) {
    return;
  }

  const MFNetwork &network = outputs_[0]->node().network();
  Storage storage(mask, network.socket_id_amount());

  Vector<const MFInputSocket *> outputs_to_initialize_in_the_end;

  this->copy_inputs_to_storage(params, storage);
  this->copy_outputs_to_storage(params, storage, outputs_to_initialize_in_the_end);
  this->evaluate_network_to_compute_outputs(context, storage);
  this->initialize_remaining_outputs(params, storage, outputs_to_initialize_in_the_end);
}

BLI_NOINLINE void MFNetworkEvaluator::copy_inputs_to_storage(MFParams params,
                                                             Storage &storage) const
{
  for (int input_index : inputs_.index_range()) {
    int param_index = input_index + 0;
    const MFOutputSocket &socket = *inputs_[input_index];
    switch (socket.data_type().category()) {
      case MFDataType::Single: {
        GVSpan input_list = params.readonly_single_input(param_index);
        storage.add_single_input_from_caller(socket, input_list);
        break;
      }
      case MFDataType::Vector: {
        GVArraySpan input_list_list = params.readonly_vector_input(param_index);
        storage.add_vector_input_from_caller(socket, input_list_list);
        break;
      }
    }
  }
}

BLI_NOINLINE void MFNetworkEvaluator::copy_outputs_to_storage(
    MFParams params,
    Storage &storage,
    Vector<const MFInputSocket *> &outputs_to_initialize_in_the_end) const
{
  for (int output_index : outputs_.index_range()) {
    int param_index = output_index + inputs_.size();
    const MFInputSocket &socket = *outputs_[output_index];
    const MFOutputSocket &origin = *socket.origin();

    if (origin.node().is_dummy()) {
      BLI_assert(inputs_.contains(&origin));
      /* Don't overwrite input buffers. */
      outputs_to_initialize_in_the_end.append(&socket);
      continue;
    }

    if (storage.socket_has_buffer_for_output(origin)) {
      /* When two outputs will be initialized to the same values. */
      outputs_to_initialize_in_the_end.append(&socket);
      continue;
    }

    switch (socket.data_type().category()) {
      case MFDataType::Single: {
        GMutableSpan span = params.uninitialized_single_output(param_index);
        storage.add_single_output_from_caller(origin, span);
        break;
      }
      case MFDataType::Vector: {
        GVectorArray &vector_array = params.vector_output(param_index);
        storage.add_vector_output_from_caller(origin, vector_array);
        break;
      }
    }
  }
}

BLI_NOINLINE void MFNetworkEvaluator::evaluate_network_to_compute_outputs(
    MFContext &global_context, Storage &storage) const
{
  Stack<const MFOutputSocket *, 32> sockets_to_compute;
  for (const MFInputSocket *socket : outputs_) {
    sockets_to_compute.push(socket->origin());
  }

  /* This is the main loop that traverses the MFNetwork. */
  while (!sockets_to_compute.is_empty()) {
    const MFOutputSocket &socket = *sockets_to_compute.peek();
    const MFNode &node = socket.node();

    if (storage.socket_is_computed(socket)) {
      sockets_to_compute.pop();
      continue;
    }

    BLI_assert(node.is_function());
    BLI_assert(!node.has_unlinked_inputs());
    const MFFunctionNode &function_node = node.as_function();

    bool all_origins_are_computed = true;
    for (const MFInputSocket *input_socket : function_node.inputs()) {
      const MFOutputSocket *origin = input_socket->origin();
      if (origin != nullptr) {
        if (!storage.socket_is_computed(*origin)) {
          sockets_to_compute.push(origin);
          all_origins_are_computed = false;
        }
      }
    }

    if (all_origins_are_computed) {
      this->evaluate_function(global_context, function_node, storage);
      sockets_to_compute.pop();
    }
  }
}

BLI_NOINLINE void MFNetworkEvaluator::evaluate_function(MFContext &global_context,
                                                        const MFFunctionNode &function_node,
                                                        Storage &storage) const
{
  const MultiFunction &function = function_node.function();
  // std::cout << "Function: " << function.name() << "\n";

  if (this->can_do_single_value_evaluation(function_node, storage)) {
    /* The function output would be the same for all elements. Therefore, it is enough to call the
     * function only on a single element. This can avoid many duplicate computations. */
    MFParamsBuilder params{function, 1};

    for (int param_index : function.param_indices()) {
      MFParamType param_type = function.param_type(param_index);
      switch (param_type.category()) {
        case MFParamType::SingleInput: {
          const MFInputSocket &socket = function_node.input_for_param(param_index);
          GVSpan values = storage.get_single_input__single(socket);
          params.add_readonly_single_input(values);
          break;
        }
        case MFParamType::VectorInput: {
          const MFInputSocket &socket = function_node.input_for_param(param_index);
          GVArraySpan values = storage.get_vector_input__single(socket);
          params.add_readonly_vector_input(values);
          break;
        }
        case MFParamType::SingleOutput: {
          const MFOutputSocket &socket = function_node.output_for_param(param_index);
          GMutableSpan values = storage.get_single_output__single(socket);
          params.add_uninitialized_single_output(values);
          break;
        }
        case MFParamType::VectorOutput: {
          const MFOutputSocket &socket = function_node.output_for_param(param_index);
          GVectorArray &values = storage.get_vector_output__single(socket);
          params.add_vector_output(values);
          break;
        }
        case MFParamType::SingleMutable: {
          const MFInputSocket &input = function_node.input_for_param(param_index);
          const MFOutputSocket &output = function_node.output_for_param(param_index);
          GMutableSpan values = storage.get_mutable_single__single(input, output);
          params.add_single_mutable(values);
          break;
        }
        case MFParamType::VectorMutable: {
          const MFInputSocket &input = function_node.input_for_param(param_index);
          const MFOutputSocket &output = function_node.output_for_param(param_index);
          GVectorArray &values = storage.get_mutable_vector__single(input, output);
          params.add_vector_mutable(values);
          break;
        }
      }
    }

    function.call(IndexRange(1), params, global_context);
  }
  else {
    MFParamsBuilder params{function, storage.mask().min_array_size()};

    for (int param_index : function.param_indices()) {
      MFParamType param_type = function.param_type(param_index);
      switch (param_type.category()) {
        case MFParamType::SingleInput: {
          const MFInputSocket &socket = function_node.input_for_param(param_index);
          GVSpan values = storage.get_single_input__full(socket);
          params.add_readonly_single_input(values);
          break;
        }
        case MFParamType::VectorInput: {
          const MFInputSocket &socket = function_node.input_for_param(param_index);
          GVArraySpan values = storage.get_vector_input__full(socket);
          params.add_readonly_vector_input(values);
          break;
        }
        case MFParamType::SingleOutput: {
          const MFOutputSocket &socket = function_node.output_for_param(param_index);
          GMutableSpan values = storage.get_single_output__full(socket);
          params.add_uninitialized_single_output(values);
          break;
        }
        case MFParamType::VectorOutput: {
          const MFOutputSocket &socket = function_node.output_for_param(param_index);
          GVectorArray &values = storage.get_vector_output__full(socket);
          params.add_vector_output(values);
          break;
        }
        case MFParamType::SingleMutable: {
          const MFInputSocket &input = function_node.input_for_param(param_index);
          const MFOutputSocket &output = function_node.output_for_param(param_index);
          GMutableSpan values = storage.get_mutable_single__full(input, output);
          params.add_single_mutable(values);
          break;
        }
        case MFParamType::VectorMutable: {
          const MFInputSocket &input = function_node.input_for_param(param_index);
          const MFOutputSocket &output = function_node.output_for_param(param_index);
          GVectorArray &values = storage.get_mutable_vector__full(input, output);
          params.add_vector_mutable(values);
          break;
        }
      }
    }

    function.call(storage.mask(), params, global_context);
  }

  storage.finish_node(function_node);
}

bool MFNetworkEvaluator::can_do_single_value_evaluation(const MFFunctionNode &function_node,
                                                        Storage &storage) const
{
  for (const MFInputSocket *socket : function_node.inputs()) {
    if (!storage.is_same_value_for_every_index(*socket->origin())) {
      return false;
    }
  }
  if (storage.mask().min_array_size() >= 1) {
    for (const MFOutputSocket *socket : function_node.outputs()) {
      if (storage.socket_has_buffer_for_output(*socket)) {
        return false;
      }
    }
  }
  return true;
}

BLI_NOINLINE void MFNetworkEvaluator::initialize_remaining_outputs(
    MFParams params, Storage &storage, Span<const MFInputSocket *> remaining_outputs) const
{
  for (const MFInputSocket *socket : remaining_outputs) {
    int param_index = inputs_.size() + outputs_.first_index_of(socket);

    switch (socket->data_type().category()) {
      case MFDataType::Single: {
        GVSpan values = storage.get_single_input__full(*socket);
        GMutableSpan output_values = params.uninitialized_single_output(param_index);
        values.materialize_to_uninitialized(storage.mask(), output_values.data());
        break;
      }
      case MFDataType::Vector: {
        GVArraySpan values = storage.get_vector_input__full(*socket);
        GVectorArray &output_values = params.vector_output(param_index);
        output_values.extend(storage.mask(), values);
        break;
      }
    }
  }
}

/* -------------------------------------------------------------------- */
/** \name Value Types
 * \{ */

enum class ValueType {
  InputSingle,
  InputVector,
  OutputSingle,
  OutputVector,
  OwnSingle,
  OwnVector,
};

struct Value {
  ValueType type;

  Value(ValueType type) : type(type)
  {
  }
};

struct InputSingleValue : public Value {
  /** This span has been provided by the code that called the multi-function network. */
  GVSpan virtual_span;

  InputSingleValue(GVSpan virtual_span) : Value(ValueType::InputSingle), virtual_span(virtual_span)
  {
  }
};

struct InputVectorValue : public Value {
  /** This span has been provided by the code that called the multi-function network. */
  GVArraySpan virtual_array_span;

  InputVectorValue(GVArraySpan virtual_array_span)
      : Value(ValueType::InputVector), virtual_array_span(virtual_array_span)
  {
  }
};

struct OutputValue : public Value {
  bool is_computed = false;

  OutputValue(ValueType type) : Value(type)
  {
  }
};

struct OutputSingleValue : public OutputValue {
  /** This span has been provided by the code that called the multi-function network. */
  GMutableSpan span;

  OutputSingleValue(GMutableSpan span) : OutputValue(ValueType::OutputSingle), span(span)
  {
  }
};

struct OutputVectorValue : public OutputValue {
  /** This vector array has been provided by the code that called the multi-function network. */
  GVectorArray *vector_array;

  OutputVectorValue(GVectorArray &vector_array)
      : OutputValue(ValueType::OutputVector), vector_array(&vector_array)
  {
  }
};

struct OwnSingleValue : public Value {
  /** This span has been allocated during the evaluation of the multi-function network and contains
   * intermediate data. It has to be freed once the network evaluation is finished. */
  GMutableSpan span;
  int max_remaining_users;
  bool is_single_allocated;

  OwnSingleValue(GMutableSpan span, int max_remaining_users, bool is_single_allocated)
      : Value(ValueType::OwnSingle),
        span(span),
        max_remaining_users(max_remaining_users),
        is_single_allocated(is_single_allocated)
  {
  }
};

struct OwnVectorValue : public Value {
  /** This vector array has been allocated during the evaluation of the multi-function network and
   * contains intermediate data. It has to be freed once the network evaluation is finished. */
  GVectorArray *vector_array;
  int max_remaining_users;

  OwnVectorValue(GVectorArray &vector_array, int max_remaining_users)
      : Value(ValueType::OwnVector),
        vector_array(&vector_array),
        max_remaining_users(max_remaining_users)
  {
  }
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name Storage methods
 * \{ */

MFNetworkEvaluationStorage::MFNetworkEvaluationStorage(IndexMask mask, int socket_id_amount)
    : mask_(mask),
      value_per_output_id_(socket_id_amount, nullptr),
      min_array_size_(mask.min_array_size())
{
}

MFNetworkEvaluationStorage::~MFNetworkEvaluationStorage()
{
  for (Value *any_value : value_per_output_id_) {
    if (any_value == nullptr) {
      continue;
    }
    if (any_value->type == ValueType::OwnSingle) {
      OwnSingleValue *value = static_cast<OwnSingleValue *>(any_value);
      GMutableSpan span = value->span;
      const CPPType &type = span.type();
      if (value->is_single_allocated) {
        type.destruct(span.data());
      }
      else {
        type.destruct_indices(span.data(), mask_);
        MEM_freeN(span.data());
      }
    }
    else if (any_value->type == ValueType::OwnVector) {
      OwnVectorValue *value = static_cast<OwnVectorValue *>(any_value);
      delete value->vector_array;
    }
  }
}

IndexMask MFNetworkEvaluationStorage::mask() const
{
  return mask_;
}

bool MFNetworkEvaluationStorage::socket_is_computed(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  if (any_value == nullptr) {
    return false;
  }
  if (ELEM(any_value->type, ValueType::OutputSingle, ValueType::OutputVector)) {
    return static_cast<OutputValue *>(any_value)->is_computed;
  }
  return true;
}

bool MFNetworkEvaluationStorage::is_same_value_for_every_index(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  switch (any_value->type) {
    case ValueType::OwnSingle:
      return static_cast<OwnSingleValue *>(any_value)->span.size() == 1;
    case ValueType::OwnVector:
      return static_cast<OwnVectorValue *>(any_value)->vector_array->size() == 1;
    case ValueType::InputSingle:
      return static_cast<InputSingleValue *>(any_value)->virtual_span.is_single_element();
    case ValueType::InputVector:
      return static_cast<InputVectorValue *>(any_value)->virtual_array_span.is_single_array();
    case ValueType::OutputSingle:
      return static_cast<OutputSingleValue *>(any_value)->span.size() == 1;
    case ValueType::OutputVector:
      return static_cast<OutputVectorValue *>(any_value)->vector_array->size() == 1;
  }
  BLI_assert(false);
  return false;
}

bool MFNetworkEvaluationStorage::socket_has_buffer_for_output(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  if (any_value == nullptr) {
    return false;
  }

  BLI_assert(ELEM(any_value->type, ValueType::OutputSingle, ValueType::OutputVector));
  return true;
}

void MFNetworkEvaluationStorage::finish_node(const MFFunctionNode &node)
{
  for (const MFInputSocket *socket : node.inputs()) {
    this->finish_input_socket(*socket);
  }
  for (const MFOutputSocket *socket : node.outputs()) {
    this->finish_output_socket(*socket);
  }
}

void MFNetworkEvaluationStorage::finish_output_socket(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  if (any_value == nullptr) {
    return;
  }

  if (ELEM(any_value->type, ValueType::OutputSingle, ValueType::OutputVector)) {
    static_cast<OutputValue *>(any_value)->is_computed = true;
  }
}

void MFNetworkEvaluationStorage::finish_input_socket(const MFInputSocket &socket)
{
  const MFOutputSocket &origin = *socket.origin();

  Value *any_value = value_per_output_id_[origin.id()];
  if (any_value == nullptr) {
    /* Can happen when a value has been forward to the next node. */
    return;
  }

  switch (any_value->type) {
    case ValueType::InputSingle:
    case ValueType::OutputSingle:
    case ValueType::InputVector:
    case ValueType::OutputVector: {
      break;
    }
    case ValueType::OwnSingle: {
      OwnSingleValue *value = static_cast<OwnSingleValue *>(any_value);
      BLI_assert(value->max_remaining_users >= 1);
      value->max_remaining_users--;
      if (value->max_remaining_users == 0) {
        GMutableSpan span = value->span;
        const CPPType &type = span.type();
        if (value->is_single_allocated) {
          type.destruct(span.data());
        }
        else {
          type.destruct_indices(span.data(), mask_);
          MEM_freeN(span.data());
        }
        value_per_output_id_[origin.id()] = nullptr;
      }
      break;
    }
    case ValueType::OwnVector: {
      OwnVectorValue *value = static_cast<OwnVectorValue *>(any_value);
      BLI_assert(value->max_remaining_users >= 1);
      value->max_remaining_users--;
      if (value->max_remaining_users == 0) {
        delete value->vector_array;
        value_per_output_id_[origin.id()] = nullptr;
      }
      break;
    }
  }
}

void MFNetworkEvaluationStorage::add_single_input_from_caller(const MFOutputSocket &socket,
                                                              GVSpan virtual_span)
{
  BLI_assert(value_per_output_id_[socket.id()] == nullptr);
  BLI_assert(virtual_span.size() >= min_array_size_);

  auto *value = allocator_.construct<InputSingleValue>(virtual_span);
  value_per_output_id_[socket.id()] = value;
}

void MFNetworkEvaluationStorage::add_vector_input_from_caller(const MFOutputSocket &socket,
                                                              GVArraySpan virtual_array_span)
{
  BLI_assert(value_per_output_id_[socket.id()] == nullptr);
  BLI_assert(virtual_array_span.size() >= min_array_size_);

  auto *value = allocator_.construct<InputVectorValue>(virtual_array_span);
  value_per_output_id_[socket.id()] = value;
}

void MFNetworkEvaluationStorage::add_single_output_from_caller(const MFOutputSocket &socket,
                                                               GMutableSpan span)
{
  BLI_assert(value_per_output_id_[socket.id()] == nullptr);
  BLI_assert(span.size() >= min_array_size_);

  auto *value = allocator_.construct<OutputSingleValue>(span);
  value_per_output_id_[socket.id()] = value;
}

void MFNetworkEvaluationStorage::add_vector_output_from_caller(const MFOutputSocket &socket,
                                                               GVectorArray &vector_array)
{
  BLI_assert(value_per_output_id_[socket.id()] == nullptr);
  BLI_assert(vector_array.size() >= min_array_size_);

  auto *value = allocator_.construct<OutputVectorValue>(vector_array);
  value_per_output_id_[socket.id()] = value;
}

GMutableSpan MFNetworkEvaluationStorage::get_single_output__full(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  if (any_value == nullptr) {
    const CPPType &type = socket.data_type().single_type();
    void *buffer = MEM_mallocN_aligned(min_array_size_ * type.size(), type.alignment(), AT);
    GMutableSpan span(type, buffer, min_array_size_);

    auto *value = allocator_.construct<OwnSingleValue>(span, socket.targets().size(), false);
    value_per_output_id_[socket.id()] = value;

    return span;
  }

  BLI_assert(any_value->type == ValueType::OutputSingle);
  return static_cast<OutputSingleValue *>(any_value)->span;
}

GMutableSpan MFNetworkEvaluationStorage::get_single_output__single(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  if (any_value == nullptr) {
    const CPPType &type = socket.data_type().single_type();
    void *buffer = allocator_.allocate(type.size(), type.alignment());
    GMutableSpan span(type, buffer, 1);

    auto *value = allocator_.construct<OwnSingleValue>(span, socket.targets().size(), true);
    value_per_output_id_[socket.id()] = value;

    return value->span;
  }

  BLI_assert(any_value->type == ValueType::OutputSingle);
  GMutableSpan span = static_cast<OutputSingleValue *>(any_value)->span;
  BLI_assert(span.size() == 1);
  return span;
}

GVectorArray &MFNetworkEvaluationStorage::get_vector_output__full(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  if (any_value == nullptr) {
    const CPPType &type = socket.data_type().vector_base_type();
    GVectorArray *vector_array = new GVectorArray(type, min_array_size_);

    auto *value = allocator_.construct<OwnVectorValue>(*vector_array, socket.targets().size());
    value_per_output_id_[socket.id()] = value;

    return *value->vector_array;
  }

  BLI_assert(any_value->type == ValueType::OutputVector);
  return *static_cast<OutputVectorValue *>(any_value)->vector_array;
}

GVectorArray &MFNetworkEvaluationStorage::get_vector_output__single(const MFOutputSocket &socket)
{
  Value *any_value = value_per_output_id_[socket.id()];
  if (any_value == nullptr) {
    const CPPType &type = socket.data_type().vector_base_type();
    GVectorArray *vector_array = new GVectorArray(type, 1);

    auto *value = allocator_.construct<OwnVectorValue>(*vector_array, socket.targets().size());
    value_per_output_id_[socket.id()] = value;

    return *value->vector_array;
  }

  BLI_assert(any_value->type == ValueType::OutputVector);
  GVectorArray &vector_array = *static_cast<OutputVectorValue *>(any_value)->vector_array;
  BLI_assert(vector_array.size() == 1);
  return vector_array;
}

GMutableSpan MFNetworkEvaluationStorage::get_mutable_single__full(const MFInputSocket &input,
                                                                  const MFOutputSocket &output)
{
  const MFOutputSocket &from = *input.origin();
  const MFOutputSocket &to = output;
  const CPPType &type = from.data_type().single_type();

  Value *from_any_value = value_per_output_id_[from.id()];
  Value *to_any_value = value_per_output_id_[to.id()];
  BLI_assert(from_any_value != nullptr);
  BLI_assert(type == to.data_type().single_type());

  if (to_any_value != nullptr) {
    BLI_assert(to_any_value->type == ValueType::OutputSingle);
    GMutableSpan span = static_cast<OutputSingleValue *>(to_any_value)->span;
    GVSpan virtual_span = this->get_single_input__full(input);
    virtual_span.materialize_to_uninitialized(mask_, span.data());
    return span;
  }

  if (from_any_value->type == ValueType::OwnSingle) {
    OwnSingleValue *value = static_cast<OwnSingleValue *>(from_any_value);
    if (value->max_remaining_users == 1 && !value->is_single_allocated) {
      value_per_output_id_[to.id()] = value;
      value_per_output_id_[from.id()] = nullptr;
      value->max_remaining_users = to.targets().size();
      return value->span;
    }
  }

  GVSpan virtual_span = this->get_single_input__full(input);
  void *new_buffer = MEM_mallocN_aligned(min_array_size_ * type.size(), type.alignment(), AT);
  GMutableSpan new_array_ref(type, new_buffer, min_array_size_);
  virtual_span.materialize_to_uninitialized(mask_, new_array_ref.data());

  OwnSingleValue *new_value = allocator_.construct<OwnSingleValue>(
      new_array_ref, to.targets().size(), false);
  value_per_output_id_[to.id()] = new_value;
  return new_array_ref;
}

GMutableSpan MFNetworkEvaluationStorage::get_mutable_single__single(const MFInputSocket &input,
                                                                    const MFOutputSocket &output)
{
  const MFOutputSocket &from = *input.origin();
  const MFOutputSocket &to = output;
  const CPPType &type = from.data_type().single_type();

  Value *from_any_value = value_per_output_id_[from.id()];
  Value *to_any_value = value_per_output_id_[to.id()];
  BLI_assert(from_any_value != nullptr);
  BLI_assert(type == to.data_type().single_type());

  if (to_any_value != nullptr) {
    BLI_assert(to_any_value->type == ValueType::OutputSingle);
    GMutableSpan span = static_cast<OutputSingleValue *>(to_any_value)->span;
    BLI_assert(span.size() == 1);
    GVSpan virtual_span = this->get_single_input__single(input);
    type.copy_to_uninitialized(virtual_span.as_single_element(), span[0]);
    return span;
  }

  if (from_any_value->type == ValueType::OwnSingle) {
    OwnSingleValue *value = static_cast<OwnSingleValue *>(from_any_value);
    if (value->max_remaining_users == 1) {
      value_per_output_id_[to.id()] = value;
      value_per_output_id_[from.id()] = nullptr;
      value->max_remaining_users = to.targets().size();
      BLI_assert(value->span.size() == 1);
      return value->span;
    }
  }

  GVSpan virtual_span = this->get_single_input__single(input);

  void *new_buffer = allocator_.allocate(type.size(), type.alignment());
  type.copy_to_uninitialized(virtual_span.as_single_element(), new_buffer);
  GMutableSpan new_array_ref(type, new_buffer, 1);

  OwnSingleValue *new_value = allocator_.construct<OwnSingleValue>(
      new_array_ref, to.targets().size(), true);
  value_per_output_id_[to.id()] = new_value;
  return new_array_ref;
}

GVectorArray &MFNetworkEvaluationStorage::get_mutable_vector__full(const MFInputSocket &input,
                                                                   const MFOutputSocket &output)
{
  const MFOutputSocket &from = *input.origin();
  const MFOutputSocket &to = output;
  const CPPType &base_type = from.data_type().vector_base_type();

  Value *from_any_value = value_per_output_id_[from.id()];
  Value *to_any_value = value_per_output_id_[to.id()];
  BLI_assert(from_any_value != nullptr);
  BLI_assert(base_type == to.data_type().vector_base_type());

  if (to_any_value != nullptr) {
    BLI_assert(to_any_value->type == ValueType::OutputVector);
    GVectorArray &vector_array = *static_cast<OutputVectorValue *>(to_any_value)->vector_array;
    GVArraySpan virtual_array_span = this->get_vector_input__full(input);
    vector_array.extend(mask_, virtual_array_span);
    return vector_array;
  }

  if (from_any_value->type == ValueType::OwnVector) {
    OwnVectorValue *value = static_cast<OwnVectorValue *>(from_any_value);
    if (value->max_remaining_users == 1) {
      value_per_output_id_[to.id()] = value;
      value_per_output_id_[from.id()] = nullptr;
      value->max_remaining_users = to.targets().size();
      return *value->vector_array;
    }
  }

  GVArraySpan virtual_array_span = this->get_vector_input__full(input);

  GVectorArray *new_vector_array = new GVectorArray(base_type, min_array_size_);
  new_vector_array->extend(mask_, virtual_array_span);

  OwnVectorValue *new_value = allocator_.construct<OwnVectorValue>(*new_vector_array,
                                                                   to.targets().size());
  value_per_output_id_[to.id()] = new_value;

  return *new_vector_array;
}

GVectorArray &MFNetworkEvaluationStorage::get_mutable_vector__single(const MFInputSocket &input,
                                                                     const MFOutputSocket &output)
{
  const MFOutputSocket &from = *input.origin();
  const MFOutputSocket &to = output;
  const CPPType &base_type = from.data_type().vector_base_type();

  Value *from_any_value = value_per_output_id_[from.id()];
  Value *to_any_value = value_per_output_id_[to.id()];
  BLI_assert(from_any_value != nullptr);
  BLI_assert(base_type == to.data_type().vector_base_type());

  if (to_any_value != nullptr) {
    BLI_assert(to_any_value->type == ValueType::OutputVector);
    GVectorArray &vector_array = *static_cast<OutputVectorValue *>(to_any_value)->vector_array;
    BLI_assert(vector_array.size() == 1);
    GVArraySpan virtual_array_span = this->get_vector_input__single(input);
    vector_array.extend(0, virtual_array_span[0]);
    return vector_array;
  }

  if (from_any_value->type == ValueType::OwnVector) {
    OwnVectorValue *value = static_cast<OwnVectorValue *>(from_any_value);
    if (value->max_remaining_users == 1) {
      value_per_output_id_[to.id()] = value;
      value_per_output_id_[from.id()] = nullptr;
      value->max_remaining_users = to.targets().size();
      return *value->vector_array;
    }
  }

  GVArraySpan virtual_array_span = this->get_vector_input__single(input);

  GVectorArray *new_vector_array = new GVectorArray(base_type, 1);
  new_vector_array->extend(0, virtual_array_span[0]);

  OwnVectorValue *new_value = allocator_.construct<OwnVectorValue>(*new_vector_array,
                                                                   to.targets().size());
  value_per_output_id_[to.id()] = new_value;
  return *new_vector_array;
}

GVSpan MFNetworkEvaluationStorage::get_single_input__full(const MFInputSocket &socket)
{
  const MFOutputSocket &origin = *socket.origin();
  Value *any_value = value_per_output_id_[origin.id()];
  BLI_assert(any_value != nullptr);

  if (any_value->type == ValueType::OwnSingle) {
    OwnSingleValue *value = static_cast<OwnSingleValue *>(any_value);
    if (value->is_single_allocated) {
      return GVSpan::FromSingle(value->span.type(), value->span.data(), min_array_size_);
    }

    return value->span;
  }
  if (any_value->type == ValueType::InputSingle) {
    InputSingleValue *value = static_cast<InputSingleValue *>(any_value);
    return value->virtual_span;
  }
  if (any_value->type == ValueType::OutputSingle) {
    OutputSingleValue *value = static_cast<OutputSingleValue *>(any_value);
    BLI_assert(value->is_computed);
    return value->span;
  }

  BLI_assert(false);
  return GVSpan(CPPType::get<float>());
}

GVSpan MFNetworkEvaluationStorage::get_single_input__single(const MFInputSocket &socket)
{
  const MFOutputSocket &origin = *socket.origin();
  Value *any_value = value_per_output_id_[origin.id()];
  BLI_assert(any_value != nullptr);

  if (any_value->type == ValueType::OwnSingle) {
    OwnSingleValue *value = static_cast<OwnSingleValue *>(any_value);
    BLI_assert(value->span.size() == 1);
    return value->span;
  }
  if (any_value->type == ValueType::InputSingle) {
    InputSingleValue *value = static_cast<InputSingleValue *>(any_value);
    BLI_assert(value->virtual_span.is_single_element());
    return value->virtual_span;
  }
  if (any_value->type == ValueType::OutputSingle) {
    OutputSingleValue *value = static_cast<OutputSingleValue *>(any_value);
    BLI_assert(value->is_computed);
    BLI_assert(value->span.size() == 1);
    return value->span;
  }

  BLI_assert(false);
  return GVSpan(CPPType::get<float>());
}

GVArraySpan MFNetworkEvaluationStorage::get_vector_input__full(const MFInputSocket &socket)
{
  const MFOutputSocket &origin = *socket.origin();
  Value *any_value = value_per_output_id_[origin.id()];
  BLI_assert(any_value != nullptr);

  if (any_value->type == ValueType::OwnVector) {
    OwnVectorValue *value = static_cast<OwnVectorValue *>(any_value);
    if (value->vector_array->size() == 1) {
      GSpan span = (*value->vector_array)[0];
      return GVArraySpan(span, min_array_size_);
    }

    return *value->vector_array;
  }
  if (any_value->type == ValueType::InputVector) {
    InputVectorValue *value = static_cast<InputVectorValue *>(any_value);
    return value->virtual_array_span;
  }
  if (any_value->type == ValueType::OutputVector) {
    OutputVectorValue *value = static_cast<OutputVectorValue *>(any_value);
    return *value->vector_array;
  }

  BLI_assert(false);
  return GVArraySpan(CPPType::get<float>());
}

GVArraySpan MFNetworkEvaluationStorage::get_vector_input__single(const MFInputSocket &socket)
{
  const MFOutputSocket &origin = *socket.origin();
  Value *any_value = value_per_output_id_[origin.id()];
  BLI_assert(any_value != nullptr);

  if (any_value->type == ValueType::OwnVector) {
    OwnVectorValue *value = static_cast<OwnVectorValue *>(any_value);
    BLI_assert(value->vector_array->size() == 1);
    return *value->vector_array;
  }
  if (any_value->type == ValueType::InputVector) {
    InputVectorValue *value = static_cast<InputVectorValue *>(any_value);
    BLI_assert(value->virtual_array_span.is_single_array());
    return value->virtual_array_span;
  }
  if (any_value->type == ValueType::OutputVector) {
    OutputVectorValue *value = static_cast<OutputVectorValue *>(any_value);
    BLI_assert(value->vector_array->size() == 1);
    return *value->vector_array;
  }

  BLI_assert(false);
  return GVArraySpan(CPPType::get<float>());
}

/** \} */

}  // namespace blender::fn
