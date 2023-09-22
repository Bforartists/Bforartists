/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#pragma once

/* so modifier types match their defines */
#include "MOD_modifiertypes.hh"

#include "DEG_depsgraph_build.hh"

struct MDeformVert;
struct Mesh;
struct ModifierData;
struct ModifierEvalContext;
struct Object;

void MOD_init_texture(MappingInfoModifierData *dmd, const ModifierEvalContext *ctx);
/**
 * \param cos: may be null, in which case we use directly mesh vertices' coordinates.
 */
void MOD_get_texture_coords(MappingInfoModifierData *dmd,
                            const ModifierEvalContext *ctx,
                            Object *ob,
                            Mesh *mesh,
                            float (*cos)[3],
                            float (*r_texco)[3]);

void MOD_previous_vcos_store(ModifierData *md, const float (*vert_coords)[3]);

void MOD_get_vgroup(const Object *ob,
                    const Mesh *mesh,
                    const char *name,
                    const MDeformVert **dvert,
                    int *defgrp_index);

void MOD_depsgraph_update_object_bone_relation(DepsNodeHandle *node,
                                               Object *object,
                                               const char *bonename,
                                               const char *description);
