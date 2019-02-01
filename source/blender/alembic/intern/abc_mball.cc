/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#include "abc_mball.h"
#include "abc_mesh.h"
#include "abc_transform.h"

extern "C" {
#include "DNA_meta_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"

#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_displist.h"
#include "BKE_main.h"
#include "BKE_mball.h"
#include "BKE_mesh.h"
#include "BKE_object.h"

#include "DEG_depsgraph.h"
#include "MEM_guardedalloc.h"
}

AbcMBallWriter::AbcMBallWriter(
        Main *bmain,
        Scene *scene,
        Object *ob,
        AbcTransformWriter *parent,
        uint32_t time_sampling,
        ExportSettings &settings)
    : AbcObjectWriter(scene, ob, time_sampling, settings, parent)
    , m_bmain(bmain)
{
	m_is_animated = isAnimated();

	m_mesh_ob = BKE_object_copy(bmain, ob);
	m_mesh_ob->curve_cache = (CurveCache *)MEM_callocN(
	                             sizeof(CurveCache),
	                             "CurveCache for AbcMBallWriter");

	m_mesh_writer = new AbcMeshWriter(scene, m_mesh_ob, parent,
	                                  time_sampling, settings);
	m_mesh_writer->setIsAnimated(m_is_animated);
}


AbcMBallWriter::~AbcMBallWriter()
{
	delete m_mesh_writer;
	BKE_object_free(m_mesh_ob);
}

bool AbcMBallWriter::isAnimated() const
{
	MetaBall *mb = static_cast<MetaBall *>(m_object->data);
	if (mb->adt != NULL) return true;

	/* Any movement of any object in the parent chain
	 * could cause the mball to deform. */
	for (Object *ob = m_object; ob != NULL; ob = ob->parent) {
		if (ob->adt != NULL) return true;
	}
	return false;
}

void AbcMBallWriter::do_write()
{
	/* We have already stored a sample for this object. */
	if (!m_first_frame && !m_is_animated)
		return;

	Mesh *tmpmesh = BKE_mesh_add(m_bmain, ((ID *)m_object->data)->name + 2);
	BLI_assert(tmpmesh != NULL);
	m_mesh_ob->data = tmpmesh;

	/* BKE_mesh_add gives us a user count we don't need */
	id_us_min(&tmpmesh->id);

	ListBase disp = {NULL, NULL};
	/* TODO(sergey): This is gonna to work for until EvaluationContext
	 *               only contains for_render flag. As soon as CoW is
	 *               implemented, this is to be rethinked.
	 */
	EvaluationContext eval_ctx;
	DEG_evaluation_context_init(&eval_ctx, DAG_EVAL_RENDER);
	BKE_displist_make_mball_forRender(m_bmain, &eval_ctx, m_scene, m_object, &disp);
	BKE_mesh_from_metaball(&disp, tmpmesh);
	BKE_displist_free(&disp);

	BKE_mesh_texspace_copy_from_object(tmpmesh, m_mesh_ob);

	m_mesh_writer->write();

	BKE_id_free(m_bmain, tmpmesh);
	m_mesh_ob->data = NULL;
}

bool AbcMBallWriter::isBasisBall(Main *bmain, EvaluationContext *eval_ctx, Scene *scene, Object *ob)
{
	Object *basis_ob = BKE_mball_basis_find(bmain, eval_ctx, scene, ob);
	return ob == basis_ob;
}
