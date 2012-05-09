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
// Author: sameeragarwal@google.com (Sameer Agarwal)

#include "ceres/block_sparse_matrix.h"

#include <cstddef>
#include <algorithm>
#include <vector>
#include <glog/logging.h>
#include "ceres/block_structure.h"
#include "ceres/matrix_proto.h"
#include "ceres/triplet_sparse_matrix.h"
#include "ceres/internal/eigen.h"

namespace ceres {
namespace internal {

BlockSparseMatrix::~BlockSparseMatrix() {}

BlockSparseMatrix::BlockSparseMatrix(
    CompressedRowBlockStructure* block_structure)
    : num_rows_(0),
      num_cols_(0),
      num_nonzeros_(0),
      values_(NULL),
      block_structure_(block_structure) {
  CHECK_NOTNULL(block_structure_.get());

  // Count the number of columns in the matrix.
  for (int i = 0; i < block_structure_->cols.size(); ++i) {
    num_cols_ += block_structure_->cols[i].size;
  }

  // Count the number of non-zero entries and the number of rows in
  // the matrix.
  for (int i = 0; i < block_structure_->rows.size(); ++i) {
    int row_block_size = block_structure_->rows[i].block.size;
    num_rows_ += row_block_size;

    const vector<Cell>& cells = block_structure_->rows[i].cells;
    for (int j = 0; j < cells.size(); ++j) {
      int col_block_id = cells[j].block_id;
      int col_block_size = block_structure_->cols[col_block_id].size;
      num_nonzeros_ += col_block_size * row_block_size;
    }
  }

  CHECK_GE(num_rows_, 0);
  CHECK_GE(num_cols_, 0);
  CHECK_GE(num_nonzeros_, 0);
  VLOG(2) << "Allocating values array with "
          << num_nonzeros_ * sizeof(double) << " bytes.";  // NOLINT
  values_.reset(new double[num_nonzeros_]);
  CHECK_NOTNULL(values_.get());
}

#ifndef CERES_DONT_HAVE_PROTOCOL_BUFFERS
BlockSparseMatrix::BlockSparseMatrix(const SparseMatrixProto& outer_proto) {
  CHECK(outer_proto.has_block_matrix());

  const BlockSparseMatrixProto& proto = outer_proto.block_matrix();
  CHECK(proto.has_num_rows());
  CHECK(proto.has_num_cols());
  CHECK_EQ(proto.num_nonzeros(), proto.values_size());

  num_rows_ = proto.num_rows();
  num_cols_ = proto.num_cols();
  num_nonzeros_ = proto.num_nonzeros();

  // Copy out the values into *this.
  values_.reset(new double[num_nonzeros_]);
  for (int i = 0; i < proto.num_nonzeros(); ++i) {
    values_[i] = proto.values(i);
  }

  // Create the block structure according to the proto.
  block_structure_.reset(new CompressedRowBlockStructure);
  ProtoToBlockStructure(proto.block_structure(), block_structure_.get());
}
#endif

void BlockSparseMatrix::SetZero() {
  fill(values_.get(), values_.get() + num_nonzeros_, 0.0);
}

void BlockSparseMatrix::RightMultiply(const double* x,  double* y) const {
  CHECK_NOTNULL(x);
  CHECK_NOTNULL(y);

  for (int i = 0; i < block_structure_->rows.size(); ++i) {
    int row_block_pos = block_structure_->rows[i].block.position;
    int row_block_size = block_structure_->rows[i].block.size;
    VectorRef yref(y + row_block_pos, row_block_size);
    const vector<Cell>& cells = block_structure_->rows[i].cells;
    for (int j = 0; j < cells.size(); ++j) {
      int col_block_id = cells[j].block_id;
      int col_block_size = block_structure_->cols[col_block_id].size;
      int col_block_pos = block_structure_->cols[col_block_id].position;
      ConstVectorRef xref(x + col_block_pos, col_block_size);
      MatrixRef m(values_.get() + cells[j].position,
                  row_block_size, col_block_size);
      yref += m.lazyProduct(xref);
    }
  }
}

void BlockSparseMatrix::LeftMultiply(const double* x, double* y) const {
  CHECK_NOTNULL(x);
  CHECK_NOTNULL(y);

  for (int i = 0; i < block_structure_->rows.size(); ++i) {
    int row_block_pos = block_structure_->rows[i].block.position;
    int row_block_size = block_structure_->rows[i].block.size;
    const ConstVectorRef xref(x + row_block_pos, row_block_size);
    const vector<Cell>& cells = block_structure_->rows[i].cells;
    for (int j = 0; j < cells.size(); ++j) {
      int col_block_id = cells[j].block_id;
      int col_block_size = block_structure_->cols[col_block_id].size;
      int col_block_pos = block_structure_->cols[col_block_id].position;
      VectorRef yref(y + col_block_pos, col_block_size);
      MatrixRef m(values_.get() + cells[j].position,
                  row_block_size, col_block_size);
      yref += m.transpose().lazyProduct(xref);
    }
  }
}

void BlockSparseMatrix::SquaredColumnNorm(double* x) const {
  CHECK_NOTNULL(x);
  VectorRef(x, num_cols_).setZero();
  for (int i = 0; i < block_structure_->rows.size(); ++i) {
    int row_block_size = block_structure_->rows[i].block.size;
    const vector<Cell>& cells = block_structure_->rows[i].cells;
    for (int j = 0; j < cells.size(); ++j) {
      int col_block_id = cells[j].block_id;
      int col_block_size = block_structure_->cols[col_block_id].size;
      int col_block_pos = block_structure_->cols[col_block_id].position;
      const MatrixRef m(values_.get() + cells[j].position,
                        row_block_size, col_block_size);
      VectorRef(x + col_block_pos, col_block_size) += m.colwise().squaredNorm();
    }
  }
}

void BlockSparseMatrix::ScaleColumns(const double* scale) {
  CHECK_NOTNULL(scale);

  for (int i = 0; i < block_structure_->rows.size(); ++i) {
    int row_block_size = block_structure_->rows[i].block.size;
    const vector<Cell>& cells = block_structure_->rows[i].cells;
    for (int j = 0; j < cells.size(); ++j) {
      int col_block_id = cells[j].block_id;
      int col_block_size = block_structure_->cols[col_block_id].size;
      int col_block_pos = block_structure_->cols[col_block_id].position;
      MatrixRef m(values_.get() + cells[j].position,
                        row_block_size, col_block_size);
      m *= ConstVectorRef(scale + col_block_pos, col_block_size).asDiagonal();
    }
  }
}

void BlockSparseMatrix::ToDenseMatrix(Matrix* dense_matrix) const {
  CHECK_NOTNULL(dense_matrix);

  dense_matrix->resize(num_rows_, num_cols_);
  dense_matrix->setZero();
  Matrix& m = *dense_matrix;

  for (int i = 0; i < block_structure_->rows.size(); ++i) {
    int row_block_pos = block_structure_->rows[i].block.position;
    int row_block_size = block_structure_->rows[i].block.size;
    const vector<Cell>& cells = block_structure_->rows[i].cells;
    for (int j = 0; j < cells.size(); ++j) {
      int col_block_id = cells[j].block_id;
      int col_block_size = block_structure_->cols[col_block_id].size;
      int col_block_pos = block_structure_->cols[col_block_id].position;
      int jac_pos = cells[j].position;
      m.block(row_block_pos, col_block_pos, row_block_size, col_block_size)
          += MatrixRef(values_.get() + jac_pos, row_block_size, col_block_size);
    }
  }
}

void BlockSparseMatrix::ToTripletSparseMatrix(
    TripletSparseMatrix* matrix) const {
  CHECK_NOTNULL(matrix);

  matrix->Reserve(num_nonzeros_);
  matrix->Resize(num_rows_, num_cols_);
  matrix->SetZero();

  for (int i = 0; i < block_structure_->rows.size(); ++i) {
    int row_block_pos = block_structure_->rows[i].block.position;
    int row_block_size = block_structure_->rows[i].block.size;
    const vector<Cell>& cells = block_structure_->rows[i].cells;
    for (int j = 0; j < cells.size(); ++j) {
      int col_block_id = cells[j].block_id;
      int col_block_size = block_structure_->cols[col_block_id].size;
      int col_block_pos = block_structure_->cols[col_block_id].position;
      int jac_pos = cells[j].position;
       for (int r = 0; r < row_block_size; ++r) {
        for (int c = 0; c < col_block_size; ++c, ++jac_pos) {
          matrix->mutable_rows()[jac_pos] = row_block_pos + r;
          matrix->mutable_cols()[jac_pos] = col_block_pos + c;
          matrix->mutable_values()[jac_pos] = values_[jac_pos];
        }
      }
    }
  }
  matrix->set_num_nonzeros(num_nonzeros_);
}

// Return a pointer to the block structure. We continue to hold
// ownership of the object though.
const CompressedRowBlockStructure* BlockSparseMatrix::block_structure()
    const {
  return block_structure_.get();
}

#ifndef CERES_DONT_HAVE_PROTOCOL_BUFFERS
void BlockSparseMatrix::ToProto(SparseMatrixProto* outer_proto) const {
  outer_proto->Clear();

  BlockSparseMatrixProto* proto = outer_proto->mutable_block_matrix();
  proto->set_num_rows(num_rows_);
  proto->set_num_cols(num_cols_);
  proto->set_num_nonzeros(num_nonzeros_);
  for (int i = 0; i < num_nonzeros_; ++i) {
    proto->add_values(values_[i]);
  }
  BlockStructureToProto(*block_structure_, proto->mutable_block_structure());
}
#endif

}  // namespace internal
}  // namespace ceres
