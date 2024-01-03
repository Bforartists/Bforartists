/* SPDX-FileCopyrightText: 2020-2021 Contributors to the OpenVDB Project
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This is an extract from NanoVDB.h, with minimal code needed for kernel side access to grids. The
 * original headers are not compatible with Metal due to missing address space qualifiers. */

#pragma once

CCL_NAMESPACE_BEGIN

#define NANOVDB_USE_SINGLE_ROOT_KEY
#define NANOVDB_DATA_ALIGNMENT 32

namespace nanovdb {

/* Utilities */

template<typename DstT, typename SrcT>
ccl_device ccl_global const DstT *PtrAdd(ccl_global const SrcT *p, int64_t offset)
{
  return reinterpret_cast<ccl_global const DstT *>(reinterpret_cast<ccl_global const char *>(p) +
                                                   offset);
}

/* Coord */

struct Coord {
  int x, y, z;

  ccl_device_inline_method explicit Coord(int32_t n) : x(n), y(n), z(n) {}
  ccl_device_inline_method Coord(int32_t x, int32_t y, int32_t z) : x(x), y(y), z(z) {}

  ccl_device_inline_method Coord operator&(int32_t n) const
  {
    return Coord(x & n, y & n, z & n);
  }
};

/* Mask */

template<uint32_t LOG2DIM> struct Mask {
  ccl_static_constexpr uint32_t SIZE = 1U << (3 * LOG2DIM);
  ccl_static_constexpr uint32_t WORD_COUNT = SIZE >> 6;
  uint64_t mWords[WORD_COUNT];

  ccl_device_inline_method bool isOff(uint32_t n) const ccl_global
  {
    return 0 == (mWords[n >> 6] & (uint64_t(1) << (n & 63)));
  }
};

/* Grid */

template<typename TreeT> struct alignas(NANOVDB_DATA_ALIGNMENT) Grid {
  ccl_static_constexpr int MaxNameSize = 256;
  uint64_t mMagic;
  uint64_t mChecksum;
  uint32_t mVersion;
  uint32_t mFlags;
  uint32_t mGridIndex;
  uint32_t mGridCount;
  uint64_t mGridSize;
  char mGridName[MaxNameSize];
  uint8_t mMap[264];
  uint8_t mWorldBBox[48];  // double[6], but no doubles in Metal
  uint8_t mVoxelSize[24];  // double[3], but no doubles in Metal
  uint32_t mGridClass;
  uint32_t mGridType;
  uint32_t mData0;
  uint64_t mData1, mData2;

  using BuildType = typename TreeT::BuildType;

  ccl_device_inline_method ccl_global const TreeT &tree() const ccl_global
  {
    return *reinterpret_cast<ccl_global const TreeT *>(this + 1);
  }
};

/* Tree */

template<typename RootT> struct alignas(NANOVDB_DATA_ALIGNMENT) Tree {
  int64_t mNodeOffset[4];
  uint32_t mNodeCount[3];
  uint32_t mTileCount[3];
  uint64_t mVoxelCount;

  using ValueType = typename RootT::ValueType;
  using BuildType = typename RootT::BuildType;

  ccl_device_inline_method ccl_global const RootT &root() const ccl_global
  {
    return *reinterpret_cast<ccl_global const RootT *>(
        mNodeOffset[3] ? PtrAdd<uint8_t>(this, mNodeOffset[3]) : nullptr);
  }
};

/* RootNode */

template<typename ChildT> struct alignas(NANOVDB_DATA_ALIGNMENT) RootNode {
  using ValueType = typename ChildT::ValueType;
  using BuildType = typename ChildT::BuildType;

#ifdef NANOVDB_USE_SINGLE_ROOT_KEY
  using KeyT = uint64_t;
  ccl_device_inline_method static uint64_t CoordToKey(const Coord ijk)
  {
    return (uint64_t(uint32_t(ijk.z) >> ChildT::TOTAL)) |
           (uint64_t(uint32_t(ijk.y) >> ChildT::TOTAL) << 21) |
           (uint64_t(uint32_t(ijk.x) >> ChildT::TOTAL) << 42);
  }
#else
  using KeyT = Coord;
  ccl_device_inline_method static Coord CoordToKey(const CoordT ijk)
  {
    return ijk & ~ChildT::MASK;
  }
#endif
  Coord mBBox[2];
  uint32_t mTableSize;

  ValueType mBackground;
  ValueType mMinimum;
  ValueType mMaximum;
  float mAverage;
  float mStdDevi;

  struct alignas(NANOVDB_DATA_ALIGNMENT) Tile {
    KeyT key;
    int64_t child;
    uint32_t state;
    ValueType value;
  };

  ccl_device_inline_method ccl_global const Tile *probeTile(const Coord ijk) const ccl_global
  {
    const auto key = CoordToKey(ijk);
    ccl_global const Tile *p = reinterpret_cast<ccl_global const Tile *>(this + 1);
    ccl_global const Tile *q = p + mTableSize;
    for (; p < q; ++p) {
      if (p->key == key) {
        return p;
      }
    }
    return nullptr;
  }

  ccl_device_inline_method ccl_global const ChildT *getChild(ccl_global const Tile *tile) const
      ccl_global
  {
    return PtrAdd<ChildT>(this, tile->child);
  }

  ccl_static_constexpr uint32_t LEVEL = 1 + ChildT::LEVEL;
};

/* InternalNode */

template<typename ChildT, uint32_t Log2Dim = ChildT::LOG2DIM + 1>
struct alignas(NANOVDB_DATA_ALIGNMENT) InternalNode {
  using ValueType = typename ChildT::ValueType;
  using BuildType = typename ChildT::BuildType;

  union Tile {
    ValueType value;
    int64_t child;
  };

  Coord mBBox[2];
  uint64_t mFlags;
  Mask<Log2Dim> mValueMask;
  Mask<Log2Dim> mChildMask;

  ValueType mMinimum;
  ValueType mMaximum;
  float mAverage;
  float mStdDevi;

  alignas(32) Tile mTable[1u << (3 * Log2Dim)];

  ccl_device_inline_method ccl_global const ChildT *getChild(uint32_t n) const ccl_global
  {
    return PtrAdd<ChildT>(this, mTable[n].child);
  }

  ccl_static_constexpr uint32_t LOG2DIM = Log2Dim;
  ccl_static_constexpr uint32_t TOTAL = LOG2DIM + ChildT::TOTAL;
  ccl_static_constexpr uint32_t DIM = 1u << TOTAL;
  ccl_static_constexpr uint32_t SIZE = 1u << (3 * LOG2DIM);
  ccl_static_constexpr uint32_t MASK = (1u << TOTAL) - 1u;
  ccl_static_constexpr uint32_t LEVEL = 1 + ChildT::LEVEL;

  ccl_device_inline_method static uint32_t CoordToOffset(const Coord ijk)
  {
    return (((ijk.x & MASK) >> ChildT::TOTAL) << (2 * LOG2DIM)) |
           (((ijk.y & MASK) >> ChildT::TOTAL) << (LOG2DIM)) | ((ijk.z & MASK) >> ChildT::TOTAL);
  }
};

/* LeafData */

template<typename ValueT, uint32_t LOG2DIM> struct alignas(NANOVDB_DATA_ALIGNMENT) LeafData {
  using ValueType = ValueT;
  using BuildType = ValueT;

  Coord mBBoxMin;
  uint8_t mBBoxDif[3];
  uint8_t mFlags;
  Mask<LOG2DIM> mValueMask;

  ValueType mMinimum;
  ValueType mMaximum;
  float mAverage;
  float mStdDevi;
  alignas(32) ValueType mValues[1u << 3 * LOG2DIM];

  ccl_device_inline_method ValueType getValue(uint32_t i) const ccl_global
  {
    return mValues[i];
  }
};

/* LeafFnBase */

template<uint32_t LOG2DIM> struct alignas(NANOVDB_DATA_ALIGNMENT) LeafFnBase {
  Coord mBBoxMin;
  uint8_t mBBoxDif[3];
  uint8_t mFlags;
  Mask<LOG2DIM> mValueMask;

  float mMinimum;
  float mQuantum;
  uint16_t mMin, mMax, mAvg, mDev;
};

/* LeafData<Fp16> */

class Fp16 {};

template<uint32_t LOG2DIM> struct alignas(NANOVDB_DATA_ALIGNMENT) LeafData<Fp16, LOG2DIM> {
  using ValueType = float;
  using BuildType = Fp16;

  LeafFnBase<LOG2DIM> base;
  alignas(32) uint16_t mCode[1u << 3 * LOG2DIM];

  ccl_device_inline_method float getValue(uint32_t i) const ccl_global
  {
    return mCode[i] * base.mQuantum + base.mMinimum;
  }
};

/* LeafData<FpN> */

class FpN {};

template<uint32_t LOG2DIM> struct alignas(NANOVDB_DATA_ALIGNMENT) LeafData<FpN, LOG2DIM> {
  using ValueType = float;
  using BuildType = FpN;

  LeafFnBase<LOG2DIM> base;

  ccl_device_inline_method float getValue(uint32_t i) const ccl_global
  {
    const int b = base.mFlags >> 5;
    uint32_t code = reinterpret_cast<ccl_global const uint32_t *>(this + 1)[i >> (5 - b)];
    code >>= (i & ((32 >> b) - 1)) << b;
    code &= (1 << (1 << b)) - 1;
    return float(code) * base.mQuantum + base.mMinimum;
  }
};

/* LeafNode */

template<typename BuildT, uint32_t Log2Dim = 3> struct alignas(NANOVDB_DATA_ALIGNMENT) LeafNode {
  using DataType = LeafData<BuildT, Log2Dim>;
  using ValueType = typename DataType::ValueType;
  using BuildType = typename DataType::BuildType;

  DataType data;

  ccl_static_constexpr uint32_t LOG2DIM = Log2Dim;
  ccl_static_constexpr uint32_t TOTAL = LOG2DIM;
  ccl_static_constexpr uint32_t DIM = 1u << TOTAL;
  ccl_static_constexpr uint32_t SIZE = 1u << 3 * LOG2DIM;
  ccl_static_constexpr uint32_t MASK = (1u << LOG2DIM) - 1u;
  ccl_static_constexpr uint32_t LEVEL = 0;

  ccl_device_inline_method static uint32_t CoordToOffset(const Coord ijk)
  {
    return ((ijk.x & MASK) << (2 * LOG2DIM)) | ((ijk.y & MASK) << LOG2DIM) | (ijk.z & MASK);
  }

  ccl_device_inline_method ValueType getValue(uint32_t offset) const ccl_global
  {
    return data.getValue(offset);
  }

  ccl_device_inline_method ValueType getValue(const Coord ijk) const ccl_global
  {
    return getValue(CoordToOffset(ijk));
  }
};

/* Template Specializations */

template<typename BuildT> using NanoLeaf = LeafNode<BuildT, 3>;
template<typename BuildT> using NanoLower = InternalNode<NanoLeaf<BuildT>, 4>;
template<typename BuildT> using NanoUpper = InternalNode<NanoLower<BuildT>, 5>;
template<typename BuildT> using NanoRoot = RootNode<NanoUpper<BuildT>>;
template<typename BuildT> using NanoTree = Tree<NanoRoot<BuildT>>;
template<typename BuildT> using NanoGrid = Grid<NanoTree<BuildT>>;

/* ReadAccessor */

template<typename BuildT> class ReadAccessor {
  using RootT = NanoRoot<BuildT>;
  using LeafT = NanoLeaf<BuildT>;

  mutable ccl_global const RootT *mRoot;

 public:
  using ValueType = typename RootT::ValueType;

  ccl_device_inline_method ReadAccessor(ccl_global const RootT &root) : mRoot(&root) {}

  ccl_device_inline_method ValueType getValue(const Coord ijk) const
  {
    ccl_global const auto *tile = mRoot->probeTile(ijk);
    if (tile == nullptr) {
      return mRoot->mBackground;
    }
    if (tile->child == 0) {
      return tile->value;
    }

    ccl_global const auto *upper = mRoot->getChild(tile);
    const uint32_t upper_n = upper->CoordToOffset(ijk);
    if (upper->mChildMask.isOff(upper_n)) {
      return upper->mTable[upper_n].value;
    }

    ccl_global const auto *lower = upper->getChild(upper_n);
    const uint32_t lower_n = lower->CoordToOffset(ijk);
    if (lower->mChildMask.isOff(lower_n)) {
      return lower->mTable[lower_n].value;
    }

    ccl_global const LeafT *leaf = lower->getChild(lower_n);
    return leaf->getValue(ijk);
  }
};

template<typename BuildT> class CachedReadAccessor {
  using RootT = NanoRoot<BuildT>;
  using UpperT = NanoUpper<BuildT>;
  using LowerT = NanoLower<BuildT>;
  using LeafT = NanoLeaf<BuildT>;

  mutable Coord mKeys[3];
  mutable ccl_global const RootT *mRoot;
  mutable ccl_global const void *mNode[3];

 public:
  using ValueType = typename RootT::ValueType;

  ccl_device_inline_method CachedReadAccessor(ccl_global const RootT &root)
      : mKeys{Coord(INT_MAX), Coord(INT_MAX), Coord(INT_MAX)},
        mRoot(&root),
        mNode{nullptr, nullptr, nullptr}
  {
  }

  template<typename NodeT> ccl_device_inline_method bool isCached(const Coord ijk) const
  {
    return (ijk.x & int32_t(~NodeT::MASK)) == mKeys[NodeT::LEVEL].x &&
           (ijk.y & int32_t(~NodeT::MASK)) == mKeys[NodeT::LEVEL].y &&
           (ijk.z & int32_t(~NodeT::MASK)) == mKeys[NodeT::LEVEL].z;
  }

  ccl_device_inline_method ValueType getValueAndCache(ccl_global const RootT &node,
                                                      const Coord ijk) const
  {
    if (ccl_global const auto *tile = node.probeTile(ijk)) {
      if (tile->child != 0) {
        ccl_global const auto *child = node.getChild(tile);
        insert(ijk, child);
        return getValueAndCache(*child, ijk);
      }
      return tile->value;
    }
    return node.mBackground;
  }

  ccl_device_inline_method ValueType getValueAndCache(ccl_global const LeafT &node,
                                                      const Coord ijk) const
  {
    return node.getValue(ijk);
  }

  template<typename NodeT>
  ccl_device_inline_method ValueType getValueAndCache(ccl_global const NodeT &node,
                                                      const Coord ijk) const
  {
    const uint32_t n = node.CoordToOffset(ijk);
    if (node.mChildMask.isOff(n)) {
      return node.mTable[n].value;
    }
    ccl_global const auto *child = node.getChild(n);
    insert(ijk, child);
    return getValueAndCache(*child, ijk);
  }

  ccl_device_inline_method ValueType getValue(const Coord ijk) const
  {
    if (isCached<LeafT>(ijk)) {
      return getValueAndCache(*((ccl_global const LeafT *)mNode[0]), ijk);
    }
    else if (isCached<LowerT>(ijk)) {
      return getValueAndCache(*((ccl_global const LowerT *)mNode[1]), ijk);
    }
    else if (isCached<UpperT>(ijk)) {
      return getValueAndCache(*((ccl_global const UpperT *)mNode[2]), ijk);
    }
    return getValueAndCache(*mRoot, ijk);
  }

  template<typename NodeT>
  ccl_device_inline_method void insert(const Coord ijk, ccl_global const NodeT *node) const
  {
    mKeys[NodeT::LEVEL] = ijk & ~NodeT::MASK;
    mNode[NodeT::LEVEL] = node;
  }
};

}  // namespace nanovdb

CCL_NAMESPACE_END
