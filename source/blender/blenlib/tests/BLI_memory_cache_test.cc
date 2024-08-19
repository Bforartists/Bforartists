/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: Apache-2.0 */

#include "BLI_hash.hh"
#include "BLI_memory_cache.hh"
#include "BLI_memory_counter.hh"

#include "testing/testing.h"

#include "BLI_strict_flags.h" /* Keep last. */

namespace blender::memory_cache::tests {

class GenericIntKey : public GenericKey {
 private:
  int value_;

 public:
  GenericIntKey(int value) : value_(value) {}

  uint64_t hash() const override
  {
    return get_default_hash(value_);
  }

  bool equal_to(const GenericKey &other) const override
  {
    if (const auto *other_typed = dynamic_cast<const GenericIntKey *>(&other)) {
      return other_typed->value_ == value_;
    }
    return false;
  }

  std::unique_ptr<GenericKey> to_storable() const override
  {
    return std::make_unique<GenericIntKey>(*this);
  }
};

class CachedInt : public memory_cache::CachedValue {
 public:
  int value;

  CachedInt(int initial_value) : value(initial_value) {}

  void count_memory(MemoryCounter &memory) const override
  {
    memory.add(sizeof(int));
  }
};

TEST(memory_cache, Simple)
{
  memory_cache::clear();
  {
    bool newly_computed = false;
    EXPECT_EQ(4, memory_cache::get<CachedInt>(GenericIntKey(0), [&]() {
                   newly_computed = true;
                   return std::make_unique<CachedInt>(4);
                 })->value);
    EXPECT_TRUE(newly_computed);
  }
  {
    bool newly_computed = false;
    EXPECT_EQ(4, memory_cache::get<CachedInt>(GenericIntKey(0), [&]() {
                   newly_computed = true;
                   return std::make_unique<CachedInt>(4);
                 })->value);
    EXPECT_FALSE(newly_computed);
  }
  memory_cache::clear();
  {
    bool newly_computed = false;
    EXPECT_EQ(4, memory_cache::get<CachedInt>(GenericIntKey(0), [&]() {
                   newly_computed = true;
                   return std::make_unique<CachedInt>(4);
                 })->value);
    EXPECT_TRUE(newly_computed);
  }
}

}  // namespace blender::memory_cache::tests
