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

#ifndef CERES_INTERNAL_SOLVER_IMPL_H_
#define CERES_INTERNAL_SOLVER_IMPL_H_

#include <set>
#include <string>
#include <vector>
#include "ceres/internal/port.h"
#include "ceres/ordered_groups.h"
#include "ceres/problem_impl.h"
#include "ceres/solver.h"

namespace ceres {
namespace internal {

class CoordinateDescentMinimizer;
class Evaluator;
class LinearSolver;
class Program;

class SolverImpl {
 public:
  // Mirrors the interface in solver.h, but exposes implementation
  // details for testing internally.
  static void Solve(const Solver::Options& options,
                    ProblemImpl* problem_impl,
                    Solver::Summary* summary);

  static void TrustRegionSolve(const Solver::Options& options,
                               ProblemImpl* problem_impl,
                               Solver::Summary* summary);

  // Run the TrustRegionMinimizer for the given evaluator and configuration.
  static void TrustRegionMinimize(
      const Solver::Options &options,
      Program* program,
      CoordinateDescentMinimizer* inner_iteration_minimizer,
      Evaluator* evaluator,
      LinearSolver* linear_solver,
      double* parameters,
      Solver::Summary* summary);

#ifndef CERES_NO_LINE_SEARCH_MINIMIZER
  static void LineSearchSolve(const Solver::Options& options,
                              ProblemImpl* problem_impl,
                              Solver::Summary* summary);

  // Run the LineSearchMinimizer for the given evaluator and configuration.
  static void LineSearchMinimize(const Solver::Options &options,
                                 Program* program,
                                 Evaluator* evaluator,
                                 double* parameters,
                                 Solver::Summary* summary);
#endif  // CERES_NO_LINE_SEARCH_MINIMIZER

  // Create the transformed Program, which has all the fixed blocks
  // and residuals eliminated, and in the case of automatic schur
  // ordering, has the E blocks first in the resulting program, with
  // options.num_eliminate_blocks set appropriately.
  //
  // If fixed_cost is not NULL, the residual blocks that are removed
  // are evaluated and the sum of their cost is returned in fixed_cost.
  static Program* CreateReducedProgram(Solver::Options* options,
                                       ProblemImpl* problem_impl,
                                       double* fixed_cost,
                                       string* error);

  // Create the appropriate linear solver, taking into account any
  // config changes decided by CreateTransformedProgram(). The
  // selected linear solver, which may be different from what the user
  // selected; consider the case that the remaining elimininated
  // blocks is zero after removing fixed blocks.
  static LinearSolver* CreateLinearSolver(Solver::Options* options,
                                          string* error);

  // Reorder the parameter blocks in program using the ordering. A
  // return value of true indicates success and false indicates an
  // error was encountered whose cause is logged to LOG(ERROR).
  static bool ApplyUserOrdering(const ProblemImpl::ParameterMap& parameter_map,
                                const ParameterBlockOrdering* ordering,
                                Program* program,
                                string* error);


  // Reorder the residuals for program, if necessary, so that the
  // residuals involving e block (i.e., the first num_eliminate_block
  // parameter blocks) occur together. This is a necessary condition
  // for the Schur eliminator.
  static bool LexicographicallyOrderResidualBlocks(
      const int num_eliminate_blocks,
      Program* program,
      string* error);

  // Create the appropriate evaluator for the transformed program.
  static Evaluator* CreateEvaluator(
      const Solver::Options& options,
      const ProblemImpl::ParameterMap& parameter_map,
      Program* program,
      string* error);

  // Remove the fixed or unused parameter blocks and residuals
  // depending only on fixed parameters from the problem. Also updates
  // num_eliminate_blocks, since removed parameters changes the point
  // at which the eliminated blocks is valid.  If fixed_cost is not
  // NULL, the residual blocks that are removed are evaluated and the
  // sum of their cost is returned in fixed_cost.
  static bool RemoveFixedBlocksFromProgram(Program* program,
                                           ParameterBlockOrdering* ordering,
                                           double* fixed_cost,
                                           string* error);

  static bool IsOrderingValid(const Solver::Options& options,
                              const ProblemImpl* problem_impl,
                              string* error);

  static bool IsParameterBlockSetIndependent(
      const set<double*>& parameter_block_ptrs,
      const vector<ResidualBlock*>& residual_blocks);

  static CoordinateDescentMinimizer* CreateInnerIterationMinimizer(
      const Solver::Options& options,
      const Program& program,
      const ProblemImpl::ParameterMap& parameter_map,
      Solver::Summary* summary);
};

}  // namespace internal
}  // namespace ceres

#endif  // CERES_INTERNAL_SOLVER_IMPL_H_
