/* SPDX-FileCopyrightText: 2016 Kévin Dietrich. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

/** \file
 * \ingroup balembic
 */

#include "abc_writer_abstract.h"

#include <Alembic/AbcGeom/OPoints.h>

namespace blender::io::alembic {

class ABCPointsWriter : public ABCAbstractWriter {
  Alembic::AbcGeom::OPoints abc_points_;
  Alembic::AbcGeom::OPointsSchema abc_points_schema_;

 public:
  explicit ABCPointsWriter(const ABCWriterConstructorArgs &args);

  void create_alembic_objects(const HierarchyContext *context) override;
  Alembic::Abc::OObject get_alembic_object() const override;
  Alembic::Abc::OCompoundProperty abc_prop_for_custom_props() override;

  bool is_supported(const HierarchyContext *context) const override;

 protected:
  bool check_is_animated(const HierarchyContext &context) const override;
  void do_write(HierarchyContext &context) override;
};

}  // namespace blender::io::alembic
