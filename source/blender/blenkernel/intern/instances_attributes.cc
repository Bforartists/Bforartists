/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_attribute_legacy_convert.hh"
#include "BKE_instances.hh"

#include "attribute_access_intern.hh"
#include "attribute_storage_access.hh"

namespace blender::bke {

static void tag_component_reference_index_changed(void *owner)
{
  Instances &instances = *static_cast<Instances *>(owner);
  instances.tag_reference_handles_changed();
}

static const auto &changed_tags()
{
  static Map<StringRef, AttrUpdateOnChange> attributes{
      {".reference_index", tag_component_reference_index_changed},
  };
  return attributes;
}

static const auto &builtin_attributes()
{
  static auto attributes = []() {
    Map<StringRef, AttrBuiltinInfo> map;

    /**
     * IDs of the instances. They are used for consistency over multiple frames for things like
     * motion blur. Proper stable ID data that actually helps when rendering can only be generated
     * in some situations, so this vector is allowed to be empty, in which case the index of each
     * instance will be used for the final ID.
     */
    AttrBuiltinInfo id(bke::AttrDomain::Instance, bke::AttrType::Int32);
    map.add_new("id", std::move(id));

    AttrBuiltinInfo instance_transform(bke::AttrDomain::Instance, bke::AttrType::Float4x4);
    instance_transform.deletable = false;
    map.add_new("instance_transform", std::move(instance_transform));

    /** Indices into `Instances::references_`. Determines what data is instanced. */
    AttrBuiltinInfo reference_index(bke::AttrDomain::Instance, bke::AttrType::Int32);
    reference_index.deletable = false;
    map.add_new(".reference_index", std::move(reference_index));

    return map;
  }();
  return attributes;
}

static constexpr AttributeAccessorFunctions get_instances_accessor_functions()
{
  AttributeAccessorFunctions fn{};
  fn.domain_supported = [](const void * /*owner*/, const AttrDomain domain) {
    return domain == AttrDomain::Instance;
  };
  fn.domain_size = [](const void *owner, const AttrDomain domain) {
    return domain == AttrDomain::Instance ?
               static_cast<const Instances *>(owner)->instances_num() :
               0;
  };
  fn.builtin_domain_and_type = [](const void * /*owner*/,
                                  const StringRef name) -> std::optional<AttributeDomainAndType> {
    const AttrBuiltinInfo *info = builtin_attributes().lookup_ptr(name);
    if (!info) {
      return std::nullopt;
    }
    const std::optional<eCustomDataType> cd_type = attr_type_to_custom_data_type(info->type);
    BLI_assert(cd_type.has_value());
    return AttributeDomainAndType{info->domain, *cd_type};
  };
  fn.get_builtin_default = [](const void * /*owner*/, StringRef name) -> GPointer {
    const AttrBuiltinInfo &info = builtin_attributes().lookup(name);
    return info.default_value;
  };
  fn.lookup = [](const void *owner, const StringRef name) -> GAttributeReader {
    const Instances &instances = *static_cast<const Instances *>(owner);
    const AttributeStorage &storage = instances.attribute_storage();
    const Attribute *attribute = storage.lookup(name);
    if (!attribute) {
      return {};
    }
    return attribute_to_reader(*attribute, AttrDomain::Instance, instances.instances_num());
  };
  fn.adapt_domain = [](const void * /*owner*/,
                       const GVArray &varray,
                       const AttrDomain from_domain,
                       const AttrDomain to_domain) {
    if (from_domain == to_domain && from_domain == AttrDomain::Instance) {
      return varray;
    }
    return GVArray{};
  };
  fn.foreach_attribute = [](const void *owner,
                            const FunctionRef<void(const AttributeIter &)> fn,
                            const AttributeAccessor &accessor) {
    const Instances &instances = *static_cast<const Instances *>(owner);
    const AttributeStorage &storage = instances.attribute_storage();
    storage.foreach_with_stop([&](const Attribute &attribute) {
      const auto get_fn = [&]() {
        return attribute_to_reader(attribute, AttrDomain::Instance, instances.instances_num());
      };
      const std::optional<eCustomDataType> cd_type = attr_type_to_custom_data_type(
          attribute.data_type());
      BLI_assert(cd_type.has_value());
      AttributeIter iter(attribute.name(), attribute.domain(), *cd_type, get_fn);
      iter.is_builtin = builtin_attributes().contains(attribute.name());
      iter.accessor = &accessor;
      fn(iter);
      return !iter.is_stopped();
    });
  };
  fn.lookup_validator = [](const void * /*owner*/, const StringRef name) -> AttributeValidator {
    const AttrBuiltinInfo *info = builtin_attributes().lookup_ptr(name);
    if (!info) {
      return {};
    }
    return info->validator;
  };
  fn.lookup_for_write = [](void *owner, const StringRef name) -> GAttributeWriter {
    Instances &instances = *static_cast<Instances *>(owner);
    AttributeStorage &storage = instances.attribute_storage();
    Attribute *attribute = storage.lookup(name);
    if (!attribute) {
      return {};
    }
    return attribute_to_writer(&instances, changed_tags(), instances.instances_num(), *attribute);
  };
  fn.remove = [](void *owner, const StringRef name) -> bool {
    Instances &instances = *static_cast<Instances *>(owner);
    AttributeStorage &storage = instances.attribute_storage();
    if (const AttrBuiltinInfo *info = builtin_attributes().lookup_ptr(name)) {
      if (!info->deletable) {
        return false;
      }
    }
    const std::optional<AttrUpdateOnChange> fn = changed_tags().lookup_try(name);
    const bool removed = storage.remove(name);
    if (!removed) {
      return false;
    }
    if (fn) {
      (*fn)(owner);
    }
    return true;
  };
  fn.add = [](void *owner,
              const StringRef name,
              const AttrDomain domain,
              const eCustomDataType data_type,
              const AttributeInit &initializer) {
    Instances &instances = *static_cast<Instances *>(owner);
    const int domain_size = instances.instances_num();
    AttributeStorage &storage = instances.attribute_storage();
    const std::optional<AttrType> type = custom_data_type_to_attr_type(data_type);
    BLI_assert(type.has_value());
    if (const AttrBuiltinInfo *info = builtin_attributes().lookup_ptr(name)) {
      if (info->domain != domain || info->type != type) {
        return false;
      }
    }
    if (storage.lookup(name)) {
      return false;
    }
    Attribute::DataVariant data = attribute_init_to_data(*type, domain_size, initializer);
    storage.add(name, domain, *type, std::move(data));
    return true;
  };

  return fn;
}

const AttributeAccessorFunctions &instance_attribute_accessor_functions()
{
  static const AttributeAccessorFunctions fn = get_instances_accessor_functions();
  return fn;
}

}  // namespace blender::bke
