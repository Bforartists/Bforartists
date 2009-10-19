/**
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * BKE_bad_level_calls function stubs
 */

#include <stdlib.h>
#include "DNA_listBase.h"
#include "RNA_types.h"

/*new render funcs */
float *RE_RenderLayerGetPass(struct RenderLayer *rl, int passtype) {return NULL;}
float RE_filter_value(int type, float x) {return 0.0f;}
struct RenderLayer *RE_GetRenderLayer(struct RenderResult *rr, const char *name) {return (struct RenderLayer *)NULL;}

/* zbuf.c stub */
void antialias_tagbuf(int xsize, int ysize, char *rectmove) {}
void RE_zbuf_accumulate_vecblur(struct NodeBlurData *nbd, int xsize, int ysize, float *newrect, float *imgrect, float *vecbufrect, float *zbufrect) {}

/* imagetexture.c stub */
void ibuf_sample(struct ImBuf *ibuf, float fx, float fy, float dx, float dy, float *result) {}

/* texture.c */
int multitex_thread(struct Tex *tex, float *texvec, float *dxt, float *dyt, int osatex, struct TexResult *texres, short thread, short which_output) {return 0;}
int multitex_ext(struct Tex *tex, float *texvec, float *dxt, float *dyt, int osatex, struct TexResult *texres){return 0;}

/* nodes */
struct RenderResult *RE_GetResult(struct Render *re){return (struct RenderResult *) NULL;}
struct Render *RE_GetRender(const char *name){return (struct Render *) NULL;}

/* blenkernel */
char* btempdir(){return NULL;}
void RE_FreeRenderResult(struct RenderResult *res){}
char* datatoc_bmonofont_ttf(){return NULL;}
int datatoc_bmonofont_ttf_size(){return 0;}
struct RenderResult *RE_MultilayerConvert(void *exrhandle, int rectx, int recty){return (struct RenderResult *) NULL;}
void RE_GetResultImage(struct Render *re, struct RenderResult *rr){}
int RE_RenderInProgress(struct Render *re){return 0;}
struct Scene *RE_GetScene(struct Render *re){return (struct Scene *) NULL;}
void RE_Database_Free(struct Render *re){}
void RE_FreeRender(struct Render *re){}
void RE_shade_external(struct Render *re, struct ShadeInput *shi, struct ShadeResult *shr){}
void RE_DataBase_GetView(struct Render *re, float mat[][4]){}
int externtex(struct MTex *mtex, float *vec, float *tin, float *tr, float *tg, float *tb, float *ta){return 0;}
float texture_value_blend(float tex, float out, float fact, float facg, int blendtype, int flip){return 0.0f;}
void texture_rgb_blend(float *in, float *tex, float *out, float fact, float facg, int blendtype){}
char stipple_quarttone[1]; //GLubyte stipple_quarttone[128]
double elbeemEstimateMemreq(int res, float sx, float sy, float sz, int refine, char *retstr) {return 0.0f;}

/* rna */
void WM_event_add_notifier(const struct bContext *C, unsigned int type, void *reference){}
void ED_armature_bone_rename(struct bArmature *arm, char *oldnamep, char *newnamep){}
void object_test_constraints (struct Object *owner){}
void ED_object_parent(struct Object *ob, struct Object *par, int type, const char *substr){}
void ED_node_composit_default(struct Scene *sce){}

struct EditBone *ED_armature_bone_get_mirrored(struct ListBase *edbo, struct EditBone *ebo){return (struct EditBone *) NULL;}
struct ListBase *get_active_constraints (struct Object *ob){return (struct ListBase *) NULL;}
int ED_pose_channel_in_IK_chain(struct Object *ob, struct bPoseChannel *pchan){return 0;}

int ED_space_image_show_uvedit(struct SpaceImage *sima, struct Object *obedit){return 0;}
int ED_space_image_show_render(struct SpaceImage *sima){return 0;}
int ED_space_image_show_paint(struct SpaceImage *sima){return 0;}
void ED_space_image_set(struct bContext *C, struct SpaceImage *sima, struct Scene *scene, struct Object *obedit, struct Image *ima){}
struct ImBuf *ED_space_image_buffer(struct SpaceImage *sima){return (struct ImBuf *) NULL;}

struct PTCacheEdit *PE_get_current(struct Scene *scene, struct Object *ob){return (struct PTCacheEdit *) NULL;}

/* rna editors */
char *ED_info_stats_string(struct Scene *scene){return NULL;}
void ED_area_tag_redraw(struct ScrArea *sa){}
void WM_event_add_fileselect(struct bContext *C, struct wmOperator *op){}
void ED_node_texture_default(struct Tex *tx){}
int text_file_modified(struct Text *text){return 0;}
void ED_node_shader_default(struct Material *ma){}
void ED_screen_animation_timer_update(struct bContext *C, int redraws){}
int ED_object_modifier_remove(struct ReportList *reports, struct Scene *scene, struct Object *ob, struct ModifierData *md){return 0;}
int ED_object_modifier_add(struct ReportList *reports, struct Scene *scene, struct Object *ob, int type){return 0;}
int uiLayoutGetActive(struct uiLayout *layout){return 0;}
int uiLayoutGetOperatorContext(struct uiLayout *layout){return 0;}
int uiLayoutGetAlignment(struct uiLayout *layout){return 0;}
int uiLayoutGetEnabled(struct uiLayout *layout){return 0;}
float uiLayoutGetScaleX(struct uiLayout *layout){return 0.0f;}
float uiLayoutGetScaleY(struct uiLayout *layout){return 0.0f;}
void uiLayoutSetActive(struct uiLayout *layout, int active){}
void uiLayoutSetOperatorContext(struct uiLayout *layout, int opcontext){}
void uiLayoutSetEnabled(struct uiLayout *layout, int enabled){}
void uiLayoutSetAlignment(struct uiLayout *layout, int alignment){}
void uiLayoutSetScaleX(struct uiLayout *layout, float scale){}
void uiLayoutSetScaleY(struct uiLayout *layout, float scale){}

void uiItemR(struct uiLayout *layout, char *name, int icon, struct PointerRNA *ptr, char *propname, int flag){}

PointerRNA uiItemFullO(struct uiLayout *layout, char *name, int icon, char *idname, struct IDProperty *properties, int context, int flag){PointerRNA a; return a;}
struct uiLayout *uiLayoutRow(struct uiLayout *layout, int align){return (struct uiLayout *) NULL;}
struct uiLayout *uiLayoutColumn(struct uiLayout *layout, int align){return (struct uiLayout *) NULL;}
struct uiLayout *uiLayoutColumnFlow(struct uiLayout *layout, int number, int align){return (struct uiLayout *) NULL;}
struct uiLayout *uiLayoutBox(struct uiLayout *layout){return (struct uiLayout *) NULL;}
struct uiLayout *uiLayoutSplit(struct uiLayout *layout, float percentage){return (struct uiLayout *) NULL;}
void uiItemsEnumR(struct uiLayout *layout, struct PointerRNA *ptr, char *propname){}
void uiItemMenuEnumR(struct uiLayout *layout, char *name, int icon, struct PointerRNA *ptr, char *propname){}
void uiItemEnumR_string(struct uiLayout *layout, char *name, int icon, struct PointerRNA *ptr, char *propname, char *value){}
void uiItemPointerR(struct uiLayout *layout, char *name, int icon, struct PointerRNA *ptr, char *propname, struct PointerRNA *searchptr, char *searchpropname){}
void uiItemsEnumO(struct uiLayout *layout, char *opname, char *propname){}
void uiItemEnumO_string(struct uiLayout *layout, char *name, int icon, char *opname, char *propname, char *value_str){}
void uiItemMenuEnumO(struct uiLayout *layout, char *name, int icon, char *opname, char *propname){}
void uiItemBooleanO(struct uiLayout *layout, char *name, int icon, char *opname, char *propname, int value){}
void uiItemIntO(struct uiLayout *layout, char *name, int icon, char *opname, char *propname, int value){}
void uiItemFloatO(struct uiLayout *layout, char *name, int icon, char *opname, char *propname, float value){}
void uiItemStringO(struct uiLayout *layout, char *name, int icon, char *opname, char *propname, char *value){}
void uiItemL(struct uiLayout *layout, char *name, int icon){}
void uiItemM(struct uiLayout *layout, struct bContext *C, char *name, int icon, char *menuname){}
void uiItemS(struct uiLayout *layout){}
void uiLayoutSetContextPointer(struct uiLayout *layout, char *name, struct PointerRNA *ptr){}

/* rna template */
void uiTemplateHeader(struct uiLayout *layout, struct bContext *C, int menus){}
void uiTemplateID(struct uiLayout *layout, struct bContext *C, struct PointerRNA *ptr, char *propname, char *newop, char *unlinkop){}
struct uiLayout *uiTemplateModifier(struct uiLayout *layout, struct PointerRNA *ptr){return (struct uiLayout *) NULL;}
struct uiLayout *uiTemplateConstraint(struct uiLayout *layout, struct PointerRNA *ptr){return (struct uiLayout *) NULL;}
void uiTemplatePreview(struct uiLayout *layout, struct ID *id, struct ID *parent, struct MTex *slot){}
void uiTemplateCurveMapping(struct uiLayout *layout, struct CurveMapping *cumap, int type, int compact){}
void uiTemplateColorRamp(struct uiLayout *layout, struct ColorBand *coba, int expand){}
void uiTemplateLayers(struct uiLayout *layout, struct PointerRNA *ptr, char *propname){}
void uiTemplateTriColorSet(struct uiLayout *layout, struct PointerRNA *ptr, char *propname){}
void uiTemplateImageLayers(struct uiLayout *layout, struct bContext *C, struct Image *ima, struct ImageUser *iuser){}
ListBase uiTemplateList(struct uiLayout *layout, struct bContext *C, struct PointerRNA *ptr, char *propname, struct PointerRNA *activeptr, char *activepropname, int rows, int listtype){struct ListBase b = {0,0}; return b;}
void uiTemplateRunningJobs(struct uiLayout *layout, struct bContext *C){}
void uiTemplateOperatorSearch(struct uiLayout *layout){}
void uiTemplateHeader3D(struct uiLayout *layout, struct bContext *C){}
void uiTemplate_view3d_select_faceselmenu(struct uiLayout *layout, struct bContext *C){}
void uiTemplateTextureImage(struct uiLayout *layout, struct bContext *C, struct Tex *tex){}

/* rna render */
struct RenderResult *RE_engine_begin_result(struct RenderEngine *engine, int x, int y, int w, int h){return (struct RenderResult *) NULL;}
void RE_engine_update_result(struct RenderEngine *engine, struct RenderResult *result){}
void RE_engine_end_result(struct RenderEngine *engine, struct RenderResult *result){}
void RE_engine_update_stats(struct RenderEngine *engine, char *stats, char *info){}
void RE_layer_load_from_file(struct RenderLayer *layer, struct ReportList *reports, char *filename){}
void RE_result_load_from_file(struct RenderResult *result, struct ReportList *reports, char *filename){}
int RE_engine_test_break(struct RenderEngine *engine){return 0;}

/* python */
struct wmOperatorType *WM_operatortype_find(const char *idname, int quiet){return (struct wmOperatorType *) NULL;}
struct wmOperatorType *WM_operatortype_first(){return (struct wmOperatorType *) NULL;}
struct wmOperatorType *WM_operatortype_exists(const char *idname){return (struct wmOperatorType *) NULL;}
int WM_operator_call_py(struct bContext *C, struct wmOperatorType *ot, int context, struct PointerRNA *properties, struct ReportList *reports){return 0;}
int WM_operatortype_remove(const char *idname){return 0;}
void WM_operator_properties_free(struct PointerRNA *ptr){}
void WM_operator_properties_create(struct PointerRNA *ptr, const char *opstring){}
void WM_operatortype_append_ptr(void (*opfunc)(struct wmOperatorType*, void*), void *userdata){}
void WM_operator_bl_idname(char *to, const char *from){}
short insert_keyframe (struct ID *id, struct bAction *act, const char group[], const char rna_path[], int array_index, float cfra, short flag){return 0;}

/* smoke */
void lzo1x_1_compress(void) {return;};
void LzmaCompress(void) {return;};
void smoke_export(void) {return;};
void lzo1x_decompress(void) {return;};
void LzmaUncompress(void) {return;};
void smoke_init(void) {return;};
void smoke_turbulence_init(void) {return;};
void smoke_turbulence_initBlenderRNA(void) {return;};
void smoke_initBlenderRNA(void) {return;};
void smoke_free(void) {return;};
void smoke_turbulence_free(void) {return;};
void smoke_turbulence_step(void) {return;};
void smoke_dissolve(void) {return;};
void smoke_get_density(void) {return;};
void smoke_get_heat(void) {return;};
void smoke_get_velocity_x(void) {return;};
void smoke_get_velocity_y(void) {return;};
void smoke_get_velocity_z(void) {return;};
void smoke_get_obstacle(void) {return;};
void smoke_get_index(void) {return;};
void smoke_step(void) {return;};
