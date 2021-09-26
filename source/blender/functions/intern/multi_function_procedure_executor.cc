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

#include "FN_multi_function_procedure_executor.hh"

#include "BLI_stack.hh"

namespace blender::fn {

MFProcedureExecutor::MFProcedureExecutor(std::string name, const MFProcedure &procedure)
    : procedure_(procedure)
{
  MFSignatureBuilder signature(std::move(name));

  for (const ConstMFParameter &param : procedure.params()) {
    signature.add(param.variable->name(), MFParamType(param.type, param.variable->data_type()));
  }

  signature_ = signature.build();
  this->set_signature(&signature_);
}

using IndicesSplitVectors = std::array<Vector<int64_t>, 2>;

namespace {
enum class ValueType {
  GVArray = 0,
  Span = 1,
  GVVectorArray = 2,
  GVectorArray = 3,
  OneSingle = 4,
  OneVector = 5,
};
constexpr int tot_variable_value_types = 6;
}  // namespace

/**
 * During evaluation, a variable may be stored in various different forms, depending on what
 * instructions do with the variables.
 */
struct VariableValue {
  ValueType type;

  VariableValue(ValueType type) : type(type)
  {
  }
};

/* This variable is the unmodified virtual array from the caller. */
struct VariableValue_GVArray : public VariableValue {
  static inline constexpr ValueType static_type = ValueType::GVArray;
  const GVArray &data;

  VariableValue_GVArray(const GVArray &data) : VariableValue(static_type), data(data)
  {
  }
};

/* This variable has a different value for every index. Some values may be uninitialized. The span
 * may be owned by the caller. */
struct VariableValue_Span : public VariableValue {
  static inline constexpr ValueType static_type = ValueType::Span;
  void *data;
  bool owned;

  VariableValue_Span(void *data, bool owned) : VariableValue(static_type), data(data), owned(owned)
  {
  }
};

/* This variable is the unmodified virtual vector array from the caller. */
struct VariableValue_GVVectorArray : public VariableValue {
  static inline constexpr ValueType static_type = ValueType::GVVectorArray;
  const GVVectorArray &data;

  VariableValue_GVVectorArray(const GVVectorArray &data) : VariableValue(static_type), data(data)
  {
  }
};

/* This variable has a different vector for every index. */
struct VariableValue_GVectorArray : public VariableValue {
  static inline constexpr ValueType static_type = ValueType::GVectorArray;
  GVectorArray &data;
  bool owned;

  VariableValue_GVectorArray(GVectorArray &data, bool owned)
      : VariableValue(static_type), data(data), owned(owned)
  {
  }
};

/* This variable has the same value for every index. */
struct VariableValue_OneSingle : public VariableValue {
  static inline constexpr ValueType static_type = ValueType::OneSingle;
  void *data;
  bool is_initialized = false;

  VariableValue_OneSingle(void *data) : VariableValue(static_type), data(data)
  {
  }
};

/* This variable has the same vector for every index. */
struct VariableValue_OneVector : public VariableValue {
  static inline constexpr ValueType static_type = ValueType::OneVector;
  GVectorArray &data;

  VariableValue_OneVector(GVectorArray &data) : VariableValue(static_type), data(data)
  {
  }
};

static_assert(std::is_trivially_destructible_v<VariableValue_GVArray>);
static_assert(std::is_trivially_destructible_v<VariableValue_Span>);
static_assert(std::is_trivially_destructible_v<VariableValue_GVVectorArray>);
static_assert(std::is_trivially_destructible_v<VariableValue_GVectorArray>);
static_assert(std::is_trivially_destructible_v<VariableValue_OneSingle>);
static_assert(std::is_trivially_destructible_v<VariableValue_OneVector>);

class VariableState;

/**
 * The #ValueAllocator is responsible for providing memory for variables and their values. It also
 * manages the reuse of buffers to improve performance.
 */
class ValueAllocator : NonCopyable, NonMovable {
 private:
  /* Allocate with 64 byte alignment for better reusability of buffers and improved cache
   * performance. */
  static constexpr inline int min_alignment = 64;

  /* Use stacks so that the most recently used buffers are reused first. This improves cache
   * efficiency. */
  std::array<Stack<VariableValue *>, tot_variable_value_types> values_free_lists_;
  /* The integer key is the size of one element (e.g. 4 for an integer buffer). All buffers are
   * aligned to #min_alignment bytes. */
  Map<int, Stack<void *>> span_buffers_free_list_;

 public:
  ValueAllocator() = default;

  ~ValueAllocator()
  {
    for (Stack<VariableValue *> &stack : values_free_lists_) {
      while (!stack.is_empty()) {
        MEM_freeN(stack.pop());
      }
    }
    for (Stack<void *> &stack : span_buffers_free_list_.values()) {
      while (!stack.is_empty()) {
        MEM_freeN(stack.pop());
      }
    }
  }

  template<typename... Args> VariableState *obtain_variable_state(Args &&...args);

  void release_variable_state(VariableState *state);

  VariableValue_GVArray *obtain_GVArray(const GVArray &varray)
  {
    return this->obtain<VariableValue_GVArray>(varray);
  }

  VariableValue_GVVectorArray *obtain_GVVectorArray(const GVVectorArray &varray)
  {
    return this->obtain<VariableValue_GVVectorArray>(varray);
  }

  VariableValue_Span *obtain_Span_not_owned(void *buffer)
  {
    return this->obtain<VariableValue_Span>(buffer, false);
  }

  VariableValue_Span *obtain_Span(const CPPType &type, int size)
  {
    void *buffer = nullptr;

    const int element_size = type.size();
    const int alignment = type.alignment();

    if (alignment > min_alignment) {
      /* In this rare case we fallback to not reusing existing buffers. */
      buffer = MEM_mallocN_aligned(element_size * size, alignment, __func__);
    }
    else {
      Stack<void *> *stack = span_buffers_free_list_.lookup_ptr(element_size);
      if (stack == nullptr || stack->is_empty()) {
        buffer = MEM_mallocN_aligned(element_size * size, min_alignment, __func__);
      }
      else {
        /* Reuse existing buffer. */
        buffer = stack->pop();
      }
    }

    return this->obtain<VariableValue_Span>(buffer, true);
  }

  VariableValue_GVectorArray *obtain_GVectorArray_not_owned(GVectorArray &data)
  {
    return this->obtain<VariableValue_GVectorArray>(data, false);
  }

  VariableValue_GVectorArray *obtain_GVectorArray(const CPPType &type, int size)
  {
    GVectorArray *vector_array = new GVectorArray(type, size);
    return this->obtain<VariableValue_GVectorArray>(*vector_array, true);
  }

  VariableValue_OneSingle *obtain_OneSingle(const CPPType &type)
  {
    void *buffer = MEM_mallocN_aligned(type.size(), type.alignment(), __func__);
    return this->obtain<VariableValue_OneSingle>(buffer);
  }

  VariableValue_OneVector *obtain_OneVector(const CPPType &type)
  {
    GVectorArray *vector_array = new GVectorArray(type, 1);
    return this->obtain<VariableValue_OneVector>(*vector_array);
  }

  void release_value(VariableValue *value, const MFDataType &data_type)
  {
    switch (value->type) {
      case ValueType::GVArray: {
        break;
      }
      case ValueType::Span: {
        auto *value_typed = static_cast<VariableValue_Span *>(value);
        if (value_typed->owned) {
          const CPPType &type = data_type.single_type();
          /* Assumes all values in the buffer are uninitialized already. */
          Stack<void *> &buffers = span_buffers_free_list_.lookup_or_add_default(type.size());
          buffers.push(value_typed->data);
        }
        break;
      }
      case ValueType::GVVectorArray: {
        break;
      }
      case ValueType::GVectorArray: {
        auto *value_typed = static_cast<VariableValue_GVectorArray *>(value);
        if (value_typed->owned) {
          delete &value_typed->data;
        }
        break;
      }
      case ValueType::OneSingle: {
        auto *value_typed = static_cast<VariableValue_OneSingle *>(value);
        if (value_typed->is_initialized) {
          const CPPType &type = data_type.single_type();
          type.destruct(value_typed->data);
        }
        MEM_freeN(value_typed->data);
        break;
      }
      case ValueType::OneVector: {
        auto *value_typed = static_cast<VariableValue_OneVector *>(value);
        delete &value_typed->data;
        break;
      }
    }

    Stack<VariableValue *> &stack = values_free_lists_[(int)value->type];
    stack.push(value);
  }

 private:
  template<typename T, typename... Args> T *obtain(Args &&...args)
  {
    static_assert(std::is_base_of_v<VariableValue, T>);
    Stack<VariableValue *> &stack = values_free_lists_[(int)T::static_type];
    if (stack.is_empty()) {
      void *buffer = MEM_mallocN(sizeof(T), __func__);
      return new (buffer) T(std::forward<Args>(args)...);
    }
    return new (stack.pop()) T(std::forward<Args>(args)...);
  }
};

/**
 * This class keeps track of a single variable during evaluation.
 */
class VariableState : NonCopyable, NonMovable {
 private:
  /** The current value of the variable. The storage format may change over time. */
  VariableValue *value_;
  /** Number of indices that are currently initialized in this variable. */
  int tot_initialized_;
  /* This a non-owning pointer to either span buffer or #GVectorArray or null. */
  void *caller_provided_storage_ = nullptr;

 public:
  VariableState(VariableValue &value, int tot_initialized, void *caller_provided_storage = nullptr)
      : value_(&value),
        tot_initialized_(tot_initialized),
        caller_provided_storage_(caller_provided_storage)
  {
  }

  void destruct_self(ValueAllocator &value_allocator, const MFDataType &data_type)
  {
    value_allocator.release_value(value_, data_type);
    value_allocator.release_variable_state(this);
  }

  /* True if this contains only one value for all indices, i.e. the value for all indices is
   * the same. */
  bool is_one() const
  {
    switch (value_->type) {
      case ValueType::GVArray:
        return this->value_as<VariableValue_GVArray>()->data.is_single();
      case ValueType::Span:
        return tot_initialized_ == 0;
      case ValueType::GVVectorArray:
        return this->value_as<VariableValue_GVVectorArray>()->data.is_single_vector();
      case ValueType::GVectorArray:
        return tot_initialized_ == 0;
      case ValueType::OneSingle:
        return true;
      case ValueType::OneVector:
        return true;
    }
    BLI_assert_unreachable();
    return false;
  }

  bool is_fully_initialized(const IndexMask full_mask)
  {
    return tot_initialized_ == full_mask.size();
  }

  bool is_fully_uninitialized(const IndexMask full_mask)
  {
    UNUSED_VARS(full_mask);
    return tot_initialized_ == 0;
  }

  void add_as_input(MFParamsBuilder &params, IndexMask mask, const MFDataType &data_type) const
  {
    /* Sanity check to make sure that enough values are initialized. */
    BLI_assert(mask.size() <= tot_initialized_);

    switch (value_->type) {
      case ValueType::GVArray: {
        params.add_readonly_single_input(this->value_as<VariableValue_GVArray>()->data);
        break;
      }
      case ValueType::Span: {
        const void *data = this->value_as<VariableValue_Span>()->data;
        const GSpan span{data_type.single_type(), data, mask.min_array_size()};
        params.add_readonly_single_input(span);
        break;
      }
      case ValueType::GVVectorArray: {
        params.add_readonly_vector_input(this->value_as<VariableValue_GVVectorArray>()->data);
        break;
      }
      case ValueType::GVectorArray: {
        params.add_readonly_vector_input(this->value_as<VariableValue_GVectorArray>()->data);
        break;
      }
      case ValueType::OneSingle: {
        const auto *value_typed = this->value_as<VariableValue_OneSingle>();
        BLI_assert(value_typed->is_initialized);
        const GPointer gpointer{data_type.single_type(), value_typed->data};
        params.add_readonly_single_input(gpointer);
        break;
      }
      case ValueType::OneVector: {
        params.add_readonly_vector_input(this->value_as<VariableValue_OneVector>()->data[0]);
        break;
      }
    }
  }

  void ensure_is_mutable(IndexMask full_mask,
                         const MFDataType &data_type,
                         ValueAllocator &value_allocator)
  {
    if (ELEM(value_->type, ValueType::Span, ValueType::GVectorArray)) {
      return;
    }

    const int array_size = full_mask.min_array_size();

    switch (data_type.category()) {
      case MFDataType::Single: {
        const CPPType &type = data_type.single_type();
        VariableValue_Span *new_value = nullptr;
        if (caller_provided_storage_ == nullptr) {
          new_value = value_allocator.obtain_Span(type, array_size);
        }
        else {
          /* Reuse the storage provided caller when possible. */
          new_value = value_allocator.obtain_Span_not_owned(caller_provided_storage_);
        }
        if (value_->type == ValueType::GVArray) {
          /* Fill new buffer with data from virtual array. */
          this->value_as<VariableValue_GVArray>()->data.materialize_to_uninitialized(
              full_mask, new_value->data);
        }
        else if (value_->type == ValueType::OneSingle) {
          auto *old_value_typed_ = this->value_as<VariableValue_OneSingle>();
          if (old_value_typed_->is_initialized) {
            /* Fill the buffer with a single value. */
            type.fill_construct_indices(old_value_typed_->data, new_value->data, full_mask);
          }
        }
        else {
          BLI_assert_unreachable();
        }
        value_allocator.release_value(value_, data_type);
        value_ = new_value;
        break;
      }
      case MFDataType::Vector: {
        const CPPType &type = data_type.vector_base_type();
        VariableValue_GVectorArray *new_value = nullptr;
        if (caller_provided_storage_ == nullptr) {
          new_value = value_allocator.obtain_GVectorArray(type, array_size);
        }
        else {
          new_value = value_allocator.obtain_GVectorArray_not_owned(
              *(GVectorArray *)caller_provided_storage_);
        }
        if (value_->type == ValueType::GVVectorArray) {
          /* Fill new vector array with data from virtual vector array. */
          new_value->data.extend(full_mask, this->value_as<VariableValue_GVVectorArray>()->data);
        }
        else if (value_->type == ValueType::OneVector) {
          /* Fill all indices with the same value. */
          const GSpan vector = this->value_as<VariableValue_OneVector>()->data[0];
          new_value->data.extend(full_mask, GVVectorArray_For_SingleGSpan{vector, array_size});
        }
        else {
          BLI_assert_unreachable();
        }
        value_allocator.release_value(value_, data_type);
        value_ = new_value;
        break;
      }
    }
  }

  void add_as_mutable(MFParamsBuilder &params,
                      IndexMask mask,
                      IndexMask full_mask,
                      const MFDataType &data_type,
                      ValueAllocator &value_allocator)
  {
    /* Sanity check to make sure that enough values are initialized. */
    BLI_assert(mask.size() <= tot_initialized_);

    this->ensure_is_mutable(full_mask, data_type, value_allocator);

    switch (value_->type) {
      case ValueType::Span: {
        void *data = this->value_as<VariableValue_Span>()->data;
        const GMutableSpan span{data_type.single_type(), data, mask.min_array_size()};
        params.add_single_mutable(span);
        break;
      }
      case ValueType::GVectorArray: {
        params.add_vector_mutable(this->value_as<VariableValue_GVectorArray>()->data);
        break;
      }
      case ValueType::GVArray:
      case ValueType::GVVectorArray:
      case ValueType::OneSingle:
      case ValueType::OneVector: {
        BLI_assert_unreachable();
        break;
      }
    }
  }

  void add_as_output(MFParamsBuilder &params,
                     IndexMask mask,
                     IndexMask full_mask,
                     const MFDataType &data_type,
                     ValueAllocator &value_allocator)
  {
    /* Sanity check to make sure that enough values are not initialized. */
    BLI_assert(mask.size() <= full_mask.size() - tot_initialized_);
    this->ensure_is_mutable(full_mask, data_type, value_allocator);

    switch (value_->type) {
      case ValueType::Span: {
        void *data = this->value_as<VariableValue_Span>()->data;
        const GMutableSpan span{data_type.single_type(), data, mask.min_array_size()};
        params.add_uninitialized_single_output(span);
        break;
      }
      case ValueType::GVectorArray: {
        params.add_vector_output(this->value_as<VariableValue_GVectorArray>()->data);
        break;
      }
      case ValueType::GVArray:
      case ValueType::GVVectorArray:
      case ValueType::OneSingle:
      case ValueType::OneVector: {
        BLI_assert_unreachable();
        break;
      }
    }

    tot_initialized_ += mask.size();
  }

  void add_as_input__one(MFParamsBuilder &params, const MFDataType &data_type) const
  {
    BLI_assert(this->is_one());

    switch (value_->type) {
      case ValueType::GVArray: {
        params.add_readonly_single_input(this->value_as<VariableValue_GVArray>()->data);
        break;
      }
      case ValueType::GVVectorArray: {
        params.add_readonly_vector_input(this->value_as<VariableValue_GVVectorArray>()->data);
        break;
      }
      case ValueType::OneSingle: {
        const auto *value_typed = this->value_as<VariableValue_OneSingle>();
        BLI_assert(value_typed->is_initialized);
        GPointer ptr{data_type.single_type(), value_typed->data};
        params.add_readonly_single_input(ptr);
        break;
      }
      case ValueType::OneVector: {
        params.add_readonly_vector_input(this->value_as<VariableValue_OneVector>()->data);
        break;
      }
      case ValueType::Span:
      case ValueType::GVectorArray: {
        BLI_assert_unreachable();
        break;
      }
    }
  }

  void ensure_is_mutable__one(const MFDataType &data_type, ValueAllocator &value_allocator)
  {
    BLI_assert(this->is_one());
    if (ELEM(value_->type, ValueType::OneSingle, ValueType::OneVector)) {
      return;
    }

    switch (data_type.category()) {
      case MFDataType::Single: {
        const CPPType &type = data_type.single_type();
        VariableValue_OneSingle *new_value = value_allocator.obtain_OneSingle(type);
        if (value_->type == ValueType::GVArray) {
          this->value_as<VariableValue_GVArray>()->data.get_internal_single_to_uninitialized(
              new_value->data);
          new_value->is_initialized = true;
        }
        else if (value_->type == ValueType::Span) {
          BLI_assert(tot_initialized_ == 0);
          /* Nothing to do, the single value is uninitialized already. */
        }
        else {
          BLI_assert_unreachable();
        }
        value_allocator.release_value(value_, data_type);
        value_ = new_value;
        break;
      }
      case MFDataType::Vector: {
        const CPPType &type = data_type.vector_base_type();
        VariableValue_OneVector *new_value = value_allocator.obtain_OneVector(type);
        if (value_->type == ValueType::GVVectorArray) {
          const GVVectorArray &old_vector_array =
              this->value_as<VariableValue_GVVectorArray>()->data;
          new_value->data.extend(IndexRange(1), old_vector_array);
        }
        else if (value_->type == ValueType::GVectorArray) {
          BLI_assert(tot_initialized_ == 0);
          /* Nothing to do. */
        }
        else {
          BLI_assert_unreachable();
        }
        value_allocator.release_value(value_, data_type);
        value_ = new_value;
        break;
      }
    }
  }

  void add_as_mutable__one(MFParamsBuilder &params,
                           const MFDataType &data_type,
                           ValueAllocator &value_allocator)
  {
    BLI_assert(this->is_one());
    this->ensure_is_mutable__one(data_type, value_allocator);

    switch (value_->type) {
      case ValueType::OneSingle: {
        auto *value_typed = this->value_as<VariableValue_OneSingle>();
        BLI_assert(value_typed->is_initialized);
        params.add_single_mutable(GMutableSpan{data_type.single_type(), value_typed->data, 1});
        break;
      }
      case ValueType::OneVector: {
        params.add_vector_mutable(this->value_as<VariableValue_OneVector>()->data);
        break;
      }
      case ValueType::GVArray:
      case ValueType::Span:
      case ValueType::GVVectorArray:
      case ValueType::GVectorArray: {
        BLI_assert_unreachable();
        break;
      }
    }
  }

  void add_as_output__one(MFParamsBuilder &params,
                          IndexMask mask,
                          const MFDataType &data_type,
                          ValueAllocator &value_allocator)
  {
    BLI_assert(this->is_one());
    this->ensure_is_mutable__one(data_type, value_allocator);

    switch (value_->type) {
      case ValueType::OneSingle: {
        auto *value_typed = this->value_as<VariableValue_OneSingle>();
        BLI_assert(!value_typed->is_initialized);
        params.add_uninitialized_single_output(
            GMutableSpan{data_type.single_type(), value_typed->data, 1});
        /* It becomes initialized when the multi-function is called. */
        value_typed->is_initialized = true;
        break;
      }
      case ValueType::OneVector: {
        auto *value_typed = this->value_as<VariableValue_OneVector>();
        BLI_assert(value_typed->data[0].is_empty());
        params.add_vector_output(value_typed->data);
        break;
      }
      case ValueType::GVArray:
      case ValueType::Span:
      case ValueType::GVVectorArray:
      case ValueType::GVectorArray: {
        BLI_assert_unreachable();
        break;
      }
    }

    tot_initialized_ += mask.size();
  }

  void destruct(IndexMask mask,
                IndexMask full_mask,
                const MFDataType &data_type,
                ValueAllocator &value_allocator)
  {
    int new_tot_initialized = tot_initialized_ - mask.size();

    /* Sanity check to make sure that enough indices can be destructed. */
    BLI_assert(new_tot_initialized >= 0);

    switch (value_->type) {
      case ValueType::GVArray: {
        if (mask.size() == full_mask.size()) {
          /* All elements are destructed. The elements are owned by the caller, so we don't
           * actually destruct them. */
          value_allocator.release_value(value_, data_type);
          value_ = value_allocator.obtain_OneSingle(data_type.single_type());
        }
        else {
          /* Not all elements are destructed. Since we can't work on the original array, we have to
           * create a copy first. */
          this->ensure_is_mutable(full_mask, data_type, value_allocator);
          BLI_assert(value_->type == ValueType::Span);
          const CPPType &type = data_type.single_type();
          type.destruct_indices(this->value_as<VariableValue_Span>()->data, mask);
        }
        break;
      }
      case ValueType::Span: {
        const CPPType &type = data_type.single_type();
        type.destruct_indices(this->value_as<VariableValue_Span>()->data, mask);
        if (new_tot_initialized == 0) {
          /* Release span when all values are initialized. */
          value_allocator.release_value(value_, data_type);
          value_ = value_allocator.obtain_OneSingle(data_type.single_type());
        }
        break;
      }
      case ValueType::GVVectorArray: {
        if (mask.size() == full_mask.size()) {
          /* All elements are cleared. The elements are owned by the caller, so don't actually
           * destruct them. */
          value_allocator.release_value(value_, data_type);
          value_ = value_allocator.obtain_OneVector(data_type.vector_base_type());
        }
        else {
          /* Not all elements are cleared. Since we can't work on the original vector array, we
           * have to create a copy first. A possible future optimization is to create the partial
           * copy directly. */
          this->ensure_is_mutable(full_mask, data_type, value_allocator);
          BLI_assert(value_->type == ValueType::GVectorArray);
          this->value_as<VariableValue_GVectorArray>()->data.clear(mask);
        }
        break;
      }
      case ValueType::GVectorArray: {
        this->value_as<VariableValue_GVectorArray>()->data.clear(mask);
        break;
      }
      case ValueType::OneSingle: {
        auto *value_typed = this->value_as<VariableValue_OneSingle>();
        BLI_assert(value_typed->is_initialized);
        if (mask.size() == tot_initialized_) {
          const CPPType &type = data_type.single_type();
          type.destruct(value_typed->data);
          value_typed->is_initialized = false;
        }
        break;
      }
      case ValueType::OneVector: {
        auto *value_typed = this->value_as<VariableValue_OneVector>();
        if (mask.size() == tot_initialized_) {
          value_typed->data.clear({0});
        }
        break;
      }
    }

    tot_initialized_ = new_tot_initialized;
  }

  void indices_split(IndexMask mask, IndicesSplitVectors &r_indices)
  {
    BLI_assert(mask.size() <= tot_initialized_);

    switch (value_->type) {
      case ValueType::GVArray: {
        const GVArray_Typed<bool> varray{this->value_as<VariableValue_GVArray>()->data};
        for (const int i : mask) {
          r_indices[varray[i]].append(i);
        }
        break;
      }
      case ValueType::Span: {
        const Span<bool> span((bool *)this->value_as<VariableValue_Span>()->data,
                              mask.min_array_size());
        for (const int i : mask) {
          r_indices[span[i]].append(i);
        }
        break;
      }
      case ValueType::OneSingle: {
        auto *value_typed = this->value_as<VariableValue_OneSingle>();
        BLI_assert(value_typed->is_initialized);
        const bool condition = *(bool *)value_typed->data;
        r_indices[condition].extend(mask);
        break;
      }
      case ValueType::GVVectorArray:
      case ValueType::GVectorArray:
      case ValueType::OneVector: {
        BLI_assert_unreachable();
        break;
      }
    }
  }

  template<typename T> T *value_as()
  {
    BLI_assert(value_->type == T::static_type);
    return static_cast<T *>(value_);
  }

  template<typename T> const T *value_as() const
  {
    BLI_assert(value_->type == T::static_type);
    return static_cast<T *>(value_);
  }
};

template<typename... Args> VariableState *ValueAllocator::obtain_variable_state(Args &&...args)
{
  return new VariableState(std::forward<Args>(args)...);
}

void ValueAllocator::release_variable_state(VariableState *state)
{
  delete state;
}

/** Keeps track of the states of all variables during evaluation. */
class VariableStates {
 private:
  ValueAllocator value_allocator_;
  Map<const MFVariable *, VariableState *> variable_states_;
  IndexMask full_mask_;

 public:
  VariableStates(IndexMask full_mask) : full_mask_(full_mask)
  {
  }

  ~VariableStates()
  {
    for (auto &&item : variable_states_.items()) {
      const MFVariable *variable = item.key;
      VariableState *state = item.value;
      state->destruct_self(value_allocator_, variable->data_type());
    }
  }

  ValueAllocator &value_allocator()
  {
    return value_allocator_;
  }

  const IndexMask &full_mask() const
  {
    return full_mask_;
  }

  void add_initial_variable_states(const MFProcedureExecutor &fn,
                                   const MFProcedure &procedure,
                                   MFParams &params)
  {
    for (const int param_index : fn.param_indices()) {
      MFParamType param_type = fn.param_type(param_index);
      const MFVariable *variable = procedure.params()[param_index].variable;

      auto add_state = [&](VariableValue *value,
                           bool input_is_initialized,
                           void *caller_provided_storage = nullptr) {
        const int tot_initialized = input_is_initialized ? full_mask_.size() : 0;
        variable_states_.add_new(variable,
                                 value_allocator_.obtain_variable_state(
                                     *value, tot_initialized, caller_provided_storage));
      };

      switch (param_type.category()) {
        case MFParamType::SingleInput: {
          const GVArray &data = params.readonly_single_input(param_index);
          add_state(value_allocator_.obtain_GVArray(data), true);
          break;
        }
        case MFParamType::VectorInput: {
          const GVVectorArray &data = params.readonly_vector_input(param_index);
          add_state(value_allocator_.obtain_GVVectorArray(data), true);
          break;
        }
        case MFParamType::SingleOutput: {
          GMutableSpan data = params.uninitialized_single_output(param_index);
          add_state(value_allocator_.obtain_Span_not_owned(data.data()), false, data.data());
          break;
        }
        case MFParamType::VectorOutput: {
          GVectorArray &data = params.vector_output(param_index);
          add_state(value_allocator_.obtain_GVectorArray_not_owned(data), false, &data);
          break;
        }
        case MFParamType::SingleMutable: {
          GMutableSpan data = params.single_mutable(param_index);
          add_state(value_allocator_.obtain_Span_not_owned(data.data()), true, data.data());
          break;
        }
        case MFParamType::VectorMutable: {
          GVectorArray &data = params.vector_mutable(param_index);
          add_state(value_allocator_.obtain_GVectorArray_not_owned(data), true, &data);
          break;
        }
      }
    }
  }

  void add_as_param(VariableState &variable_state,
                    MFParamsBuilder &params,
                    const MFParamType &param_type,
                    const IndexMask &mask)
  {
    const MFDataType data_type = param_type.data_type();
    switch (param_type.interface_type()) {
      case MFParamType::Input: {
        variable_state.add_as_input(params, mask, data_type);
        break;
      }
      case MFParamType::Mutable: {
        variable_state.add_as_mutable(params, mask, full_mask_, data_type, value_allocator_);
        break;
      }
      case MFParamType::Output: {
        variable_state.add_as_output(params, mask, full_mask_, data_type, value_allocator_);
        break;
      }
    }
  }

  void add_as_param__one(VariableState &variable_state,
                         MFParamsBuilder &params,
                         const MFParamType &param_type,
                         const IndexMask &mask)
  {
    const MFDataType data_type = param_type.data_type();
    switch (param_type.interface_type()) {
      case MFParamType::Input: {
        variable_state.add_as_input__one(params, data_type);
        break;
      }
      case MFParamType::Mutable: {
        variable_state.add_as_mutable__one(params, data_type, value_allocator_);
        break;
      }
      case MFParamType::Output: {
        variable_state.add_as_output__one(params, mask, data_type, value_allocator_);
        break;
      }
    }
  }

  void destruct(const MFVariable &variable, const IndexMask &mask)
  {
    VariableState &variable_state = this->get_variable_state(variable);
    variable_state.destruct(mask, full_mask_, variable.data_type(), value_allocator_);
  }

  VariableState &get_variable_state(const MFVariable &variable)
  {
    return *variable_states_.lookup_or_add_cb(
        &variable, [&]() { return this->create_new_state_for_variable(variable); });
  }

  VariableState *create_new_state_for_variable(const MFVariable &variable)
  {
    MFDataType data_type = variable.data_type();
    switch (data_type.category()) {
      case MFDataType::Single: {
        const CPPType &type = data_type.single_type();
        return value_allocator_.obtain_variable_state(*value_allocator_.obtain_OneSingle(type), 0);
      }
      case MFDataType::Vector: {
        const CPPType &type = data_type.vector_base_type();
        return value_allocator_.obtain_variable_state(*value_allocator_.obtain_OneVector(type), 0);
      }
    }
    BLI_assert_unreachable();
    return nullptr;
  }
};

static bool evaluate_as_one(const MultiFunction &fn,
                            Span<VariableState *> param_variable_states,
                            const IndexMask &mask,
                            const IndexMask &full_mask)
{
  if (fn.depends_on_context()) {
    return false;
  }
  if (mask.size() < full_mask.size()) {
    return false;
  }
  for (VariableState *state : param_variable_states) {
    if (state != nullptr && !state->is_one()) {
      return false;
    }
  }
  return true;
}

static void execute_call_instruction(const MFCallInstruction &instruction,
                                     IndexMask mask,
                                     VariableStates &variable_states,
                                     const MFContext &context)
{
  const MultiFunction &fn = instruction.fn();

  Vector<VariableState *> param_variable_states;
  param_variable_states.resize(fn.param_amount());

  for (const int param_index : fn.param_indices()) {
    const MFVariable *variable = instruction.params()[param_index];
    if (variable == nullptr) {
      param_variable_states[param_index] = nullptr;
    }
    else {
      VariableState &variable_state = variable_states.get_variable_state(*variable);
      param_variable_states[param_index] = &variable_state;
    }
  }

  /* If all inputs to the function are constant, it's enough to call the function only once instead
   * of for every index. */
  if (evaluate_as_one(fn, param_variable_states, mask, variable_states.full_mask())) {
    MFParamsBuilder params(fn, 1);

    for (const int param_index : fn.param_indices()) {
      const MFParamType param_type = fn.param_type(param_index);
      VariableState *variable_state = param_variable_states[param_index];
      if (variable_state == nullptr) {
        params.add_ignored_single_output();
      }
      else {
        variable_states.add_as_param__one(*variable_state, params, param_type, mask);
      }
    }

    try {
      fn.call(IndexRange(1), params, context);
    }
    catch (...) {
      /* Multi-functions must not throw exceptions. */
      BLI_assert_unreachable();
    }
  }
  else {
    MFParamsBuilder params(fn, &mask);

    for (const int param_index : fn.param_indices()) {
      const MFParamType param_type = fn.param_type(param_index);
      VariableState *variable_state = param_variable_states[param_index];
      if (variable_state == nullptr) {
        params.add_ignored_single_output();
      }
      else {
        variable_states.add_as_param(*variable_state, params, param_type, mask);
      }
    }

    try {
      fn.call(mask, params, context);
    }
    catch (...) {
      /* Multi-functions must not throw exceptions. */
      BLI_assert_unreachable();
    }
  }
}

/** An index mask, that might own the indices if necessary. */
struct InstructionIndices {
  bool is_owned;
  Vector<int64_t> owned_indices;
  IndexMask referenced_indices;

  IndexMask mask() const
  {
    if (this->is_owned) {
      return this->owned_indices.as_span();
    }
    return this->referenced_indices;
  }
};

/** Contains information about the next instruction that should be executed. */
struct NextInstructionInfo {
  const MFInstruction *instruction = nullptr;
  InstructionIndices indices;

  IndexMask mask() const
  {
    return this->indices.mask();
  }

  operator bool() const
  {
    return this->instruction != nullptr;
  }
};

/**
 * Keeps track of the next instruction for all indices and decides in which order instructions are
 * evaluated.
 */
class InstructionScheduler {
 private:
  Map<const MFInstruction *, Vector<InstructionIndices>> indices_by_instruction_;

 public:
  InstructionScheduler() = default;

  void add_referenced_indices(const MFInstruction &instruction, IndexMask mask)
  {
    if (mask.is_empty()) {
      return;
    }
    InstructionIndices new_indices;
    new_indices.is_owned = false;
    new_indices.referenced_indices = mask;
    indices_by_instruction_.lookup_or_add_default(&instruction).append(std::move(new_indices));
  }

  void add_owned_indices(const MFInstruction &instruction, Vector<int64_t> indices)
  {
    if (indices.is_empty()) {
      return;
    }
    BLI_assert(IndexMask::indices_are_valid_index_mask(indices));

    InstructionIndices new_indices;
    new_indices.is_owned = true;
    new_indices.owned_indices = std::move(indices);
    indices_by_instruction_.lookup_or_add_default(&instruction).append(std::move(new_indices));
  }

  void add_previous_instruction_indices(const MFInstruction &instruction,
                                        NextInstructionInfo &instr_info)
  {
    indices_by_instruction_.lookup_or_add_default(&instruction)
        .append(std::move(instr_info.indices));
  }

  NextInstructionInfo pop_next()
  {
    if (indices_by_instruction_.is_empty()) {
      return {};
    }
    /* TODO: Implement better mechanism to determine next instruction. */
    const MFInstruction *instruction = *indices_by_instruction_.keys().begin();

    NextInstructionInfo next_instruction_info;
    next_instruction_info.instruction = instruction;
    next_instruction_info.indices = this->pop_indices_array(instruction);
    return next_instruction_info;
  }

 private:
  InstructionIndices pop_indices_array(const MFInstruction *instruction)
  {
    Vector<InstructionIndices> *indices = indices_by_instruction_.lookup_ptr(instruction);
    if (indices == nullptr) {
      return {};
    }
    InstructionIndices r_indices = (*indices).pop_last();
    BLI_assert(!r_indices.mask().is_empty());
    if (indices->is_empty()) {
      indices_by_instruction_.remove_contained(instruction);
    }
    return r_indices;
  }
};

void MFProcedureExecutor::call(IndexMask full_mask, MFParams params, MFContext context) const
{
  BLI_assert(procedure_.validate());

  LinearAllocator<> allocator;

  VariableStates variable_states{full_mask};
  variable_states.add_initial_variable_states(*this, procedure_, params);

  InstructionScheduler scheduler;
  scheduler.add_referenced_indices(*procedure_.entry(), full_mask);

  /* Loop until all indices got to a return instruction. */
  while (NextInstructionInfo instr_info = scheduler.pop_next()) {
    const MFInstruction &instruction = *instr_info.instruction;
    switch (instruction.type()) {
      case MFInstructionType::Call: {
        const MFCallInstruction &call_instruction = static_cast<const MFCallInstruction &>(
            instruction);
        execute_call_instruction(call_instruction, instr_info.mask(), variable_states, context);
        scheduler.add_previous_instruction_indices(*call_instruction.next(), instr_info);
        break;
      }
      case MFInstructionType::Branch: {
        const MFBranchInstruction &branch_instruction = static_cast<const MFBranchInstruction &>(
            instruction);
        const MFVariable *condition_var = branch_instruction.condition();
        VariableState &variable_state = variable_states.get_variable_state(*condition_var);

        IndicesSplitVectors new_indices;
        variable_state.indices_split(instr_info.mask(), new_indices);
        scheduler.add_owned_indices(*branch_instruction.branch_false(), new_indices[false]);
        scheduler.add_owned_indices(*branch_instruction.branch_true(), new_indices[true]);
        break;
      }
      case MFInstructionType::Destruct: {
        const MFDestructInstruction &destruct_instruction =
            static_cast<const MFDestructInstruction &>(instruction);
        const MFVariable *variable = destruct_instruction.variable();
        variable_states.destruct(*variable, instr_info.mask());
        scheduler.add_previous_instruction_indices(*destruct_instruction.next(), instr_info);
        break;
      }
      case MFInstructionType::Dummy: {
        const MFDummyInstruction &dummy_instruction = static_cast<const MFDummyInstruction &>(
            instruction);
        scheduler.add_previous_instruction_indices(*dummy_instruction.next(), instr_info);
        break;
      }
      case MFInstructionType::Return: {
        /* Don't insert the indices back into the scheduler. */
        break;
      }
    }
  }

  for (const int param_index : this->param_indices()) {
    const MFParamType param_type = this->param_type(param_index);
    const MFVariable *variable = procedure_.params()[param_index].variable;
    VariableState &variable_state = variable_states.get_variable_state(*variable);
    switch (param_type.interface_type()) {
      case MFParamType::Input: {
        /* Input variables must be destructed in the end. */
        BLI_assert(variable_state.is_fully_uninitialized(full_mask));
        break;
      }
      case MFParamType::Mutable:
      case MFParamType::Output: {
        /* Mutable and output variables must be initialized in the end. */
        BLI_assert(variable_state.is_fully_initialized(full_mask));
        /* Make sure that the data is in the memory provided by the caller. */
        variable_state.ensure_is_mutable(
            full_mask, param_type.data_type(), variable_states.value_allocator());
        break;
      }
    }
  }
}

}  // namespace blender::fn
