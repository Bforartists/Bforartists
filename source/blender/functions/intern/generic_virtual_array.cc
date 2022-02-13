/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "FN_generic_virtual_array.hh"

namespace blender::fn {

/* -------------------------------------------------------------------- */
/** \name #GVArrayImpl
 * \{ */

void GVArrayImpl::materialize(const IndexMask mask, void *dst) const
{
  for (const int64_t i : mask) {
    void *elem_dst = POINTER_OFFSET(dst, type_->size() * i);
    this->get(i, elem_dst);
  }
}

void GVArrayImpl::materialize_to_uninitialized(const IndexMask mask, void *dst) const
{
  for (const int64_t i : mask) {
    void *elem_dst = POINTER_OFFSET(dst, type_->size() * i);
    this->get_to_uninitialized(i, elem_dst);
  }
}

void GVArrayImpl::get(const int64_t index, void *r_value) const
{
  type_->destruct(r_value);
  this->get_to_uninitialized(index, r_value);
}

bool GVArrayImpl::is_span() const
{
  return false;
}

GSpan GVArrayImpl::get_internal_span() const
{
  BLI_assert(false);
  return GSpan(*type_);
}

bool GVArrayImpl::is_single() const
{
  return false;
}

void GVArrayImpl::get_internal_single(void *UNUSED(r_value)) const
{
  BLI_assert(false);
}

bool GVArrayImpl::try_assign_VArray(void *UNUSED(varray)) const
{
  return false;
}

bool GVArrayImpl::may_have_ownership() const
{
  /* Use true as default to avoid accidentally creating subclasses that have this set to false but
   * actually own data. Subclasses should set the to false instead. */
  return true;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVMutableArrayImpl
 * \{ */

GVMutableArrayImpl::GVMutableArrayImpl(const CPPType &type, const int64_t size)
    : GVArrayImpl(type, size)
{
}

void GVMutableArrayImpl::set_by_copy(const int64_t index, const void *value)
{
  BUFFER_FOR_CPP_TYPE_VALUE(*type_, buffer);
  type_->copy_construct(value, buffer);
  this->set_by_move(index, buffer);
  type_->destruct(buffer);
}

void GVMutableArrayImpl::set_by_relocate(const int64_t index, void *value)
{
  this->set_by_move(index, value);
  type_->destruct(value);
}

void GVMutableArrayImpl::set_all(const void *src)
{
  if (this->is_span()) {
    const GSpan span = this->get_internal_span();
    type_->copy_assign_n(src, const_cast<void *>(span.data()), size_);
  }
  else {
    for (int64_t i : IndexRange(size_)) {
      this->set_by_copy(i, POINTER_OFFSET(src, type_->size() * i));
    }
  }
}

void GVMutableArray::fill(const void *value)
{
  if (this->is_span()) {
    const GSpan span = this->get_internal_span();
    this->type().fill_assign_n(value, const_cast<void *>(span.data()), this->size());
  }
  else {
    for (int64_t i : IndexRange(this->size())) {
      this->set_by_copy(i, value);
    }
  }
}

bool GVMutableArrayImpl::try_assign_VMutableArray(void *UNUSED(varray)) const
{
  return false;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArrayImpl_For_GSpan
 * \{ */

GVArrayImpl_For_GSpan::GVArrayImpl_For_GSpan(const GMutableSpan span)
    : GVMutableArrayImpl(span.type(), span.size()),
      data_(span.data()),
      element_size_(span.type().size())
{
}

GVArrayImpl_For_GSpan::GVArrayImpl_For_GSpan(const CPPType &type, const int64_t size)
    : GVMutableArrayImpl(type, size), element_size_(type.size())
{
}

void GVArrayImpl_For_GSpan::get(const int64_t index, void *r_value) const
{
  type_->copy_assign(POINTER_OFFSET(data_, element_size_ * index), r_value);
}

void GVArrayImpl_For_GSpan::get_to_uninitialized(const int64_t index, void *r_value) const
{
  type_->copy_construct(POINTER_OFFSET(data_, element_size_ * index), r_value);
}

void GVArrayImpl_For_GSpan::set_by_copy(const int64_t index, const void *value)
{
  type_->copy_assign(value, POINTER_OFFSET(data_, element_size_ * index));
}

void GVArrayImpl_For_GSpan::set_by_move(const int64_t index, void *value)
{
  type_->move_construct(value, POINTER_OFFSET(data_, element_size_ * index));
}

void GVArrayImpl_For_GSpan::set_by_relocate(const int64_t index, void *value)
{
  type_->relocate_assign(value, POINTER_OFFSET(data_, element_size_ * index));
}

bool GVArrayImpl_For_GSpan::is_span() const
{
  return true;
}

GSpan GVArrayImpl_For_GSpan::get_internal_span() const
{
  return GSpan(*type_, data_, size_);
}

class GVArrayImpl_For_GSpan_final final : public GVArrayImpl_For_GSpan {
 public:
  using GVArrayImpl_For_GSpan::GVArrayImpl_For_GSpan;

 private:
  bool may_have_ownership() const override
  {
    return false;
  }
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArrayImpl_For_SingleValueRef
 * \{ */

/* Generic virtual array where each element has the same value. The value is not owned. */
class GVArrayImpl_For_SingleValueRef : public GVArrayImpl {
 protected:
  const void *value_ = nullptr;

 public:
  GVArrayImpl_For_SingleValueRef(const CPPType &type, const int64_t size, const void *value)
      : GVArrayImpl(type, size), value_(value)
  {
  }

 protected:
  GVArrayImpl_For_SingleValueRef(const CPPType &type, const int64_t size) : GVArrayImpl(type, size)
  {
  }

  void get(const int64_t UNUSED(index), void *r_value) const override
  {
    type_->copy_assign(value_, r_value);
  }
  void get_to_uninitialized(const int64_t UNUSED(index), void *r_value) const override
  {
    type_->copy_construct(value_, r_value);
  }

  bool is_span() const override
  {
    return size_ == 1;
  }
  GSpan get_internal_span() const override
  {
    return GSpan{*type_, value_, 1};
  }

  bool is_single() const override
  {
    return true;
  }
  void get_internal_single(void *r_value) const override
  {
    type_->copy_assign(value_, r_value);
  }
};

class GVArrayImpl_For_SingleValueRef_final final : public GVArrayImpl_For_SingleValueRef {
 public:
  using GVArrayImpl_For_SingleValueRef::GVArrayImpl_For_SingleValueRef;

 private:
  bool may_have_ownership() const override
  {
    return false;
  }
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArrayImpl_For_SingleValue
 * \{ */

/* Same as GVArrayImpl_For_SingleValueRef, but the value is owned. */
class GVArrayImpl_For_SingleValue : public GVArrayImpl_For_SingleValueRef,
                                    NonCopyable,
                                    NonMovable {
 public:
  GVArrayImpl_For_SingleValue(const CPPType &type, const int64_t size, const void *value)
      : GVArrayImpl_For_SingleValueRef(type, size)
  {
    value_ = MEM_mallocN_aligned(type.size(), type.alignment(), __func__);
    type.copy_construct(value, (void *)value_);
  }

  ~GVArrayImpl_For_SingleValue() override
  {
    type_->destruct((void *)value_);
    MEM_freeN((void *)value_);
  }
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArrayImpl_For_SmallTrivialSingleValue
 * \{ */

/**
 * Contains an inline buffer that can store a single value of a trivial type.
 * This avoids the allocation that would be done by #GVArrayImpl_For_SingleValue.
 */
template<int BufferSize> class GVArrayImpl_For_SmallTrivialSingleValue : public GVArrayImpl {
 private:
  AlignedBuffer<BufferSize, 8> buffer_;

 public:
  GVArrayImpl_For_SmallTrivialSingleValue(const CPPType &type,
                                          const int64_t size,
                                          const void *value)
      : GVArrayImpl(type, size)
  {
    BLI_assert(type.is_trivial());
    BLI_assert(type.alignment() <= 8);
    BLI_assert(type.size() <= BufferSize);
    type.copy_construct(value, &buffer_);
  }

 private:
  void get(const int64_t UNUSED(index), void *r_value) const override
  {
    this->copy_value_to(r_value);
  }
  void get_to_uninitialized(const int64_t UNUSED(index), void *r_value) const override
  {
    this->copy_value_to(r_value);
  }

  bool is_single() const override
  {
    return true;
  }
  void get_internal_single(void *r_value) const override
  {
    this->copy_value_to(r_value);
  }

  void copy_value_to(void *dst) const
  {
    memcpy(dst, &buffer_, type_->size());
  }
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArray_GSpan
 * \{ */

GVArray_GSpan::GVArray_GSpan(GVArray varray) : GSpan(varray.type()), varray_(std::move(varray))
{
  size_ = varray_.size();
  if (varray_.is_span()) {
    data_ = varray_.get_internal_span().data();
  }
  else {
    owned_data_ = MEM_mallocN_aligned(type_->size() * size_, type_->alignment(), __func__);
    varray_.materialize_to_uninitialized(IndexRange(size_), owned_data_);
    data_ = owned_data_;
  }
}

GVArray_GSpan::~GVArray_GSpan()
{
  if (owned_data_ != nullptr) {
    type_->destruct_n(owned_data_, size_);
    MEM_freeN(owned_data_);
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVMutableArray_GSpan
 * \{ */

GVMutableArray_GSpan::GVMutableArray_GSpan(GVMutableArray varray, const bool copy_values_to_span)
    : GMutableSpan(varray.type()), varray_(std::move(varray))
{
  size_ = varray_.size();
  if (varray_.is_span()) {
    data_ = varray_.get_internal_span().data();
  }
  else {
    owned_data_ = MEM_mallocN_aligned(type_->size() * size_, type_->alignment(), __func__);
    if (copy_values_to_span) {
      varray_.materialize_to_uninitialized(IndexRange(size_), owned_data_);
    }
    else {
      type_->default_construct_n(owned_data_, size_);
    }
    data_ = owned_data_;
  }
}

GVMutableArray_GSpan::~GVMutableArray_GSpan()
{
  if (show_not_saved_warning_) {
    if (!save_has_been_called_) {
      std::cout << "Warning: Call `apply()` to make sure that changes persist in all cases.\n";
    }
  }
  if (owned_data_ != nullptr) {
    type_->destruct_n(owned_data_, size_);
    MEM_freeN(owned_data_);
  }
}

void GVMutableArray_GSpan::save()
{
  save_has_been_called_ = true;
  if (data_ != owned_data_) {
    return;
  }
  const int64_t element_size = type_->size();
  for (int64_t i : IndexRange(size_)) {
    varray_.set_by_copy(i, POINTER_OFFSET(owned_data_, element_size * i));
  }
}

void GVMutableArray_GSpan::disable_not_applied_warning()
{
  show_not_saved_warning_ = false;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArrayImpl_For_SlicedGVArray
 * \{ */

class GVArrayImpl_For_SlicedGVArray : public GVArrayImpl {
 protected:
  GVArray varray_;
  int64_t offset_;
  IndexRange slice_;

 public:
  GVArrayImpl_For_SlicedGVArray(GVArray varray, const IndexRange slice)
      : GVArrayImpl(varray.type(), slice.size()),
        varray_(std::move(varray)),
        offset_(slice.start()),
        slice_(slice)
  {
    BLI_assert(slice.one_after_last() <= varray_.size());
  }

  void get(const int64_t index, void *r_value) const override
  {
    varray_.get(index + offset_, r_value);
  }

  void get_to_uninitialized(const int64_t index, void *r_value) const override
  {
    varray_.get_to_uninitialized(index + offset_, r_value);
  }

  bool is_span() const override
  {
    return varray_.is_span();
  }
  GSpan get_internal_span() const override
  {
    return varray_.get_internal_span().slice(slice_);
  }

  bool is_single() const override
  {
    return varray_.is_single();
  }
  void get_internal_single(void *r_value) const override
  {
    varray_.get_internal_single(r_value);
  }
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArrayCommon
 * \{ */

GVArrayCommon::GVArrayCommon() = default;

GVArrayCommon::GVArrayCommon(const GVArrayCommon &other) : storage_(other.storage_)
{
  impl_ = this->impl_from_storage();
}

GVArrayCommon::GVArrayCommon(GVArrayCommon &&other) noexcept : storage_(std::move(other.storage_))
{
  impl_ = this->impl_from_storage();
  other.storage_.reset();
  other.impl_ = nullptr;
}

GVArrayCommon::GVArrayCommon(const GVArrayImpl *impl) : impl_(impl)
{
  storage_ = impl_;
}

GVArrayCommon::GVArrayCommon(std::shared_ptr<const GVArrayImpl> impl) : impl_(impl.get())
{
  if (impl) {
    storage_ = std::move(impl);
  }
}

GVArrayCommon::~GVArrayCommon() = default;

void GVArrayCommon::materialize(void *dst) const
{
  this->materialize(IndexMask(impl_->size()), dst);
}

void GVArrayCommon::materialize(const IndexMask mask, void *dst) const
{
  impl_->materialize(mask, dst);
}

void GVArrayCommon::materialize_to_uninitialized(void *dst) const
{
  this->materialize_to_uninitialized(IndexMask(impl_->size()), dst);
}

void GVArrayCommon::materialize_to_uninitialized(const IndexMask mask, void *dst) const
{
  BLI_assert(mask.min_array_size() <= impl_->size());
  impl_->materialize_to_uninitialized(mask, dst);
}

bool GVArrayCommon::may_have_ownership() const
{
  return impl_->may_have_ownership();
}

void GVArrayCommon::copy_from(const GVArrayCommon &other)
{
  if (this == &other) {
    return;
  }
  storage_ = other.storage_;
  impl_ = this->impl_from_storage();
}

void GVArrayCommon::move_from(GVArrayCommon &&other) noexcept
{
  if (this == &other) {
    return;
  }
  storage_ = std::move(other.storage_);
  impl_ = this->impl_from_storage();
  other.storage_.reset();
  other.impl_ = nullptr;
}

bool GVArrayCommon::is_span() const
{
  return impl_->is_span();
}

GSpan GVArrayCommon::get_internal_span() const
{
  BLI_assert(this->is_span());
  return impl_->get_internal_span();
}

bool GVArrayCommon::is_single() const
{
  return impl_->is_single();
}

void GVArrayCommon::get_internal_single(void *r_value) const
{
  BLI_assert(this->is_single());
  impl_->get_internal_single(r_value);
}

void GVArrayCommon::get_internal_single_to_uninitialized(void *r_value) const
{
  impl_->type().default_construct(r_value);
  this->get_internal_single(r_value);
}

const GVArrayImpl *GVArrayCommon::impl_from_storage() const
{
  return storage_.extra_info().get_varray(storage_.get());
}

IndexRange GVArrayCommon::index_range() const
{
  return IndexRange(this->size());
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVArray
 * \{ */

GVArray::GVArray(const GVArray &other) = default;

GVArray::GVArray(GVArray &&other) noexcept = default;

GVArray::GVArray(const GVArrayImpl *impl) : GVArrayCommon(impl)
{
}

GVArray::GVArray(std::shared_ptr<const GVArrayImpl> impl) : GVArrayCommon(std::move(impl))
{
}

GVArray GVArray::ForSingle(const CPPType &type, const int64_t size, const void *value)
{
  if (type.is_trivial() && type.size() <= 16 && type.alignment() <= 8) {
    return GVArray::For<GVArrayImpl_For_SmallTrivialSingleValue<16>>(type, size, value);
  }
  return GVArray::For<GVArrayImpl_For_SingleValue>(type, size, value);
}

GVArray GVArray::ForSingleRef(const CPPType &type, const int64_t size, const void *value)
{
  return GVArray::For<GVArrayImpl_For_SingleValueRef_final>(type, size, value);
}

GVArray GVArray::ForSingleDefault(const CPPType &type, const int64_t size)
{
  return GVArray::ForSingleRef(type, size, type.default_value());
}

GVArray GVArray::ForSpan(GSpan span)
{
  /* Use const-cast because the underlying virtual array implementation is shared between const
   * and non const data. */
  GMutableSpan mutable_span{span.type(), const_cast<void *>(span.data()), span.size()};
  return GVArray::For<GVArrayImpl_For_GSpan_final>(mutable_span);
}

class GVArrayImpl_For_GArray : public GVArrayImpl_For_GSpan {
 protected:
  GArray<> array_;

 public:
  GVArrayImpl_For_GArray(GArray<> array)
      : GVArrayImpl_For_GSpan(array.as_mutable_span()), array_(std::move(array))
  {
  }
};

GVArray GVArray::ForGArray(GArray<> array)
{
  return GVArray::For<GVArrayImpl_For_GArray>(array);
}

GVArray GVArray::ForEmpty(const CPPType &type)
{
  return GVArray::ForSpan(GSpan(type));
}

GVArray GVArray::slice(IndexRange slice) const
{
  return GVArray::For<GVArrayImpl_For_SlicedGVArray>(*this, slice);
}

GVArray &GVArray::operator=(const GVArray &other)
{
  this->copy_from(other);
  return *this;
}

GVArray &GVArray::operator=(GVArray &&other) noexcept
{
  this->move_from(std::move(other));
  return *this;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name #GVMutableArray
 * \{ */

GVMutableArray::GVMutableArray(const GVMutableArray &other) = default;
GVMutableArray::GVMutableArray(GVMutableArray &&other) noexcept = default;

GVMutableArray::GVMutableArray(GVMutableArrayImpl *impl) : GVArrayCommon(impl)
{
}

GVMutableArray::GVMutableArray(std::shared_ptr<GVMutableArrayImpl> impl)
    : GVArrayCommon(std::move(impl))
{
}

GVMutableArray GVMutableArray::ForSpan(GMutableSpan span)
{
  return GVMutableArray::For<GVArrayImpl_For_GSpan_final>(span);
}

GVMutableArray::operator GVArray() const &
{
  GVArray varray;
  varray.copy_from(*this);
  return varray;
}

GVMutableArray::operator GVArray() &&noexcept
{
  GVArray varray;
  varray.move_from(std::move(*this));
  return varray;
}

GVMutableArray &GVMutableArray::operator=(const GVMutableArray &other)
{
  this->copy_from(other);
  return *this;
}

GVMutableArray &GVMutableArray::operator=(GVMutableArray &&other) noexcept
{
  this->move_from(std::move(other));
  return *this;
}

GVMutableArrayImpl *GVMutableArray::get_implementation() const
{
  return this->get_impl();
}

void GVMutableArray::set_all(const void *src)
{
  this->get_impl()->set_all(src);
}

GMutableSpan GVMutableArray::get_internal_span() const
{
  BLI_assert(this->is_span());
  const GSpan span = impl_->get_internal_span();
  return GMutableSpan(span.type(), const_cast<void *>(span.data()), span.size());
}

/** \} */

}  // namespace blender::fn
