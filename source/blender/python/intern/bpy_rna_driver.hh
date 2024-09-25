/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup pythonintern
 */

struct AnimationEvalContext;
struct ChannelDriver;
struct DriverTarget;
struct DriverVar;
struct PathResolvedRNA;

/**
 * A version of #driver_get_variable_value which returns a #PyObject.
 */
PyObject *pyrna_driver_get_variable_value(const AnimationEvalContext *anim_eval_context,
                                          ChannelDriver *driver,
                                          DriverVar *dvar,
                                          DriverTarget *dtar);

PyObject *pyrna_driver_self_from_anim_rna(PathResolvedRNA *anim_rna);
bool pyrna_driver_is_equal_anim_rna(const PathResolvedRNA *anim_rna, const PyObject *py_anim_rna);
