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

#include "FN_multi_function_builder.hh"

#include "BLI_hash.hh"

namespace blender::fn {

CustomMF_GenericConstant::CustomMF_GenericConstant(const CPPType &type,
                                                   const void *value,
                                                   bool make_value_copy)
    : type_(type), owns_value_(make_value_copy)
{
  if (make_value_copy) {
    void *copied_value = MEM_mallocN_aligned(type.size(), type.alignment(), __func__);
    type.copy_construct(value, copied_value);
    value = copied_value;
  }
  value_ = value;

  MFSignatureBuilder signature{"Constant " + type.name()};
  std::stringstream ss;
  type.print_or_default(value, ss, type.name());
  signature.single_output(ss.str(), type);
  signature_ = signature.build();
  this->set_signature(&signature_);
}

CustomMF_GenericConstant::~CustomMF_GenericConstant()
{
  if (owns_value_) {
    signature_.param_types[0].data_type().single_type().destruct((void *)value_);
    MEM_freeN((void *)value_);
  }
}

void CustomMF_GenericConstant::call(IndexMask mask,
                                    MFParams params,
                                    MFContext UNUSED(context)) const
{
  GMutableSpan output = params.uninitialized_single_output(0);
  type_.fill_construct_indices(value_, output.data(), mask);
}

uint64_t CustomMF_GenericConstant::hash() const
{
  return type_.hash_or_fallback(value_, (uintptr_t)this);
}

bool CustomMF_GenericConstant::equals(const MultiFunction &other) const
{
  const CustomMF_GenericConstant *_other = dynamic_cast<const CustomMF_GenericConstant *>(&other);
  if (_other == nullptr) {
    return false;
  }
  if (type_ != _other->type_) {
    return false;
  }
  return type_.is_equal(value_, _other->value_);
}

static std::string gspan_to_string(GSpan array)
{
  const CPPType &type = array.type();
  std::stringstream ss;
  ss << "[";
  const int64_t max_amount = 5;
  for (int64_t i : IndexRange(std::min(max_amount, array.size()))) {
    type.print_or_default(array[i], ss, type.name());
    ss << ", ";
  }
  if (max_amount < array.size()) {
    ss << "...";
  }
  ss << "]";
  return ss.str();
}

CustomMF_GenericConstantArray::CustomMF_GenericConstantArray(GSpan array) : array_(array)
{
  const CPPType &type = array.type();
  MFSignatureBuilder signature{"Constant " + type.name() + " Vector"};
  signature.vector_output(gspan_to_string(array), type);
  signature_ = signature.build();
  this->set_signature(&signature_);
}

void CustomMF_GenericConstantArray::call(IndexMask mask,
                                         MFParams params,
                                         MFContext UNUSED(context)) const
{
  GVectorArray &vectors = params.vector_output(0);
  for (int64_t i : mask) {
    vectors.extend(i, array_);
  }
}

CustomMF_DefaultOutput::CustomMF_DefaultOutput(StringRef name,
                                               Span<MFDataType> input_types,
                                               Span<MFDataType> output_types)
    : output_amount_(output_types.size())
{
  MFSignatureBuilder signature{name};
  for (MFDataType data_type : input_types) {
    signature.input("Input", data_type);
  }
  for (MFDataType data_type : output_types) {
    signature.output("Output", data_type);
  }
  signature_ = signature.build();
  this->set_signature(&signature_);
}
void CustomMF_DefaultOutput::call(IndexMask mask, MFParams params, MFContext UNUSED(context)) const
{
  for (int param_index : this->param_indices()) {
    MFParamType param_type = this->param_type(param_index);
    if (!param_type.is_output()) {
      continue;
    }

    if (param_type.data_type().is_single()) {
      GMutableSpan span = params.uninitialized_single_output(param_index);
      const CPPType &type = span.type();
      type.fill_construct_indices(type.default_value(), span.data(), mask);
    }
  }
}

CustomMF_GenericCopy::CustomMF_GenericCopy(StringRef name, MFDataType data_type)
{
  MFSignatureBuilder signature{name};
  signature.input("Input", data_type);
  signature.output("Output", data_type);
  signature_ = signature.build();
  this->set_signature(&signature_);
}

void CustomMF_GenericCopy::call(IndexMask mask, MFParams params, MFContext UNUSED(context)) const
{
  const MFDataType data_type = this->param_type(0).data_type();
  switch (data_type.category()) {
    case MFDataType::Single: {
      const GVArray &inputs = params.readonly_single_input(0, "Input");
      GMutableSpan outputs = params.uninitialized_single_output(1, "Output");
      inputs.materialize_to_uninitialized(mask, outputs.data());
      break;
    }
    case MFDataType::Vector: {
      const GVVectorArray &inputs = params.readonly_vector_input(0, "Input");
      GVectorArray &outputs = params.vector_output(1, "Output");
      outputs.extend(mask, inputs);
      break;
    }
  }
}

}  // namespace blender::fn
