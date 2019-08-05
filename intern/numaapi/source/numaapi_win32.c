// Copyright (c) 2016, libnumaapi authors
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.
//
// Author: Sergey Sharybin (sergey.vfx@gmail.com)

#include "build_config.h"

#if OS_WIN

#include "numaapi.h"

#ifndef NOGDI
#  define NOGDI
#endif
#ifndef NOMINMAX
#  define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#  define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOCOMM
#  define NOCOMM
#endif

#include <stdlib.h>
#include <stdint.h>
#include <windows.h>

#if ARCH_CPU_64_BITS
#  include <VersionHelpers.h>
#endif

////////////////////////////////////////////////////////////////////////////////
// Initialization.

// Kernel library, from where the symbols come.
static HMODULE kernel_lib;

// Types of all symbols which are read from the library.

// NUMA function types.
typedef BOOL t_GetNumaHighestNodeNumber(PULONG highest_node_number);
typedef BOOL t_GetNumaNodeProcessorMask(UCHAR node, ULONGLONG* processor_mask);
typedef BOOL t_GetNumaNodeProcessorMaskEx(USHORT node,
                                          GROUP_AFFINITY* processor_mask);
typedef BOOL t_GetNumaProcessorNode(UCHAR processor, UCHAR* node_number);
typedef void* t_VirtualAllocExNuma(HANDLE process_handle,
                                   LPVOID address,
                                   SIZE_T size,
                                   DWORD  allocation_type,
                                   DWORD  protect,
                                   DWORD  preferred);
typedef BOOL t_VirtualFree(void* address, SIZE_T size, DWORD free_type);
// Threading function types.
typedef BOOL t_SetProcessAffinityMask(HANDLE process_handle,
                                      DWORD_PTR process_affinity_mask);
typedef BOOL t_SetThreadGroupAffinity(HANDLE thread_handle,
                                      const GROUP_AFFINITY* group_affinity,
                                      GROUP_AFFINITY* PreviousGroupAffinity);
typedef BOOL t_GetThreadGroupAffinity(HANDLE thread_handle,
                                      GROUP_AFFINITY* group_affinity);
typedef DWORD t_GetCurrentProcessorNumber(void);
typedef void t_GetCurrentProcessorNumberEx(PROCESSOR_NUMBER* proc_number);
typedef DWORD t_GetActiveProcessorCount(WORD group_number);


// NUMA symbols.
static t_GetNumaHighestNodeNumber* _GetNumaHighestNodeNumber;
static t_GetNumaNodeProcessorMask* _GetNumaNodeProcessorMask;
static t_GetNumaNodeProcessorMaskEx* _GetNumaNodeProcessorMaskEx;
static t_GetNumaProcessorNode* _GetNumaProcessorNode;
static t_VirtualAllocExNuma* _VirtualAllocExNuma;
static t_VirtualFree* _VirtualFree;
// Threading symbols.
static t_SetProcessAffinityMask* _SetProcessAffinityMask;
static t_SetThreadGroupAffinity* _SetThreadGroupAffinity;
static t_GetThreadGroupAffinity* _GetThreadGroupAffinity;
static t_GetCurrentProcessorNumber* _GetCurrentProcessorNumber;
static t_GetCurrentProcessorNumberEx* _GetCurrentProcessorNumberEx;
static t_GetActiveProcessorCount* _GetActiveProcessorCount;

static void numaExit(void) {
  // TODO(sergey): Consider closing library here.
}

static NUMAAPI_Result loadNumaSymbols(void) {
  // Prevent multiple initializations.
  static bool initialized = false;
  static NUMAAPI_Result result = NUMAAPI_NOT_AVAILABLE;
  if (initialized) {
    return result;
  }
  initialized = true;
  // Register de-initialization.
  const int error = atexit(numaExit);
  if (error) {
    result = NUMAAPI_ERROR_ATEXIT;
    return result;
  }
  // Load library.
  kernel_lib = LoadLibraryA("Kernel32.dll");
  // Load symbols.

#define _LIBRARY_FIND(lib, name)                   \
  do {                                             \
    _##name = (t_##name *)GetProcAddress(lib, #name);  \
  } while (0)
#define KERNEL_LIBRARY_FIND(name) _LIBRARY_FIND(kernel_lib, name)

  // NUMA.
  KERNEL_LIBRARY_FIND(GetNumaHighestNodeNumber);
  KERNEL_LIBRARY_FIND(GetNumaNodeProcessorMask);
  KERNEL_LIBRARY_FIND(GetNumaNodeProcessorMaskEx);
  KERNEL_LIBRARY_FIND(GetNumaProcessorNode);
  KERNEL_LIBRARY_FIND(VirtualAllocExNuma);
  KERNEL_LIBRARY_FIND(VirtualFree);
  // Threading.
  KERNEL_LIBRARY_FIND(SetProcessAffinityMask);
  KERNEL_LIBRARY_FIND(SetThreadGroupAffinity);
  KERNEL_LIBRARY_FIND(GetThreadGroupAffinity);
  KERNEL_LIBRARY_FIND(GetCurrentProcessorNumber);
  KERNEL_LIBRARY_FIND(GetCurrentProcessorNumberEx);
  KERNEL_LIBRARY_FIND(GetActiveProcessorCount);

#undef KERNEL_LIBRARY_FIND
#undef _LIBRARY_FIND

  result = NUMAAPI_SUCCESS;
  return result;
}

NUMAAPI_Result numaAPI_Initialize(void) {
#if !ARCH_CPU_64_BITS
  // No NUMA on 32 bit platforms.
  return NUMAAPI_NOT_AVAILABLE;
#else
  if (!IsWindows7OrGreater()) {
    // Require Windows 7 or higher.
    NUMAAPI_NOT_AVAILABLE;
  }
  loadNumaSymbols();
  return NUMAAPI_SUCCESS;
#endif
}

////////////////////////////////////////////////////////////////////////////////
// Internal helpers.

static int countNumSetBits(ULONGLONG mask) {
  // TODO(sergey): There might be faster way calculating number of set bits.
  // NOTE: mask must be unsigned, there is undefined behavior for signed ints.
  int num_bits = 0;
  while (mask != 0) {
    num_bits += (mask & 1);
    mask = (mask >> 1);
  }
  return num_bits;
}

////////////////////////////////////////////////////////////////////////////////
// Topology query.

int numaAPI_GetNumNodes(void) {
  ULONG highest_node_number;
  if (!_GetNumaHighestNodeNumber(&highest_node_number)) {
    return 0;
  }
  // TODO(sergey): Resolve the type narrowing.
  // NOTE: This is not necessarily a total amount of nodes in the system.
  return (int)highest_node_number + 1;
}

bool numaAPI_IsNodeAvailable(int node) {
  // Trick to detect whether the node is usable or not: check whether
  // there are any processors associated with it.
  //
  // This is needed because numaApiGetNumNodes() is not guaranteed to
  // give total amount of nodes and some nodes might be unavailable.
  GROUP_AFFINITY processor_mask = { 0 };
  if (!_GetNumaNodeProcessorMaskEx(node, &processor_mask)) {
    return false;
  }
  if (processor_mask.Mask == 0) {
    return false;
  }
  return true;
}

int numaAPI_GetNumNodeProcessors(int node) {
  GROUP_AFFINITY processor_mask = { 0 };
  if (!_GetNumaNodeProcessorMaskEx(node, &processor_mask)) {
    return 0;
  }
  return countNumSetBits(processor_mask.Mask);
}

////////////////////////////////////////////////////////////////////////////////
// Topology helpers.

int numaAPI_GetNumCurrentNodesProcessors(void) {
  HANDLE thread_handle = GetCurrentThread();
  GROUP_AFFINITY group_affinity;
  // TODO(sergey): Needs implementation.
  if (!_GetThreadGroupAffinity(thread_handle, &group_affinity)) {
    return 0;
  }
  // First, count number of possible bits in the affinity mask.
  const int num_processors = countNumSetBits(group_affinity.Mask);
  // Then check that it's not exceeding number of processors in tjhe group.
  const int num_group_processors =
      _GetActiveProcessorCount(group_affinity.Group);
  if (num_group_processors < num_processors) {
    return num_group_processors;
  }
  return num_processors;
}

////////////////////////////////////////////////////////////////////////////////
// Affinities.

bool numaAPI_RunProcessOnNode(int node) {
  // TODO(sergey): Make sure requested node is within active CPU group.
  // Change affinity of the proces to make it to run on a given node.
  HANDLE process_handle = GetCurrentProcess();
  GROUP_AFFINITY processor_mask = { 0 };
  if (_GetNumaNodeProcessorMaskEx(node, &processor_mask) == 0) {
    return false;
  }
  // TODO: Affinity should respect processor group.
  if (_SetProcessAffinityMask(process_handle, processor_mask.Mask) == 0) {
    return false;
  }
  return true;
}

bool numaAPI_RunThreadOnNode(int node) {
  HANDLE thread_handle = GetCurrentThread();
  GROUP_AFFINITY group_affinity = { 0 };
  if (_GetNumaNodeProcessorMaskEx(node, &group_affinity) == 0) {
    return false;
  }
  if (_SetThreadGroupAffinity(thread_handle, &group_affinity, NULL) == 0) {
    return false;
  }
  return true;
}

////////////////////////////////////////////////////////////////////////////////
// Memory management.

void* numaAPI_AllocateOnNode(size_t size, int node) {
  return _VirtualAllocExNuma(GetCurrentProcess(),
                             NULL,
                             size,
                             MEM_RESERVE | MEM_COMMIT,
                             PAGE_READWRITE,
                             node);
}

void* numaAPI_AllocateLocal(size_t size) {
  UCHAR current_processor = (UCHAR)_GetCurrentProcessorNumber();
  UCHAR node;
  if (!_GetNumaProcessorNode(current_processor, &node)) {
    return NULL;
  }
  return numaAPI_AllocateOnNode(size, node);
}

void numaAPI_Free(void* start, size_t size) {
  if (!_VirtualFree(start, size, MEM_RELEASE)) {
    // TODO(sergey): Throw an error!
  }
}

#endif  // OS_WIN
