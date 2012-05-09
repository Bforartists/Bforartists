// Ceres Solver - A fast non-linear least squares minimizer
// Copyright 2010, 2011, 2012 Google Inc. All rights reserved.
// http://code.google.com/p/ceres-solver/
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// * Redistributions of source code must retain the above copyright notice,
//   this list of conditions and the following disclaimer.
// * Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
// * Neither the name of Google Inc. nor the names of its contributors may be
//   used to endorse or promote products derived from this software without
//   specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//
// Author: keir@google.com (Keir Mierle)
//
// Computation of the Jacobian matrix for vector-valued functions of multiple
// variables, using automatic differentiation based on the implementation of
// dual numbers in jet.h. Before reading the rest of this file, it is adivsable
// to read jet.h's header comment in detail.
//
// The helper wrapper AutoDiff::Differentiate() computes the jacobian of
// functors with templated operator() taking this form:
//
//   struct F {
//     template<typename T>
//     bool operator(const T *x, const T *y, ..., T *z) {
//       // Compute z[] based on x[], y[], ...
//       // return true if computation succeeded, false otherwise.
//     }
//   };
//
// All inputs and outputs may be vector-valued.
//
// To understand how jets are used to compute the jacobian, a
// picture may help. Consider a vector-valued function, F, returning 3
// dimensions and taking a vector-valued parameter of 4 dimensions:
//
//     y            x
//   [ * ]    F   [ * ]
//   [ * ]  <---  [ * ]
//   [ * ]        [ * ]
//                [ * ]
//
// Similar to the 2-parameter example for f described in jet.h, computing the
// jacobian dy/dx is done by substutiting a suitable jet object for x and all
// intermediate steps of the computation of F. Since x is has 4 dimensions, use
// a Jet<double, 4>.
//
// Before substituting a jet object for x, the dual components are set
// appropriately for each dimension of x:
//
//          y                       x
//   [ * | * * * * ]    f   [ * | 1 0 0 0 ]   x0
//   [ * | * * * * ]  <---  [ * | 0 1 0 0 ]   x1
//   [ * | * * * * ]        [ * | 0 0 1 0 ]   x2
//         ---+---          [ * | 0 0 0 1 ]   x3
//            |                   ^ ^ ^ ^
//          dy/dx                 | | | +----- infinitesimal for x3
//                                | | +------- infinitesimal for x2
//                                | +--------- infinitesimal for x1
//                                +----------- infinitesimal for x0
//
// The reason to set the internal 4x4 submatrix to the identity is that we wish
// to take the derivative of y separately with respect to each dimension of x.
// Each column of the 4x4 identity is therefore for a single component of the
// independent variable x.
//
// Then the jacobian of the mapping, dy/dx, is the 3x4 sub-matrix of the
// extended y vector, indicated in the above diagram.
//
// Functors with multiple parameters
// ---------------------------------
// In practice, it is often convenient to use a function f of two or more
// vector-valued parameters, for example, x[3] and z[6]. Unfortunately, the jet
// framework is designed for a single-parameter vector-valued input. The wrapper
// in this file addresses this issue adding support for functions with one or
// more parameter vectors.
//
// To support multiple parameters, all the parameter vectors are concatenated
// into one and treated as a single parameter vector, except that since the
// functor expects different inputs, we need to construct the jets as if they
// were part of a single parameter vector. The extended jets are passed
// separately for each parameter.
//
// For example, consider a functor F taking two vector parameters, p[2] and
// q[3], and producing an output y[4]:
//
//   struct F {
//     template<typename T>
//     bool operator(const T *p, const T *q, T *z) {
//       // ...
//     }
//   };
//
// In this case, the necessary jet type is Jet<double, 5>. Here is a
// visualization of the jet objects in this case:
//
//          Dual components for p ----+
//                                    |
//                                   -+-
//           y                 [ * | 1 0 | 0 0 0 ]    --- p[0]
//                             [ * | 0 1 | 0 0 0 ]    --- p[1]
//   [ * | . . | + + + ]         |
//   [ * | . . | + + + ]         v
//   [ * | . . | + + + ]  <--- F(p, q)
//   [ * | . . | + + + ]            ^
//         ^^^   ^^^^^              |
//        dy/dp  dy/dq            [ * | 0 0 | 1 0 0 ] --- q[0]
//                                [ * | 0 0 | 0 1 0 ] --- q[1]
//                                [ * | 0 0 | 0 0 1 ] --- q[2]
//                                            --+--
//                                              |
//          Dual components for q --------------+
//
// where the 4x2 submatrix (marked with ".") and 4x3 submatrix (marked with "+"
// of y in the above diagram are the derivatives of y with respect to p and q
// respectively. This is how autodiff works for functors taking multiple vector
// valued arguments (up to 6).
//
// Jacobian NULL pointers
// ----------------------
// In general, the functions below will accept NULL pointers for all or some of
// the Jacobian parameters, meaning that those Jacobians will not be computed.

#ifndef CERES_PUBLIC_INTERNAL_AUTODIFF_H_
#define CERES_PUBLIC_INTERNAL_AUTODIFF_H_

#include <stddef.h>

#include <glog/logging.h>
#include "ceres/jet.h"
#include "ceres/internal/fixed_array.h"

namespace ceres {
namespace internal {

// Extends src by a 1st order pertubation for every dimension and puts it in
// dst. The size of src is N. Since this is also used for perturbations in
// blocked arrays, offset is used to shift which part of the jet the
// perturbation occurs. This is used to set up the extended x augmented by an
// identity matrix. The JetT type should be a Jet type, and T should be a
// numeric type (e.g. double). For example,
//
//             0   1 2   3 4 5   6 7 8
//   dst[0]  [ * | . . | 1 0 0 | . . . ]
//   dst[1]  [ * | . . | 0 1 0 | . . . ]
//   dst[2]  [ * | . . | 0 0 1 | . . . ]
//
// is what would get put in dst if N was 3, offset was 3, and the jet type JetT
// was 8-dimensional.
template <typename JetT, typename T>
inline void Make1stOrderPerturbation(int offset, int N, const T *src,
                                     JetT *dst) {
  DCHECK(src);
  DCHECK(dst);
  for (int j = 0; j < N; ++j) {
    dst[j] = JetT(src[j], offset + j);
  }
}

// Takes the 0th order part of src, assumed to be a Jet type, and puts it in
// dst. This is used to pick out the "vector" part of the extended y.
template <typename JetT, typename T>
inline void Take0thOrderPart(int M, const JetT *src, T dst) {
  DCHECK(src);
  for (int i = 0; i < M; ++i) {
    dst[i] = src[i].a;
  }
}

// Takes N 1st order parts, starting at index N0, and puts them in the M x N
// matrix 'dst'. This is used to pick out the "matrix" parts of the extended y.
template <typename JetT, typename T, int M, int N0, int N>
inline void Take1stOrderPart(const JetT *src, T *dst) {
  DCHECK(src);
  DCHECK(dst);
  // TODO(keir): Change Jet to use a single array, where v[0] is the
  // non-infinitesimal part rather than "a". That way it's possible to use a
  // single memcpy or eigen operation, rather than the explicit loop. The loop
  // doesn't exploit any SSE or other intrinsics.
  for (int i = 0; i < M; ++i) {
    for (int j = 0; j < N; ++j) {
      dst[N * i + j] = src[i].v[N0 + j];
    }
  }
}

// This block of quasi-repeated code calls the user-supplied functor, which may
// take a variable number of arguments. This is accomplished by specializing the
// struct based on the size of the trailing parameters; parameters with 0 size
// are assumed missing.
//
// Supporting variadic functions is the primary source of complexity in the
// autodiff implementation.

template<typename Functor, typename T, int kNumOutputs,
         int N0, int N1, int N2, int N3, int N4, int N5>
struct VariadicEvaluate {
  static bool Call(const Functor& functor, T const *const *input, T* output) {
    return functor(input[0],
                   input[1],
                   input[2],
                   input[3],
                   input[4],
                   input[5],
                   output);
  }
};

template<typename Functor, typename T, int kNumOutputs,
         int N0, int N1, int N2, int N3, int N4>
struct VariadicEvaluate<Functor, T, kNumOutputs, N0, N1, N2, N3, N4, 0> {
  static bool Call(const Functor& functor, T const *const *input, T* output) {
    return functor(input[0],
                   input[1],
                   input[2],
                   input[3],
                   input[4],
                   output);
  }
};

template<typename Functor, typename T, int kNumOutputs,
         int N0, int N1, int N2, int N3>
struct VariadicEvaluate<Functor, T, kNumOutputs, N0, N1, N2, N3, 0, 0> {
  static bool Call(const Functor& functor, T const *const *input, T* output) {
    return functor(input[0],
                   input[1],
                   input[2],
                   input[3],
                   output);
  }
};

template<typename Functor, typename T, int kNumOutputs,
         int N0, int N1, int N2>
struct VariadicEvaluate<Functor, T, kNumOutputs, N0, N1, N2, 0, 0, 0> {
  static bool Call(const Functor& functor, T const *const *input, T* output) {
    return functor(input[0],
                   input[1],
                   input[2],
                   output);
  }
};

template<typename Functor, typename T, int kNumOutputs,
         int N0, int N1>
struct VariadicEvaluate<Functor, T, kNumOutputs, N0, N1, 0, 0, 0, 0> {
  static bool Call(const Functor& functor, T const *const *input, T* output) {
    return functor(input[0],
                   input[1],
                   output);
  }
};

template<typename Functor, typename T, int kNumOutputs, int N0>
struct VariadicEvaluate<Functor, T, kNumOutputs, N0, 0, 0, 0, 0, 0> {
  static bool Call(const Functor& functor, T const *const *input, T* output) {
    return functor(input[0],
                   output);
  }
};

// This is in a struct because default template parameters on a function are not
// supported in C++03 (though it is available in C++0x). N0 through N5 are the
// dimension of the input arguments to the user supplied functor.
template <typename Functor, typename T, int kNumOutputs,
          int N0 = 0, int N1 = 0, int N2 = 0, int N3 = 0, int N4 = 0, int N5=0>
struct AutoDiff {
  static bool Differentiate(const Functor& functor,
                            T const *const *parameters,
                            T *function_value,
                            T **jacobians) {
    typedef Jet<T, N0 + N1 + N2 + N3 + N4 + N5> JetT;

    DCHECK_GT(N0, 0)
        << "Cost functions must have at least one parameter block.";
    DCHECK((!N1 && !N2 && !N3 && !N4 && !N5) ||
           ((N1 > 0) && !N2 && !N3 && !N4 && !N5) ||
           ((N1 > 0) && (N2 > 0) && !N3 && !N4 && !N5) ||
           ((N1 > 0) && (N2 > 0) && (N3 > 0) && !N4 && !N5) ||
           ((N1 > 0) && (N2 > 0) && (N3 > 0) && (N4 > 0) && !N5) ||
           ((N1 > 0) && (N2 > 0) && (N3 > 0) && (N4 > 0) && (N5 > 0)))
        << "Zero block cannot precede a non-zero block. Block sizes are "
        << "(ignore trailing 0s): " << N0 << ", " << N1 << ", " << N2 << ", "
        << N3 << ", " << N4 << ", " << N5;

    DCHECK_GT(kNumOutputs, 0);

    FixedArray<JetT, (256 * 7) / sizeof(JetT)> x(
        N0 + N1 + N2 + N3 + N4 + N5 + kNumOutputs);

    // It's ugly, but it works.
    const int jet0 = 0;
    const int jet1 = N0;
    const int jet2 = N0 + N1;
    const int jet3 = N0 + N1 + N2;
    const int jet4 = N0 + N1 + N2 + N3;
    const int jet5 = N0 + N1 + N2 + N3 + N4;
    const int jet6 = N0 + N1 + N2 + N3 + N4 + N5;

    const JetT *unpacked_parameters[6] = {
        x.get() + jet0,
        x.get() + jet1,
        x.get() + jet2,
        x.get() + jet3,
        x.get() + jet4,
        x.get() + jet5,
    };
    JetT *output = x.get() + jet6;

#define CERES_MAKE_1ST_ORDER_PERTURBATION(i) \
    if (N ## i) { \
      internal::Make1stOrderPerturbation(jet ## i, \
                                         N ## i, \
                                         parameters[i], \
                                         x.get() + jet ## i); \
    }
    CERES_MAKE_1ST_ORDER_PERTURBATION(0);
    CERES_MAKE_1ST_ORDER_PERTURBATION(1);
    CERES_MAKE_1ST_ORDER_PERTURBATION(2);
    CERES_MAKE_1ST_ORDER_PERTURBATION(3);
    CERES_MAKE_1ST_ORDER_PERTURBATION(4);
    CERES_MAKE_1ST_ORDER_PERTURBATION(5);
#undef CERES_MAKE_1ST_ORDER_PERTURBATION

    if (!VariadicEvaluate<Functor, JetT, kNumOutputs,
                          N0, N1, N2, N3, N4, N5>::Call(
        functor, unpacked_parameters, output)) {
      return false;
    }

    internal::Take0thOrderPart(kNumOutputs, output, function_value);

#define CERES_TAKE_1ST_ORDER_PERTURBATION(i) \
    if (N ## i) { \
      if (jacobians[i]) { \
        internal::Take1stOrderPart<JetT, T, \
                                   kNumOutputs, \
                                   jet ## i, \
                                   N ## i>(output, \
                                          jacobians[i]); \
      } \
    }
    CERES_TAKE_1ST_ORDER_PERTURBATION(0);
    CERES_TAKE_1ST_ORDER_PERTURBATION(1);
    CERES_TAKE_1ST_ORDER_PERTURBATION(2);
    CERES_TAKE_1ST_ORDER_PERTURBATION(3);
    CERES_TAKE_1ST_ORDER_PERTURBATION(4);
    CERES_TAKE_1ST_ORDER_PERTURBATION(5);
#undef CERES_TAKE_1ST_ORDER_PERTURBATION
    return true;
  }
};

}  // namespace internal
}  // namespace ceres

#endif  // CERES_PUBLIC_INTERNAL_AUTODIFF_H_
