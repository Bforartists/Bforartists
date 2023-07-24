/* SPDX-FileCopyrightText: 2018 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup shader_fx
 */

#include <cstdio>

#include "DNA_gpencil_legacy_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"

#include "BLI_math_base.h"
#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "BKE_context.h"
#include "BKE_lib_query.h"
#include "BKE_modifier.h"
#include "BKE_screen.h"
#include "BKE_shader_fx.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "RNA_access.h"

#include "FX_shader_types.h"
#include "FX_ui_common.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"

static void initData(ShaderFxData *md)
{
  SwirlShaderFxData *gpmd = (SwirlShaderFxData *)md;
  gpmd->radius = 100;
  gpmd->angle = M_PI_2;
}

static void copyData(const ShaderFxData *md, ShaderFxData *target)
{
  BKE_shaderfx_copydata_generic(md, target);
}

static void updateDepsgraph(ShaderFxData *fx, const ModifierUpdateDepsgraphContext *ctx)
{
  SwirlShaderFxData *fxd = (SwirlShaderFxData *)fx;
  if (fxd->object != nullptr) {
    DEG_add_object_relation(ctx->node, fxd->object, DEG_OB_COMP_TRANSFORM, "Swirl ShaderFx");
  }
  DEG_add_object_relation(ctx->node, ctx->object, DEG_OB_COMP_TRANSFORM, "Swirl ShaderFx");
}

static bool isDisabled(ShaderFxData *fx, int /*userRenderParams*/)
{
  SwirlShaderFxData *fxd = (SwirlShaderFxData *)fx;

  return !fxd->object;
}

static void foreachIDLink(ShaderFxData *fx, Object *ob, IDWalkFunc walk, void *userData)
{
  SwirlShaderFxData *fxd = (SwirlShaderFxData *)fx;

  walk(userData, ob, (ID **)&fxd->object, IDWALK_CB_NOP);
}

static void panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = shaderfx_panel_get_property_pointers(panel, nullptr);

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "object", 0, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "radius", 0, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "angle", 0, nullptr, ICON_NONE);

  shaderfx_panel_end(layout, ptr);
}

static void panelRegister(ARegionType *region_type)
{
  shaderfx_panel_register(region_type, eShaderFxType_Swirl, panel_draw);
}

ShaderFxTypeInfo shaderfx_Type_Swirl = {
    /*name*/ N_("Swirl"),
    /*struct_name*/ "SwirlShaderFxData",
    /*struct_size*/ sizeof(SwirlShaderFxData),
    /*type*/ eShaderFxType_GpencilType,
    /*flags*/ ShaderFxTypeFlag(0),

    /*copyData*/ copyData,

    /*initData*/ initData,
    /*freeData*/ nullptr,
    /*isDisabled*/ isDisabled,
    /*updateDepsgraph*/ updateDepsgraph,
    /*dependsOnTime*/ nullptr,
    /*foreachIDLink*/ foreachIDLink,
    /*panelRegister*/ panelRegister,
};
