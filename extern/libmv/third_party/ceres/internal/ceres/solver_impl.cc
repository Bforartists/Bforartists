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

#include "ceres/solver_impl.h"

#include <cstdio>
#include <iostream>  // NOLINT
#include <numeric>
#include "ceres/coordinate_descent_minimizer.h"
#include "ceres/evaluator.h"
#include "ceres/gradient_checking_cost_function.h"
#include "ceres/iteration_callback.h"
#include "ceres/levenberg_marquardt_strategy.h"
#include "ceres/linear_solver.h"
#include "ceres/line_search_minimizer.h"
#include "ceres/map_util.h"
#include "ceres/minimizer.h"
#include "ceres/ordered_groups.h"
#include "ceres/parameter_block.h"
#include "ceres/parameter_block_ordering.h"
#include "ceres/problem.h"
#include "ceres/problem_impl.h"
#include "ceres/program.h"
#include "ceres/residual_block.h"
#include "ceres/stringprintf.h"
#include "ceres/trust_region_minimizer.h"
#include "ceres/wall_time.h"

namespace ceres {
namespace internal {
namespace {

// Callback for updating the user's parameter blocks. Updates are only
// done if the step is successful.
class StateUpdatingCallback : public IterationCallback {
 public:
  StateUpdatingCallback(Program* program, double* parameters)
      : program_(program), parameters_(parameters) {}

  CallbackReturnType operator()(const IterationSummary& summary) {
    if (summary.step_is_successful) {
      program_->StateVectorToParameterBlocks(parameters_);
      program_->CopyParameterBlockStateToUserState();
    }
    return SOLVER_CONTINUE;
  }

 private:
  Program* program_;
  double* parameters_;
};

void SetSummaryFinalCost(Solver::Summary* summary) {
  summary->final_cost = summary->initial_cost;
  // We need the loop here, instead of just looking at the last
  // iteration because the minimizer maybe making non-monotonic steps.
  for (int i = 0; i < summary->iterations.size(); ++i) {
    const IterationSummary& iteration_summary = summary->iterations[i];
    summary->final_cost = min(iteration_summary.cost, summary->final_cost);
  }
}

// Callback for logging the state of the minimizer to STDERR or STDOUT
// depending on the user's preferences and logging level.
class TrustRegionLoggingCallback : public IterationCallback {
 public:
  explicit TrustRegionLoggingCallback(bool log_to_stdout)
      : log_to_stdout_(log_to_stdout) {}

  ~TrustRegionLoggingCallback() {}

  CallbackReturnType operator()(const IterationSummary& summary) {
    const char* kReportRowFormat =
        "% 4d: f:% 8e d:% 3.2e g:% 3.2e h:% 3.2e "
        "rho:% 3.2e mu:% 3.2e li:% 3d it:% 3.2e tt:% 3.2e";
    string output = StringPrintf(kReportRowFormat,
                                 summary.iteration,
                                 summary.cost,
                                 summary.cost_change,
                                 summary.gradient_max_norm,
                                 summary.step_norm,
                                 summary.relative_decrease,
                                 summary.trust_region_radius,
                                 summary.linear_solver_iterations,
                                 summary.iteration_time_in_seconds,
                                 summary.cumulative_time_in_seconds);
    if (log_to_stdout_) {
      cout << output << endl;
    } else {
      VLOG(1) << output;
    }
    return SOLVER_CONTINUE;
  }

 private:
  const bool log_to_stdout_;
};

// Callback for logging the state of the minimizer to STDERR or STDOUT
// depending on the user's preferences and logging level.
class LineSearchLoggingCallback : public IterationCallback {
 public:
  explicit LineSearchLoggingCallback(bool log_to_stdout)
      : log_to_stdout_(log_to_stdout) {}

  ~LineSearchLoggingCallback() {}

  CallbackReturnType operator()(const IterationSummary& summary) {
    const char* kReportRowFormat =
        "% 4d: f:% 8e d:% 3.2e g:% 3.2e h:% 3.2e "
        "s:% 3.2e e:% 3d it:% 3.2e tt:% 3.2e";
    string output = StringPrintf(kReportRowFormat,
                                 summary.iteration,
                                 summary.cost,
                                 summary.cost_change,
                                 summary.gradient_max_norm,
                                 summary.step_norm,
                                 summary.step_size,
                                 summary.line_search_function_evaluations,
                                 summary.iteration_time_in_seconds,
                                 summary.cumulative_time_in_seconds);
    if (log_to_stdout_) {
      cout << output << endl;
    } else {
      VLOG(1) << output;
    }
    return SOLVER_CONTINUE;
  }

 private:
  const bool log_to_stdout_;
};


// Basic callback to record the execution of the solver to a file for
// offline analysis.
class FileLoggingCallback : public IterationCallback {
 public:
  explicit FileLoggingCallback(const string& filename)
      : fptr_(NULL) {
    fptr_ = fopen(filename.c_str(), "w");
    CHECK_NOTNULL(fptr_);
  }

  virtual ~FileLoggingCallback() {
    if (fptr_ != NULL) {
      fclose(fptr_);
    }
  }

  virtual CallbackReturnType operator()(const IterationSummary& summary) {
    fprintf(fptr_,
            "%4d %e %e\n",
            summary.iteration,
            summary.cost,
            summary.cumulative_time_in_seconds);
    return SOLVER_CONTINUE;
  }
 private:
    FILE* fptr_;
};

// Iterate over each of the groups in order of their priority and fill
// summary with their sizes.
void SummarizeOrdering(ParameterBlockOrdering* ordering,
                       vector<int>* summary) {
  CHECK_NOTNULL(summary)->clear();
  if (ordering == NULL) {
    return;
  }

  const map<int, set<double*> >& group_to_elements =
      ordering->group_to_elements();
  for (map<int, set<double*> >::const_iterator it = group_to_elements.begin();
       it != group_to_elements.end();
       ++it) {
    summary->push_back(it->second.size());
  }
}

}  // namespace

void SolverImpl::TrustRegionMinimize(
    const Solver::Options& options,
    Program* program,
    CoordinateDescentMinimizer* inner_iteration_minimizer,
    Evaluator* evaluator,
    LinearSolver* linear_solver,
    double* parameters,
    Solver::Summary* summary) {
  Minimizer::Options minimizer_options(options);

  // TODO(sameeragarwal): Add support for logging the configuration
  // and more detailed stats.
  scoped_ptr<IterationCallback> file_logging_callback;
  if (!options.solver_log.empty()) {
    file_logging_callback.reset(new FileLoggingCallback(options.solver_log));
    minimizer_options.callbacks.insert(minimizer_options.callbacks.begin(),
                                       file_logging_callback.get());
  }

  TrustRegionLoggingCallback logging_callback(
      options.minimizer_progress_to_stdout);
  if (options.logging_type != SILENT) {
    minimizer_options.callbacks.insert(minimizer_options.callbacks.begin(),
                                       &logging_callback);
  }

  StateUpdatingCallback updating_callback(program, parameters);
  if (options.update_state_every_iteration) {
    // This must get pushed to the front of the callbacks so that it is run
    // before any of the user callbacks.
    minimizer_options.callbacks.insert(minimizer_options.callbacks.begin(),
                                       &updating_callback);
  }

  minimizer_options.evaluator = evaluator;
  scoped_ptr<SparseMatrix> jacobian(evaluator->CreateJacobian());

  minimizer_options.jacobian = jacobian.get();
  minimizer_options.inner_iteration_minimizer = inner_iteration_minimizer;

  TrustRegionStrategy::Options trust_region_strategy_options;
  trust_region_strategy_options.linear_solver = linear_solver;
  trust_region_strategy_options.initial_radius =
      options.initial_trust_region_radius;
  trust_region_strategy_options.max_radius = options.max_trust_region_radius;
  trust_region_strategy_options.lm_min_diagonal = options.lm_min_diagonal;
  trust_region_strategy_options.lm_max_diagonal = options.lm_max_diagonal;
  trust_region_strategy_options.trust_region_strategy_type =
      options.trust_region_strategy_type;
  trust_region_strategy_options.dogleg_type = options.dogleg_type;
  scoped_ptr<TrustRegionStrategy> strategy(
      TrustRegionStrategy::Create(trust_region_strategy_options));
  minimizer_options.trust_region_strategy = strategy.get();

  TrustRegionMinimizer minimizer;
  double minimizer_start_time = WallTimeInSeconds();
  minimizer.Minimize(minimizer_options, parameters, summary);
  summary->minimizer_time_in_seconds =
      WallTimeInSeconds() - minimizer_start_time;
}

#ifndef CERES_NO_LINE_SEARCH_MINIMIZER
void SolverImpl::LineSearchMinimize(
    const Solver::Options& options,
    Program* program,
    Evaluator* evaluator,
    double* parameters,
    Solver::Summary* summary) {
  Minimizer::Options minimizer_options(options);

  // TODO(sameeragarwal): Add support for logging the configuration
  // and more detailed stats.
  scoped_ptr<IterationCallback> file_logging_callback;
  if (!options.solver_log.empty()) {
    file_logging_callback.reset(new FileLoggingCallback(options.solver_log));
    minimizer_options.callbacks.insert(minimizer_options.callbacks.begin(),
                                       file_logging_callback.get());
  }

  LineSearchLoggingCallback logging_callback(
      options.minimizer_progress_to_stdout);
  if (options.logging_type != SILENT) {
    minimizer_options.callbacks.insert(minimizer_options.callbacks.begin(),
                                       &logging_callback);
  }

  StateUpdatingCallback updating_callback(program, parameters);
  if (options.update_state_every_iteration) {
    // This must get pushed to the front of the callbacks so that it is run
    // before any of the user callbacks.
    minimizer_options.callbacks.insert(minimizer_options.callbacks.begin(),
                                       &updating_callback);
  }

  minimizer_options.evaluator = evaluator;

  LineSearchMinimizer minimizer;
  double minimizer_start_time = WallTimeInSeconds();
  minimizer.Minimize(minimizer_options, parameters, summary);
  summary->minimizer_time_in_seconds =
      WallTimeInSeconds() - minimizer_start_time;
}
#endif  // CERES_NO_LINE_SEARCH_MINIMIZER

void SolverImpl::Solve(const Solver::Options& options,
                       ProblemImpl* problem_impl,
                       Solver::Summary* summary) {
  if (options.minimizer_type == TRUST_REGION) {
    TrustRegionSolve(options, problem_impl, summary);
  } else {
#ifndef CERES_NO_LINE_SEARCH_MINIMIZER
    LineSearchSolve(options, problem_impl, summary);
#else
    LOG(FATAL) << "Ceres Solver was compiled with -DLINE_SEARCH_MINIMIZER=OFF";
#endif
  }
}

void SolverImpl::TrustRegionSolve(const Solver::Options& original_options,
                                  ProblemImpl* original_problem_impl,
                                  Solver::Summary* summary) {
  EventLogger event_logger("TrustRegionSolve");
  double solver_start_time = WallTimeInSeconds();

  Program* original_program = original_problem_impl->mutable_program();
  ProblemImpl* problem_impl = original_problem_impl;

  // Reset the summary object to its default values.
  *CHECK_NOTNULL(summary) = Solver::Summary();

  summary->minimizer_type = TRUST_REGION;
  summary->num_parameter_blocks = problem_impl->NumParameterBlocks();
  summary->num_parameters = problem_impl->NumParameters();
  summary->num_effective_parameters =
      original_program->NumEffectiveParameters();
  summary->num_residual_blocks = problem_impl->NumResidualBlocks();
  summary->num_residuals = problem_impl->NumResiduals();

  // Empty programs are usually a user error.
  if (summary->num_parameter_blocks == 0) {
    summary->error = "Problem contains no parameter blocks.";
    LOG(ERROR) << summary->error;
    return;
  }

  if (summary->num_residual_blocks == 0) {
    summary->error = "Problem contains no residual blocks.";
    LOG(ERROR) << summary->error;
    return;
  }

  SummarizeOrdering(original_options.linear_solver_ordering,
                    &(summary->linear_solver_ordering_given));

  SummarizeOrdering(original_options.inner_iteration_ordering,
                    &(summary->inner_iteration_ordering_given));

  Solver::Options options(original_options);
  options.linear_solver_ordering = NULL;
  options.inner_iteration_ordering = NULL;

#ifndef CERES_USE_OPENMP
  if (options.num_threads > 1) {
    LOG(WARNING)
        << "OpenMP support is not compiled into this binary; "
        << "only options.num_threads=1 is supported. Switching "
        << "to single threaded mode.";
    options.num_threads = 1;
  }
  if (options.num_linear_solver_threads > 1) {
    LOG(WARNING)
        << "OpenMP support is not compiled into this binary; "
        << "only options.num_linear_solver_threads=1 is supported. Switching "
        << "to single threaded mode.";
    options.num_linear_solver_threads = 1;
  }
#endif

  summary->num_threads_given = original_options.num_threads;
  summary->num_threads_used = options.num_threads;

  if (options.lsqp_iterations_to_dump.size() > 0) {
    LOG(WARNING) << "Dumping linear least squares problems to disk is"
        " currently broken. Ignoring Solver::Options::lsqp_iterations_to_dump";
  }

  event_logger.AddEvent("Init");

  original_program->SetParameterBlockStatePtrsToUserStatePtrs();
  event_logger.AddEvent("SetParameterBlockPtrs");

  // If the user requests gradient checking, construct a new
  // ProblemImpl by wrapping the CostFunctions of problem_impl inside
  // GradientCheckingCostFunction and replacing problem_impl with
  // gradient_checking_problem_impl.
  scoped_ptr<ProblemImpl> gradient_checking_problem_impl;
  if (options.check_gradients) {
    VLOG(1) << "Checking Gradients";
    gradient_checking_problem_impl.reset(
        CreateGradientCheckingProblemImpl(
            problem_impl,
            options.numeric_derivative_relative_step_size,
            options.gradient_check_relative_precision));

    // From here on, problem_impl will point to the gradient checking
    // version.
    problem_impl = gradient_checking_problem_impl.get();
  }

  if (original_options.linear_solver_ordering != NULL) {
    if (!IsOrderingValid(original_options, problem_impl, &summary->error)) {
      LOG(ERROR) << summary->error;
      return;
    }
    event_logger.AddEvent("CheckOrdering");
    options.linear_solver_ordering =
        new ParameterBlockOrdering(*original_options.linear_solver_ordering);
    event_logger.AddEvent("CopyOrdering");
  } else {
    options.linear_solver_ordering = new ParameterBlockOrdering;
    const ProblemImpl::ParameterMap& parameter_map =
        problem_impl->parameter_map();
    for (ProblemImpl::ParameterMap::const_iterator it = parameter_map.begin();
         it != parameter_map.end();
         ++it) {
      options.linear_solver_ordering->AddElementToGroup(it->first, 0);
    }
    event_logger.AddEvent("ConstructOrdering");
  }

  // Create the three objects needed to minimize: the transformed program, the
  // evaluator, and the linear solver.
  scoped_ptr<Program> reduced_program(CreateReducedProgram(&options,
                                                           problem_impl,
                                                           &summary->fixed_cost,
                                                           &summary->error));

  event_logger.AddEvent("CreateReducedProgram");
  if (reduced_program == NULL) {
    return;
  }

  SummarizeOrdering(options.linear_solver_ordering,
                    &(summary->linear_solver_ordering_used));

  summary->num_parameter_blocks_reduced = reduced_program->NumParameterBlocks();
  summary->num_parameters_reduced = reduced_program->NumParameters();
  summary->num_effective_parameters_reduced =
      reduced_program->NumEffectiveParameters();
  summary->num_residual_blocks_reduced = reduced_program->NumResidualBlocks();
  summary->num_residuals_reduced = reduced_program->NumResiduals();

  if (summary->num_parameter_blocks_reduced == 0) {
    summary->preprocessor_time_in_seconds =
        WallTimeInSeconds() - solver_start_time;

    double post_process_start_time = WallTimeInSeconds();
    LOG(INFO) << "Terminating: FUNCTION_TOLERANCE reached. "
              << "No non-constant parameter blocks found.";

    summary->initial_cost = summary->fixed_cost;
    summary->final_cost = summary->fixed_cost;

    // FUNCTION_TOLERANCE is the right convergence here, as we know
    // that the objective function is constant and cannot be changed
    // any further.
    summary->termination_type = FUNCTION_TOLERANCE;

    // Ensure the program state is set to the user parameters on the way out.
    original_program->SetParameterBlockStatePtrsToUserStatePtrs();

    summary->postprocessor_time_in_seconds =
        WallTimeInSeconds() - post_process_start_time;
    return;
  }

  scoped_ptr<LinearSolver>
      linear_solver(CreateLinearSolver(&options, &summary->error));
  event_logger.AddEvent("CreateLinearSolver");
  if (linear_solver == NULL) {
    return;
  }

  summary->linear_solver_type_given = original_options.linear_solver_type;
  summary->linear_solver_type_used = options.linear_solver_type;

  summary->preconditioner_type = options.preconditioner_type;

  summary->num_linear_solver_threads_given =
      original_options.num_linear_solver_threads;
  summary->num_linear_solver_threads_used = options.num_linear_solver_threads;

  summary->sparse_linear_algebra_library =
      options.sparse_linear_algebra_library;

  summary->trust_region_strategy_type = options.trust_region_strategy_type;
  summary->dogleg_type = options.dogleg_type;

  // Only Schur types require the lexicographic reordering.
  if (IsSchurType(options.linear_solver_type)) {
    const int num_eliminate_blocks =
        options.linear_solver_ordering
        ->group_to_elements().begin()
        ->second.size();
    if (!LexicographicallyOrderResidualBlocks(num_eliminate_blocks,
                                              reduced_program.get(),
                                              &summary->error)) {
      return;
    }
  }

  scoped_ptr<Evaluator> evaluator(CreateEvaluator(options,
                                                  problem_impl->parameter_map(),
                                                  reduced_program.get(),
                                                  &summary->error));

  event_logger.AddEvent("CreateEvaluator");

  if (evaluator == NULL) {
    return;
  }

  scoped_ptr<CoordinateDescentMinimizer> inner_iteration_minimizer;
  if (options.use_inner_iterations) {
    if (reduced_program->parameter_blocks().size() < 2) {
      LOG(WARNING) << "Reduced problem only contains one parameter block."
                   << "Disabling inner iterations.";
    } else {
      inner_iteration_minimizer.reset(
          CreateInnerIterationMinimizer(original_options,
                                        *reduced_program,
                                        problem_impl->parameter_map(),
                                        summary));
      if (inner_iteration_minimizer == NULL) {
        LOG(ERROR) << summary->error;
        return;
      }
    }
  }

  event_logger.AddEvent("CreateIIM");

  // The optimizer works on contiguous parameter vectors; allocate some.
  Vector parameters(reduced_program->NumParameters());

  // Collect the discontiguous parameters into a contiguous state vector.
  reduced_program->ParameterBlocksToStateVector(parameters.data());

  Vector original_parameters = parameters;

  double minimizer_start_time = WallTimeInSeconds();
  summary->preprocessor_time_in_seconds =
      minimizer_start_time - solver_start_time;

  // Run the optimization.
  TrustRegionMinimize(options,
                      reduced_program.get(),
                      inner_iteration_minimizer.get(),
                      evaluator.get(),
                      linear_solver.get(),
                      parameters.data(),
                      summary);
  event_logger.AddEvent("Minimize");

  SetSummaryFinalCost(summary);

  // If the user aborted mid-optimization or the optimization
  // terminated because of a numerical failure, then return without
  // updating user state.
  if (summary->termination_type == USER_ABORT ||
      summary->termination_type == NUMERICAL_FAILURE) {
    return;
  }

  double post_process_start_time = WallTimeInSeconds();

  // Push the contiguous optimized parameters back to the user's
  // parameters.
  reduced_program->StateVectorToParameterBlocks(parameters.data());
  reduced_program->CopyParameterBlockStateToUserState();

  // Ensure the program state is set to the user parameters on the way
  // out.
  original_program->SetParameterBlockStatePtrsToUserStatePtrs();

  const map<string, double>& linear_solver_time_statistics =
      linear_solver->TimeStatistics();
  summary->linear_solver_time_in_seconds =
      FindWithDefault(linear_solver_time_statistics,
                      "LinearSolver::Solve",
                      0.0);

  const map<string, double>& evaluator_time_statistics =
      evaluator->TimeStatistics();

  summary->residual_evaluation_time_in_seconds =
      FindWithDefault(evaluator_time_statistics, "Evaluator::Residual", 0.0);
  summary->jacobian_evaluation_time_in_seconds =
      FindWithDefault(evaluator_time_statistics, "Evaluator::Jacobian", 0.0);

  // Stick a fork in it, we're done.
  summary->postprocessor_time_in_seconds =
      WallTimeInSeconds() - post_process_start_time;
  event_logger.AddEvent("PostProcess");
}


#ifndef CERES_NO_LINE_SEARCH_MINIMIZER
void SolverImpl::LineSearchSolve(const Solver::Options& original_options,
                                 ProblemImpl* original_problem_impl,
                                 Solver::Summary* summary) {
  double solver_start_time = WallTimeInSeconds();

  Program* original_program = original_problem_impl->mutable_program();
  ProblemImpl* problem_impl = original_problem_impl;

  // Reset the summary object to its default values.
  *CHECK_NOTNULL(summary) = Solver::Summary();

  summary->minimizer_type = LINE_SEARCH;
  summary->line_search_direction_type =
      original_options.line_search_direction_type;
  summary->max_lbfgs_rank = original_options.max_lbfgs_rank;
  summary->line_search_type = original_options.line_search_type;
  summary->num_parameter_blocks = problem_impl->NumParameterBlocks();
  summary->num_parameters = problem_impl->NumParameters();
  summary->num_residual_blocks = problem_impl->NumResidualBlocks();
  summary->num_residuals = problem_impl->NumResiduals();

  // Empty programs are usually a user error.
  if (summary->num_parameter_blocks == 0) {
    summary->error = "Problem contains no parameter blocks.";
    LOG(ERROR) << summary->error;
    return;
  }

  if (summary->num_residual_blocks == 0) {
    summary->error = "Problem contains no residual blocks.";
    LOG(ERROR) << summary->error;
    return;
  }

  Solver::Options options(original_options);

  // This ensures that we get a Block Jacobian Evaluator along with
  // none of the Schur nonsense. This file will have to be extensively
  // refactored to deal with the various bits of cleanups related to
  // line search.
  options.linear_solver_type = CGNR;

  options.linear_solver_ordering = NULL;
  options.inner_iteration_ordering = NULL;

#ifndef CERES_USE_OPENMP
  if (options.num_threads > 1) {
    LOG(WARNING)
        << "OpenMP support is not compiled into this binary; "
        << "only options.num_threads=1 is supported. Switching "
        << "to single threaded mode.";
    options.num_threads = 1;
  }
#endif  // CERES_USE_OPENMP

  summary->num_threads_given = original_options.num_threads;
  summary->num_threads_used = options.num_threads;

  if (original_options.linear_solver_ordering != NULL) {
    if (!IsOrderingValid(original_options, problem_impl, &summary->error)) {
      LOG(ERROR) << summary->error;
      return;
    }
    options.linear_solver_ordering =
        new ParameterBlockOrdering(*original_options.linear_solver_ordering);
  } else {
    options.linear_solver_ordering = new ParameterBlockOrdering;
    const ProblemImpl::ParameterMap& parameter_map =
        problem_impl->parameter_map();
    for (ProblemImpl::ParameterMap::const_iterator it = parameter_map.begin();
         it != parameter_map.end();
         ++it) {
      options.linear_solver_ordering->AddElementToGroup(it->first, 0);
    }
  }

  original_program->SetParameterBlockStatePtrsToUserStatePtrs();

  // If the user requests gradient checking, construct a new
  // ProblemImpl by wrapping the CostFunctions of problem_impl inside
  // GradientCheckingCostFunction and replacing problem_impl with
  // gradient_checking_problem_impl.
  scoped_ptr<ProblemImpl> gradient_checking_problem_impl;
  if (options.check_gradients) {
    VLOG(1) << "Checking Gradients";
    gradient_checking_problem_impl.reset(
        CreateGradientCheckingProblemImpl(
            problem_impl,
            options.numeric_derivative_relative_step_size,
            options.gradient_check_relative_precision));

    // From here on, problem_impl will point to the gradient checking
    // version.
    problem_impl = gradient_checking_problem_impl.get();
  }

  // Create the three objects needed to minimize: the transformed program, the
  // evaluator, and the linear solver.
  scoped_ptr<Program> reduced_program(CreateReducedProgram(&options,
                                                           problem_impl,
                                                           &summary->fixed_cost,
                                                           &summary->error));
  if (reduced_program == NULL) {
    return;
  }

  summary->num_parameter_blocks_reduced = reduced_program->NumParameterBlocks();
  summary->num_parameters_reduced = reduced_program->NumParameters();
  summary->num_residual_blocks_reduced = reduced_program->NumResidualBlocks();
  summary->num_residuals_reduced = reduced_program->NumResiduals();

  if (summary->num_parameter_blocks_reduced == 0) {
    summary->preprocessor_time_in_seconds =
        WallTimeInSeconds() - solver_start_time;

    LOG(INFO) << "Terminating: FUNCTION_TOLERANCE reached. "
              << "No non-constant parameter blocks found.";

    // FUNCTION_TOLERANCE is the right convergence here, as we know
    // that the objective function is constant and cannot be changed
    // any further.
    summary->termination_type = FUNCTION_TOLERANCE;

    const double post_process_start_time = WallTimeInSeconds();

    SetSummaryFinalCost(summary);

    // Ensure the program state is set to the user parameters on the way out.
    original_program->SetParameterBlockStatePtrsToUserStatePtrs();
    summary->postprocessor_time_in_seconds =
        WallTimeInSeconds() - post_process_start_time;
    return;
  }

  scoped_ptr<Evaluator> evaluator(CreateEvaluator(options,
                                                  problem_impl->parameter_map(),
                                                  reduced_program.get(),
                                                  &summary->error));
  if (evaluator == NULL) {
    return;
  }

  // The optimizer works on contiguous parameter vectors; allocate some.
  Vector parameters(reduced_program->NumParameters());

  // Collect the discontiguous parameters into a contiguous state vector.
  reduced_program->ParameterBlocksToStateVector(parameters.data());

  Vector original_parameters = parameters;

  const double minimizer_start_time = WallTimeInSeconds();
  summary->preprocessor_time_in_seconds =
      minimizer_start_time - solver_start_time;

  // Run the optimization.
  LineSearchMinimize(options,
                     reduced_program.get(),
                     evaluator.get(),
                     parameters.data(),
                     summary);

  // If the user aborted mid-optimization or the optimization
  // terminated because of a numerical failure, then return without
  // updating user state.
  if (summary->termination_type == USER_ABORT ||
      summary->termination_type == NUMERICAL_FAILURE) {
    return;
  }

  const double post_process_start_time = WallTimeInSeconds();

  // Push the contiguous optimized parameters back to the user's parameters.
  reduced_program->StateVectorToParameterBlocks(parameters.data());
  reduced_program->CopyParameterBlockStateToUserState();

  SetSummaryFinalCost(summary);

  // Ensure the program state is set to the user parameters on the way out.
  original_program->SetParameterBlockStatePtrsToUserStatePtrs();

  const map<string, double>& evaluator_time_statistics =
      evaluator->TimeStatistics();

  summary->residual_evaluation_time_in_seconds =
      FindWithDefault(evaluator_time_statistics, "Evaluator::Residual", 0.0);
  summary->jacobian_evaluation_time_in_seconds =
      FindWithDefault(evaluator_time_statistics, "Evaluator::Jacobian", 0.0);

  // Stick a fork in it, we're done.
  summary->postprocessor_time_in_seconds =
      WallTimeInSeconds() - post_process_start_time;
}
#endif  // CERES_NO_LINE_SEARCH_MINIMIZER

bool SolverImpl::IsOrderingValid(const Solver::Options& options,
                                 const ProblemImpl* problem_impl,
                                 string* error) {
  if (options.linear_solver_ordering->NumElements() !=
      problem_impl->NumParameterBlocks()) {
      *error = "Number of parameter blocks in user supplied ordering "
          "does not match the number of parameter blocks in the problem";
    return false;
  }

  const Program& program = problem_impl->program();
  const vector<ParameterBlock*>& parameter_blocks = program.parameter_blocks();
  for (vector<ParameterBlock*>::const_iterator it = parameter_blocks.begin();
       it != parameter_blocks.end();
       ++it) {
    if (!options.linear_solver_ordering
        ->IsMember(const_cast<double*>((*it)->user_state()))) {
      *error = "Problem contains a parameter block that is not in "
          "the user specified ordering.";
      return false;
    }
  }

  if (IsSchurType(options.linear_solver_type) &&
      options.linear_solver_ordering->NumGroups() > 1) {
    const vector<ResidualBlock*>& residual_blocks = program.residual_blocks();
    const set<double*>& e_blocks  =
        options.linear_solver_ordering->group_to_elements().begin()->second;
    if (!IsParameterBlockSetIndependent(e_blocks, residual_blocks)) {
      *error = "The user requested the use of a Schur type solver. "
          "But the first elimination group in the ordering is not an "
          "independent set.";
      return false;
    }
  }
  return true;
}

bool SolverImpl::IsParameterBlockSetIndependent(
    const set<double*>& parameter_block_ptrs,
    const vector<ResidualBlock*>& residual_blocks) {
  // Loop over each residual block and ensure that no two parameter
  // blocks in the same residual block are part of
  // parameter_block_ptrs as that would violate the assumption that it
  // is an independent set in the Hessian matrix.
  for (vector<ResidualBlock*>::const_iterator it = residual_blocks.begin();
       it != residual_blocks.end();
       ++it) {
    ParameterBlock* const* parameter_blocks = (*it)->parameter_blocks();
    const int num_parameter_blocks = (*it)->NumParameterBlocks();
    int count = 0;
    for (int i = 0; i < num_parameter_blocks; ++i) {
      count += parameter_block_ptrs.count(
          parameter_blocks[i]->mutable_user_state());
    }
    if (count > 1) {
      return false;
    }
  }
  return true;
}


// Strips varying parameters and residuals, maintaining order, and updating
// num_eliminate_blocks.
bool SolverImpl::RemoveFixedBlocksFromProgram(Program* program,
                                              ParameterBlockOrdering* ordering,
                                              double* fixed_cost,
                                              string* error) {
  vector<ParameterBlock*>* parameter_blocks =
      program->mutable_parameter_blocks();

  scoped_array<double> residual_block_evaluate_scratch;
  if (fixed_cost != NULL) {
    residual_block_evaluate_scratch.reset(
        new double[program->MaxScratchDoublesNeededForEvaluate()]);
    *fixed_cost = 0.0;
  }

  // Mark all the parameters as unused. Abuse the index member of the parameter
  // blocks for the marking.
  for (int i = 0; i < parameter_blocks->size(); ++i) {
    (*parameter_blocks)[i]->set_index(-1);
  }

  // Filter out residual that have all-constant parameters, and mark all the
  // parameter blocks that appear in residuals.
  {
    vector<ResidualBlock*>* residual_blocks =
        program->mutable_residual_blocks();
    int j = 0;
    for (int i = 0; i < residual_blocks->size(); ++i) {
      ResidualBlock* residual_block = (*residual_blocks)[i];
      int num_parameter_blocks = residual_block->NumParameterBlocks();

      // Determine if the residual block is fixed, and also mark varying
      // parameters that appear in the residual block.
      bool all_constant = true;
      for (int k = 0; k < num_parameter_blocks; k++) {
        ParameterBlock* parameter_block = residual_block->parameter_blocks()[k];
        if (!parameter_block->IsConstant()) {
          all_constant = false;
          parameter_block->set_index(1);
        }
      }

      if (!all_constant) {
        (*residual_blocks)[j++] = (*residual_blocks)[i];
      } else if (fixed_cost != NULL) {
        // The residual is constant and will be removed, so its cost is
        // added to the variable fixed_cost.
        double cost = 0.0;
        if (!residual_block->Evaluate(true,
                                      &cost,
                                      NULL,
                                      NULL,
                                      residual_block_evaluate_scratch.get())) {
          *error = StringPrintf("Evaluation of the residual %d failed during "
                                "removal of fixed residual blocks.", i);
          return false;
        }
        *fixed_cost += cost;
      }
    }
    residual_blocks->resize(j);
  }

  // Filter out unused or fixed parameter blocks, and update
  // the ordering.
  {
    vector<ParameterBlock*>* parameter_blocks =
        program->mutable_parameter_blocks();
    int j = 0;
    for (int i = 0; i < parameter_blocks->size(); ++i) {
      ParameterBlock* parameter_block = (*parameter_blocks)[i];
      if (parameter_block->index() == 1) {
        (*parameter_blocks)[j++] = parameter_block;
      } else {
        ordering->Remove(parameter_block->mutable_user_state());
      }
    }
    parameter_blocks->resize(j);
  }

  CHECK(((program->NumResidualBlocks() == 0) &&
         (program->NumParameterBlocks() == 0)) ||
        ((program->NumResidualBlocks() != 0) &&
         (program->NumParameterBlocks() != 0)))
      << "Congratulations, you found a bug in Ceres. Please report it.";
  return true;
}

Program* SolverImpl::CreateReducedProgram(Solver::Options* options,
                                          ProblemImpl* problem_impl,
                                          double* fixed_cost,
                                          string* error) {
  EventLogger event_logger("CreateReducedProgram");

  CHECK_NOTNULL(options->linear_solver_ordering);
  Program* original_program = problem_impl->mutable_program();
  scoped_ptr<Program> transformed_program(new Program(*original_program));
  event_logger.AddEvent("TransformedProgram");

  ParameterBlockOrdering* linear_solver_ordering =
      options->linear_solver_ordering;

  const int min_group_id =
      linear_solver_ordering->group_to_elements().begin()->first;
  const int original_num_groups = linear_solver_ordering->NumGroups();

  if (!RemoveFixedBlocksFromProgram(transformed_program.get(),
                                    linear_solver_ordering,
                                    fixed_cost,
                                    error)) {
    return NULL;
  }

  event_logger.AddEvent("RemoveFixedBlocks");

  if (transformed_program->NumParameterBlocks() == 0) {
    if (transformed_program->NumResidualBlocks() > 0) {
      *error = "Zero parameter blocks but non-zero residual blocks"
          " in the reduced program. Congratulations, you found a "
          "Ceres bug! Please report this error to the developers.";
      return NULL;
    }

    LOG(WARNING) << "No varying parameter blocks to optimize; "
                 << "bailing early.";
    return transformed_program.release();
  }

  // If the user supplied an linear_solver_ordering with just one
  // group, it is equivalent to the user supplying NULL as
  // ordering. Ceres is completely free to choose the parameter block
  // ordering as it sees fit. For Schur type solvers, this means that
  // the user wishes for Ceres to identify the e_blocks, which we do
  // by computing a maximal independent set.
  if (original_num_groups == 1 && IsSchurType(options->linear_solver_type)) {
    vector<ParameterBlock*> schur_ordering;
    const int num_eliminate_blocks = ComputeSchurOrdering(*transformed_program,
                                                          &schur_ordering);
    CHECK_EQ(schur_ordering.size(), transformed_program->NumParameterBlocks())
        << "Congratulations, you found a Ceres bug! Please report this error "
        << "to the developers.";

    for (int i = 0; i < schur_ordering.size(); ++i) {
      linear_solver_ordering->AddElementToGroup(
          schur_ordering[i]->mutable_user_state(),
          (i < num_eliminate_blocks) ? 0 : 1);
    }
  }
  event_logger.AddEvent("SchurOrdering");

  if (!ApplyUserOrdering(problem_impl->parameter_map(),
                         linear_solver_ordering,
                         transformed_program.get(),
                         error)) {
    return NULL;
  }
  event_logger.AddEvent("ApplyOrdering");

  // If the user requested the use of a Schur type solver, and
  // supplied a non-NULL linear_solver_ordering object with more than
  // one elimination group, then it can happen that after all the
  // parameter blocks which are fixed or unused have been removed from
  // the program and the ordering, there are no more parameter blocks
  // in the first elimination group.
  //
  // In such a case, the use of a Schur type solver is not possible,
  // as they assume there is at least one e_block. Thus, we
  // automatically switch to one of the other solvers, depending on
  // the user's indicated preferences.
  if (IsSchurType(options->linear_solver_type) &&
      original_num_groups > 1 &&
      linear_solver_ordering->GroupSize(min_group_id) == 0) {
    string msg = "No e_blocks remaining. Switching from ";
    if (options->linear_solver_type == SPARSE_SCHUR) {
      options->linear_solver_type = SPARSE_NORMAL_CHOLESKY;
      msg += "SPARSE_SCHUR to SPARSE_NORMAL_CHOLESKY.";
    } else if (options->linear_solver_type == DENSE_SCHUR) {
      // TODO(sameeragarwal): This is probably not a great choice.
      // Ideally, we should have a DENSE_NORMAL_CHOLESKY, that can
      // take a BlockSparseMatrix as input.
      options->linear_solver_type = DENSE_QR;
      msg += "DENSE_SCHUR to DENSE_QR.";
    } else if (options->linear_solver_type == ITERATIVE_SCHUR) {
      msg += StringPrintf("ITERATIVE_SCHUR with %s preconditioner "
                          "to CGNR with JACOBI preconditioner.",
                          PreconditionerTypeToString(
                              options->preconditioner_type));
      options->linear_solver_type = CGNR;
      if (options->preconditioner_type != IDENTITY) {
        // CGNR currently only supports the JACOBI preconditioner.
        options->preconditioner_type = JACOBI;
      }
    }

    LOG(WARNING) << msg;
  }

  event_logger.AddEvent("AlternateSolver");

  // Since the transformed program is the "active" program, and it is
  // mutated, update the parameter offsets and indices.
  transformed_program->SetParameterOffsetsAndIndex();

  event_logger.AddEvent("SetOffsets");
  return transformed_program.release();
}

LinearSolver* SolverImpl::CreateLinearSolver(Solver::Options* options,
                                             string* error) {
  CHECK_NOTNULL(options);
  CHECK_NOTNULL(options->linear_solver_ordering);
  CHECK_NOTNULL(error);

  if (options->trust_region_strategy_type == DOGLEG) {
    if (options->linear_solver_type == ITERATIVE_SCHUR ||
        options->linear_solver_type == CGNR) {
      *error = "DOGLEG only supports exact factorization based linear "
               "solvers. If you want to use an iterative solver please "
               "use LEVENBERG_MARQUARDT as the trust_region_strategy_type";
      return NULL;
    }
  }

#ifdef CERES_NO_SUITESPARSE
  if (options->linear_solver_type == SPARSE_NORMAL_CHOLESKY &&
      options->sparse_linear_algebra_library == SUITE_SPARSE) {
    *error = "Can't use SPARSE_NORMAL_CHOLESKY with SUITESPARSE because "
             "SuiteSparse was not enabled when Ceres was built.";
    return NULL;
  }

  if (options->preconditioner_type == CLUSTER_JACOBI) {
    *error =  "CLUSTER_JACOBI preconditioner not suppored. Please build Ceres "
        "with SuiteSparse support.";
    return NULL;
  }

  if (options->preconditioner_type == CLUSTER_TRIDIAGONAL) {
    *error =  "CLUSTER_TRIDIAGONAL preconditioner not suppored. Please build "
        "Ceres with SuiteSparse support.";
    return NULL;
  }
#endif

#ifdef CERES_NO_CXSPARSE
  if (options->linear_solver_type == SPARSE_NORMAL_CHOLESKY &&
      options->sparse_linear_algebra_library == CX_SPARSE) {
    *error = "Can't use SPARSE_NORMAL_CHOLESKY with CXSPARSE because "
             "CXSparse was not enabled when Ceres was built.";
    return NULL;
  }
#endif

#if defined(CERES_NO_SUITESPARSE) && defined(CERES_NO_CXSPARSE)
  if (options->linear_solver_type == SPARSE_SCHUR) {
    *error = "Can't use SPARSE_SCHUR because neither SuiteSparse nor"
        "CXSparse was enabled when Ceres was compiled.";
    return NULL;
  }
#endif

  if (options->linear_solver_max_num_iterations <= 0) {
    *error = "Solver::Options::linear_solver_max_num_iterations is 0.";
    return NULL;
  }
  if (options->linear_solver_min_num_iterations <= 0) {
    *error = "Solver::Options::linear_solver_min_num_iterations is 0.";
    return NULL;
  }
  if (options->linear_solver_min_num_iterations >
      options->linear_solver_max_num_iterations) {
    *error = "Solver::Options::linear_solver_min_num_iterations > "
        "Solver::Options::linear_solver_max_num_iterations.";
    return NULL;
  }

  LinearSolver::Options linear_solver_options;
  linear_solver_options.min_num_iterations =
        options->linear_solver_min_num_iterations;
  linear_solver_options.max_num_iterations =
      options->linear_solver_max_num_iterations;
  linear_solver_options.type = options->linear_solver_type;
  linear_solver_options.preconditioner_type = options->preconditioner_type;
  linear_solver_options.sparse_linear_algebra_library =
      options->sparse_linear_algebra_library;

  linear_solver_options.num_threads = options->num_linear_solver_threads;
  options->num_linear_solver_threads = linear_solver_options.num_threads;

  linear_solver_options.use_block_amd = options->use_block_amd;
  const map<int, set<double*> >& groups =
      options->linear_solver_ordering->group_to_elements();
  for (map<int, set<double*> >::const_iterator it = groups.begin();
       it != groups.end();
       ++it) {
    linear_solver_options.elimination_groups.push_back(it->second.size());
  }
  // Schur type solvers, expect at least two elimination groups. If
  // there is only one elimination group, then CreateReducedProgram
  // guarantees that this group only contains e_blocks. Thus we add a
  // dummy elimination group with zero blocks in it.
  if (IsSchurType(linear_solver_options.type) &&
      linear_solver_options.elimination_groups.size() == 1) {
    linear_solver_options.elimination_groups.push_back(0);
  }

  return LinearSolver::Create(linear_solver_options);
}

bool SolverImpl::ApplyUserOrdering(
    const ProblemImpl::ParameterMap& parameter_map,
    const ParameterBlockOrdering* ordering,
    Program* program,
    string* error) {
  if (ordering->NumElements() != program->NumParameterBlocks()) {
    *error = StringPrintf("User specified ordering does not have the same "
                          "number of parameters as the problem. The problem"
                          "has %d blocks while the ordering has %d blocks.",
                          program->NumParameterBlocks(),
                          ordering->NumElements());
    return false;
  }

  vector<ParameterBlock*>* parameter_blocks =
      program->mutable_parameter_blocks();
  parameter_blocks->clear();

  const map<int, set<double*> >& groups =
      ordering->group_to_elements();

  for (map<int, set<double*> >::const_iterator group_it = groups.begin();
       group_it != groups.end();
       ++group_it) {
    const set<double*>& group = group_it->second;
    for (set<double*>::const_iterator parameter_block_ptr_it = group.begin();
         parameter_block_ptr_it != group.end();
         ++parameter_block_ptr_it) {
      ProblemImpl::ParameterMap::const_iterator parameter_block_it =
          parameter_map.find(*parameter_block_ptr_it);
      if (parameter_block_it == parameter_map.end()) {
        *error = StringPrintf("User specified ordering contains a pointer "
                              "to a double that is not a parameter block in "
                              "the problem. The invalid double is in group: %d",
                              group_it->first);
        return false;
      }
      parameter_blocks->push_back(parameter_block_it->second);
    }
  }
  return true;
}

// Find the minimum index of any parameter block to the given residual.
// Parameter blocks that have indices greater than num_eliminate_blocks are
// considered to have an index equal to num_eliminate_blocks.
static int MinParameterBlock(const ResidualBlock* residual_block,
                             int num_eliminate_blocks) {
  int min_parameter_block_position = num_eliminate_blocks;
  for (int i = 0; i < residual_block->NumParameterBlocks(); ++i) {
    ParameterBlock* parameter_block = residual_block->parameter_blocks()[i];
    if (!parameter_block->IsConstant()) {
      CHECK_NE(parameter_block->index(), -1)
          << "Did you forget to call Program::SetParameterOffsetsAndIndex()? "
          << "This is a Ceres bug; please contact the developers!";
      min_parameter_block_position = std::min(parameter_block->index(),
                                              min_parameter_block_position);
    }
  }
  return min_parameter_block_position;
}

// Reorder the residuals for program, if necessary, so that the residuals
// involving each E block occur together. This is a necessary condition for the
// Schur eliminator, which works on these "row blocks" in the jacobian.
bool SolverImpl::LexicographicallyOrderResidualBlocks(
    const int num_eliminate_blocks,
    Program* program,
    string* error) {
  CHECK_GE(num_eliminate_blocks, 1)
      << "Congratulations, you found a Ceres bug! Please report this error "
      << "to the developers.";

  // Create a histogram of the number of residuals for each E block. There is an
  // extra bucket at the end to catch all non-eliminated F blocks.
  vector<int> residual_blocks_per_e_block(num_eliminate_blocks + 1);
  vector<ResidualBlock*>* residual_blocks = program->mutable_residual_blocks();
  vector<int> min_position_per_residual(residual_blocks->size());
  for (int i = 0; i < residual_blocks->size(); ++i) {
    ResidualBlock* residual_block = (*residual_blocks)[i];
    int position = MinParameterBlock(residual_block, num_eliminate_blocks);
    min_position_per_residual[i] = position;
    DCHECK_LE(position, num_eliminate_blocks);
    residual_blocks_per_e_block[position]++;
  }

  // Run a cumulative sum on the histogram, to obtain offsets to the start of
  // each histogram bucket (where each bucket is for the residuals for that
  // E-block).
  vector<int> offsets(num_eliminate_blocks + 1);
  std::partial_sum(residual_blocks_per_e_block.begin(),
                   residual_blocks_per_e_block.end(),
                   offsets.begin());
  CHECK_EQ(offsets.back(), residual_blocks->size())
      << "Congratulations, you found a Ceres bug! Please report this error "
      << "to the developers.";

  CHECK(find(residual_blocks_per_e_block.begin(),
             residual_blocks_per_e_block.end() - 1, 0) !=
        residual_blocks_per_e_block.end())
      << "Congratulations, you found a Ceres bug! Please report this error "
      << "to the developers.";

  // Fill in each bucket with the residual blocks for its corresponding E block.
  // Each bucket is individually filled from the back of the bucket to the front
  // of the bucket. The filling order among the buckets is dictated by the
  // residual blocks. This loop uses the offsets as counters; subtracting one
  // from each offset as a residual block is placed in the bucket. When the
  // filling is finished, the offset pointerts should have shifted down one
  // entry (this is verified below).
  vector<ResidualBlock*> reordered_residual_blocks(
      (*residual_blocks).size(), static_cast<ResidualBlock*>(NULL));
  for (int i = 0; i < residual_blocks->size(); ++i) {
    int bucket = min_position_per_residual[i];

    // Decrement the cursor, which should now point at the next empty position.
    offsets[bucket]--;

    // Sanity.
    CHECK(reordered_residual_blocks[offsets[bucket]] == NULL)
        << "Congratulations, you found a Ceres bug! Please report this error "
        << "to the developers.";

    reordered_residual_blocks[offsets[bucket]] = (*residual_blocks)[i];
  }

  // Sanity check #1: The difference in bucket offsets should match the
  // histogram sizes.
  for (int i = 0; i < num_eliminate_blocks; ++i) {
    CHECK_EQ(residual_blocks_per_e_block[i], offsets[i + 1] - offsets[i])
        << "Congratulations, you found a Ceres bug! Please report this error "
        << "to the developers.";
  }
  // Sanity check #2: No NULL's left behind.
  for (int i = 0; i < reordered_residual_blocks.size(); ++i) {
    CHECK(reordered_residual_blocks[i] != NULL)
        << "Congratulations, you found a Ceres bug! Please report this error "
        << "to the developers.";
  }

  // Now that the residuals are collected by E block, swap them in place.
  swap(*program->mutable_residual_blocks(), reordered_residual_blocks);
  return true;
}

Evaluator* SolverImpl::CreateEvaluator(
    const Solver::Options& options,
    const ProblemImpl::ParameterMap& parameter_map,
    Program* program,
    string* error) {
  Evaluator::Options evaluator_options;
  evaluator_options.linear_solver_type = options.linear_solver_type;
  evaluator_options.num_eliminate_blocks =
      (options.linear_solver_ordering->NumGroups() > 0 &&
       IsSchurType(options.linear_solver_type))
      ? (options.linear_solver_ordering
         ->group_to_elements().begin()
         ->second.size())
      : 0;
  evaluator_options.num_threads = options.num_threads;
  return Evaluator::Create(evaluator_options, program, error);
}

CoordinateDescentMinimizer* SolverImpl::CreateInnerIterationMinimizer(
    const Solver::Options& options,
    const Program& program,
    const ProblemImpl::ParameterMap& parameter_map,
    Solver::Summary* summary) {
  scoped_ptr<CoordinateDescentMinimizer> inner_iteration_minimizer(
      new CoordinateDescentMinimizer);
  scoped_ptr<ParameterBlockOrdering> inner_iteration_ordering;
  ParameterBlockOrdering* ordering_ptr  = NULL;

  if (options.inner_iteration_ordering == NULL) {
    // Find a recursive decomposition of the Hessian matrix as a set
    // of independent sets of decreasing size and invert it. This
    // seems to work better in practice, i.e., Cameras before
    // points.
    inner_iteration_ordering.reset(new ParameterBlockOrdering);
    ComputeRecursiveIndependentSetOrdering(program,
                                           inner_iteration_ordering.get());
    inner_iteration_ordering->Reverse();
    ordering_ptr = inner_iteration_ordering.get();
  } else {
    const map<int, set<double*> >& group_to_elements =
        options.inner_iteration_ordering->group_to_elements();

    // Iterate over each group and verify that it is an independent
    // set.
    map<int, set<double*> >::const_iterator it = group_to_elements.begin();
    for ( ; it != group_to_elements.end(); ++it) {
      if (!IsParameterBlockSetIndependent(it->second,
                                          program.residual_blocks())) {
        summary->error =
            StringPrintf("The user-provided "
                         "parameter_blocks_for_inner_iterations does not "
                         "form an independent set. Group Id: %d", it->first);
        return NULL;
      }
    }
    ordering_ptr = options.inner_iteration_ordering;
  }

  if (!inner_iteration_minimizer->Init(program,
                                       parameter_map,
                                       *ordering_ptr,
                                       &summary->error)) {
    return NULL;
  }

  summary->inner_iterations = true;
  SummarizeOrdering(ordering_ptr, &(summary->inner_iteration_ordering_used));

  return inner_iteration_minimizer.release();
}

}  // namespace internal
}  // namespace ceres
