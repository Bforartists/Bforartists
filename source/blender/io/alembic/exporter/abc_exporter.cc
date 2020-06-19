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

/** \file
 * \ingroup balembic
 */

#include "abc_exporter.h"

#include <cmath>

#include "abc_writer_archive.h"
#include "abc_writer_camera.h"
#include "abc_writer_curves.h"
#include "abc_writer_hair.h"
#include "abc_writer_mball.h"
#include "abc_writer_mesh.h"
#include "abc_writer_nurbs.h"
#include "abc_writer_points.h"
#include "abc_writer_transform.h"
#include "intern/abc_util.h"

#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_fluid_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h" /* for FILE_MAX */

#include "BLI_string.h"

#ifdef WIN32
/* needed for MSCV because of snprintf from BLI_string */
#  include "BLI_winstuff.h"
#endif

#include "BKE_duplilist.h"
#include "BKE_global.h"
#include "BKE_idprop.h"
#include "BKE_layer.h"
#include "BKE_main.h"
#include "BKE_mball.h"
#include "BKE_modifier.h"
#include "BKE_particle.h"
#include "BKE_scene.h"

#include "DEG_depsgraph_query.h"

using Alembic::Abc::OBox3dProperty;
using Alembic::Abc::TimeSamplingPtr;

/* ************************************************************************** */

namespace blender {
namespace io {
namespace alembic {

ExportSettings::ExportSettings()
    : scene(NULL),
      view_layer(NULL),
      depsgraph(NULL),
      logger(),
      selected_only(false),
      visible_objects_only(false),
      renderable_only(false),
      frame_start(1),
      frame_end(1),
      frame_samples_xform(1),
      frame_samples_shape(1),
      shutter_open(0.0),
      shutter_close(1.0),
      global_scale(1.0f),
      flatten_hierarchy(false),
      export_normals(false),
      export_uvs(false),
      export_vcols(false),
      export_face_sets(false),
      export_vweigths(false),
      export_hair(true),
      export_particles(true),
      apply_subdiv(false),
      use_subdiv_schema(false),
      export_child_hairs(true),
      pack_uv(false),
      triangulate(false),
      quad_method(0),
      ngon_method(0)
{
}

static bool object_is_smoke_sim(Object *ob)
{
  ModifierData *md = BKE_modifiers_findby_type(ob, eModifierType_Fluid);

  if (md) {
    FluidModifierData *smd = reinterpret_cast<FluidModifierData *>(md);
    return (smd->type == MOD_FLUID_TYPE_DOMAIN && smd->domain &&
            smd->domain->type == FLUID_DOMAIN_TYPE_GAS);
  }

  return false;
}

static bool object_type_is_exportable(Scene *scene, Object *ob)
{
  switch (ob->type) {
    case OB_MESH:
      if (object_is_smoke_sim(ob)) {
        return false;
      }

      return true;
    case OB_EMPTY:
    case OB_CURVE:
    case OB_SURF:
    case OB_CAMERA:
      return true;
    case OB_MBALL:
      return AbcMBallWriter::isBasisBall(scene, ob);
    default:
      return false;
  }
}

/**
 * Returns whether this object should be exported into the Alembic file.
 *
 * \param settings: export settings, used for options like 'selected only'.
 * \param ob: the object's base in question.
 * \param is_duplicated: Normally false; true when the object is instanced
 * into the scene by a dupli-object (e.g. part of a dupligroup).
 * This ignores selection and layer visibility,
 * and assumes that the dupli-object itself (e.g. the group-instantiating empty) is exported.
 */
static bool export_object(const ExportSettings *const settings,
                          const Base *const base,
                          bool is_duplicated)
{
  if (!is_duplicated) {
    View3D *v3d = NULL;

    /* These two tests only make sense when the object isn't being instanced
     * into the scene. When it is, its exportability is determined by
     * its dupli-object and the DupliObject::no_draw property. */
    if (settings->selected_only && !BASE_SELECTED(v3d, base)) {
      return false;
    }
    // FIXME Sybren: handle these cleanly (maybe just remove code),
    // now using active scene layer instead.
    if (settings->visible_objects_only && !BASE_VISIBLE(v3d, base)) {
      return false;
    }
  }

  Object *ob_eval = DEG_get_evaluated_object(settings->depsgraph, base->object);
  if ((ob_eval->id.tag & LIB_TAG_COPIED_ON_WRITE) == 0) {
    /* XXX fix after 2.80: the object was not part of the depsgraph, and thus we cannot get the
     * evaluated copy to export. This will be handled more elegantly in the new
     * AbstractHierarchyIterator that Sybren is working on. This condition is temporary, and avoids
     * a BLI_assert() failure getting the evaluated mesh of this object. */
    return false;
  }

  //  if (settings->renderable_only && (ob->restrictflag & OB_RESTRICT_RENDER)) {
  //      return false;
  //  }

  return true;
}

/* ************************************************************************** */

AbcExporter::AbcExporter(Main *bmain, const char *filename, ExportSettings &settings)
    : m_bmain(bmain),
      m_settings(settings),
      m_filename(filename),
      m_trans_sampling_index(0),
      m_shape_sampling_index(0),
      m_writer(NULL)
{
}

AbcExporter::~AbcExporter()
{
  /* Free xforms map */
  m_xforms_type::iterator it_x, e_x;
  for (it_x = m_xforms.begin(), e_x = m_xforms.end(); it_x != e_x; ++it_x) {
    delete it_x->second;
  }

  /* Free shapes vector */
  for (int i = 0, e = m_shapes.size(); i != e; i++) {
    delete m_shapes[i];
  }

  delete m_writer;
}

void AbcExporter::getShutterSamples(unsigned int nr_of_samples,
                                    bool time_relative,
                                    std::vector<double> &samples)
{
  Scene *scene = m_settings.scene; /* for use in the FPS macro */
  samples.clear();

  unsigned int frame_offset = time_relative ? m_settings.frame_start : 0;
  double time_factor = time_relative ? FPS : 1.0;
  double shutter_open = m_settings.shutter_open;
  double shutter_close = m_settings.shutter_close;
  double time_inc = (shutter_close - shutter_open) / nr_of_samples;

  /* sample between shutter open & close */
  for (int sample = 0; sample < nr_of_samples; sample++) {
    double sample_time = shutter_open + time_inc * sample;
    double time = (frame_offset + sample_time) / time_factor;

    samples.push_back(time);
  }
}

Alembic::Abc::TimeSamplingPtr AbcExporter::createTimeSampling(double step)
{
  std::vector<double> samples;

  if (m_settings.frame_start == m_settings.frame_end) {
    return TimeSamplingPtr(new Alembic::Abc::TimeSampling());
  }

  getShutterSamples(step, true, samples);

  /* TODO(Sybren): shouldn't we use the FPS macro here? */
  Alembic::Abc::TimeSamplingType ts(static_cast<uint32_t>(samples.size()),
                                    1.0 / m_settings.scene->r.frs_sec);

  return TimeSamplingPtr(new Alembic::Abc::TimeSampling(ts, samples));
}

void AbcExporter::getFrameSet(unsigned int nr_of_samples, std::set<double> &frames)
{
  frames.clear();

  std::vector<double> shutter_samples;

  getShutterSamples(nr_of_samples, false, shutter_samples);

  for (double frame = m_settings.frame_start; frame <= m_settings.frame_end; frame += 1.0) {
    for (size_t j = 0; j < nr_of_samples; j++) {
      frames.insert(frame + shutter_samples[j]);
    }
  }
}

void AbcExporter::operator()(short *do_update, float *progress, bool *was_canceled)
{
  std::string abc_scene_name;

  if (m_bmain->name[0] != '\0') {
    char scene_file_name[FILE_MAX];
    BLI_strncpy(scene_file_name, m_bmain->name, FILE_MAX);
    abc_scene_name = scene_file_name;
  }
  else {
    abc_scene_name = "untitled";
  }

  m_writer = new ArchiveWriter(m_filename, abc_scene_name, m_settings.scene);

  /* Create time samplings for transforms and shapes. */

  TimeSamplingPtr trans_time = createTimeSampling(m_settings.frame_samples_xform);

  m_trans_sampling_index = m_writer->archive().addTimeSampling(*trans_time);

  TimeSamplingPtr shape_time;

  if ((m_settings.frame_samples_shape == m_settings.frame_samples_xform) ||
      (m_settings.frame_start == m_settings.frame_end)) {
    shape_time = trans_time;
    m_shape_sampling_index = m_trans_sampling_index;
  }
  else {
    shape_time = createTimeSampling(m_settings.frame_samples_shape);
    m_shape_sampling_index = m_writer->archive().addTimeSampling(*shape_time);
  }

  OBox3dProperty archive_bounds_prop = Alembic::AbcGeom::CreateOArchiveBounds(
      m_writer->archive(), m_trans_sampling_index);

  createTransformWritersHierarchy();
  createShapeWriters();

  /* Make a list of frames to export. */

  std::set<double> xform_frames;
  getFrameSet(m_settings.frame_samples_xform, xform_frames);

  std::set<double> shape_frames;
  getFrameSet(m_settings.frame_samples_shape, shape_frames);

  /* Merge all frames needed. */
  std::set<double> frames(xform_frames);
  frames.insert(shape_frames.begin(), shape_frames.end());

  /* Export all frames. */

  std::set<double>::const_iterator begin = frames.begin();
  std::set<double>::const_iterator end = frames.end();

  const float size = static_cast<float>(frames.size());
  size_t i = 0;

  for (; begin != end; ++begin) {
    *progress = (++i / size);
    *do_update = 1;

    if (G.is_break) {
      *was_canceled = true;
      break;
    }

    const double frame = *begin;

    /* 'frame' is offset by start frame, so need to cancel the offset. */
    setCurrentFrame(m_bmain, frame);

    if (shape_frames.count(frame) != 0) {
      for (int i = 0, e = m_shapes.size(); i != e; i++) {
        m_shapes[i]->write();
      }
    }

    if (xform_frames.count(frame) == 0) {
      continue;
    }

    m_xforms_type::iterator xit, xe;
    for (xit = m_xforms.begin(), xe = m_xforms.end(); xit != xe; ++xit) {
      xit->second->write();
    }

    /* Save the archive 's bounding box. */
    Imath::Box3d bounds;

    for (xit = m_xforms.begin(), xe = m_xforms.end(); xit != xe; ++xit) {
      Imath::Box3d box = xit->second->bounds();
      bounds.extendBy(box);
    }

    archive_bounds_prop.set(bounds);
  }
}

void AbcExporter::createTransformWritersHierarchy()
{
  for (Base *base = static_cast<Base *>(m_settings.view_layer->object_bases.first); base;
       base = base->next) {
    Object *ob = base->object;

    if (export_object(&m_settings, base, false)) {
      switch (ob->type) {
        case OB_LAMP:
        case OB_LATTICE:
        case OB_SPEAKER:
          /* We do not export transforms for objects of these classes. */
          break;
        default:
          exploreTransform(base, ob, ob->parent, NULL);
      }
    }
  }
}

void AbcExporter::exploreTransform(Base *base,
                                   Object *object,
                                   Object *parent,
                                   Object *dupliObParent)
{
  /* If an object isn't exported itself, its duplilist shouldn't be
   * exported either. */
  if (!export_object(&m_settings, base, dupliObParent != NULL)) {
    return;
  }

  Object *ob = DEG_get_evaluated_object(m_settings.depsgraph, object);
  if (object_type_is_exportable(m_settings.scene, ob)) {
    createTransformWriter(ob, parent, dupliObParent);
  }

  ListBase *lb = object_duplilist(m_settings.depsgraph, m_settings.scene, ob);

  if (lb) {
    DupliObject *link = static_cast<DupliObject *>(lb->first);
    Object *dupli_ob = NULL;
    Object *dupli_parent = NULL;

    for (; link; link = link->next) {
      /* This skips things like custom bone shapes. */
      if (m_settings.renderable_only && link->no_draw) {
        continue;
      }

      if (link->type == OB_DUPLICOLLECTION) {
        dupli_ob = link->ob;
        dupli_parent = (dupli_ob->parent) ? dupli_ob->parent : ob;

        exploreTransform(base, dupli_ob, dupli_parent, ob);
      }
    }

    free_object_duplilist(lb);
  }
}

AbcTransformWriter *AbcExporter::createTransformWriter(Object *ob,
                                                       Object *parent,
                                                       Object *dupliObParent)
{
  /* An object should not be its own parent, or we'll get infinite loops. */
  BLI_assert(ob != parent);
  BLI_assert(ob != dupliObParent);

  std::string name;
  if (m_settings.flatten_hierarchy) {
    name = get_id_name(ob);
  }
  else {
    name = get_object_dag_path_name(ob, dupliObParent);
  }

  /* check if we have already created a transform writer for this object */
  AbcTransformWriter *my_writer = getXForm(name);
  if (my_writer != NULL) {
    return my_writer;
  }

  AbcTransformWriter *parent_writer = NULL;
  Alembic::Abc::OObject alembic_parent;

  if (m_settings.flatten_hierarchy || parent == NULL) {
    /* Parentless objects still have the "top object" as parent
     * in Alembic. */
    alembic_parent = m_writer->archive().getTop();
  }
  else {
    /* Since there are so many different ways to find parents (as evident
     * in the number of conditions below), we can't really look up the
     * parent by name. We'll just call createTransformWriter(), which will
     * return the parent's AbcTransformWriter pointer. */
    if (parent->parent) {
      if (parent == dupliObParent) {
        parent_writer = createTransformWriter(parent, parent->parent, NULL);
      }
      else {
        parent_writer = createTransformWriter(parent, parent->parent, dupliObParent);
      }
    }
    else if (parent == dupliObParent) {
      if (dupliObParent->parent == NULL) {
        parent_writer = createTransformWriter(parent, NULL, NULL);
      }
      else {
        parent_writer = createTransformWriter(
            parent, dupliObParent->parent, dupliObParent->parent);
      }
    }
    else {
      parent_writer = createTransformWriter(parent, dupliObParent, dupliObParent);
    }

    BLI_assert(parent_writer);
    alembic_parent = parent_writer->alembicXform();
  }

  my_writer = new AbcTransformWriter(
      ob, alembic_parent, parent_writer, m_trans_sampling_index, m_settings);

  /* When flattening, the matrix of the dupliobject has to be added. */
  if (m_settings.flatten_hierarchy && dupliObParent) {
    my_writer->m_proxy_from = dupliObParent;
  }

  m_xforms[name] = my_writer;
  return my_writer;
}

void AbcExporter::createShapeWriters()
{
  for (Base *base = static_cast<Base *>(m_settings.view_layer->object_bases.first); base;
       base = base->next) {
    exploreObject(base, base->object, NULL);
  }
}

void AbcExporter::exploreObject(Base *base, Object *object, Object *dupliObParent)
{
  /* If an object isn't exported itself, its duplilist shouldn't be
   * exported either. */
  if (!export_object(&m_settings, base, dupliObParent != NULL)) {
    return;
  }

  Object *ob = DEG_get_evaluated_object(m_settings.depsgraph, object);
  createShapeWriter(ob, dupliObParent);

  ListBase *lb = object_duplilist(m_settings.depsgraph, m_settings.scene, ob);

  if (lb) {
    DupliObject *link = static_cast<DupliObject *>(lb->first);

    for (; link; link = link->next) {
      /* This skips things like custom bone shapes. */
      if (m_settings.renderable_only && link->no_draw) {
        continue;
      }
      if (link->type == OB_DUPLICOLLECTION) {
        exploreObject(base, link->ob, ob);
      }
    }

    free_object_duplilist(lb);
  }
}

void AbcExporter::createParticleSystemsWriters(Object *ob, AbcTransformWriter *xform)
{
  if (!m_settings.export_hair && !m_settings.export_particles) {
    return;
  }

  ParticleSystem *psys = static_cast<ParticleSystem *>(ob->particlesystem.first);

  for (; psys; psys = psys->next) {
    if (!psys_check_enabled(ob, psys, G.is_rendering) || !psys->part) {
      continue;
    }

    if (m_settings.export_hair && psys->part->type == PART_HAIR) {
      m_settings.export_child_hairs = true;
      m_shapes.push_back(new AbcHairWriter(ob, xform, m_shape_sampling_index, m_settings, psys));
    }
    else if (m_settings.export_particles &&
             (psys->part->type == PART_EMITTER || psys->part->type == PART_FLUID_FLIP ||
              psys->part->type == PART_FLUID_SPRAY || psys->part->type == PART_FLUID_BUBBLE ||
              psys->part->type == PART_FLUID_FOAM || psys->part->type == PART_FLUID_TRACER ||
              psys->part->type == PART_FLUID_SPRAYFOAM ||
              psys->part->type == PART_FLUID_SPRAYBUBBLE ||
              psys->part->type == PART_FLUID_FOAMBUBBLE ||
              psys->part->type == PART_FLUID_SPRAYFOAMBUBBLE)) {
      m_shapes.push_back(new AbcPointsWriter(ob, xform, m_shape_sampling_index, m_settings, psys));
    }
  }
}

void AbcExporter::createShapeWriter(Object *ob, Object *dupliObParent)
{
  if (!object_type_is_exportable(m_settings.scene, ob)) {
    return;
  }

  std::string name;

  if (m_settings.flatten_hierarchy) {
    name = get_id_name(ob);
  }
  else {
    name = get_object_dag_path_name(ob, dupliObParent);
  }

  AbcTransformWriter *xform = getXForm(name);

  if (!xform) {
    ABC_LOG(m_settings.logger) << __func__ << ": xform " << name << " is NULL\n";
    return;
  }

  createParticleSystemsWriters(ob, xform);

  switch (ob->type) {
    case OB_MESH: {
      Mesh *me = static_cast<Mesh *>(ob->data);

      if (!me) {
        return;
      }

      m_shapes.push_back(new AbcMeshWriter(ob, xform, m_shape_sampling_index, m_settings));
      break;
    }
    case OB_SURF: {
      Curve *cu = static_cast<Curve *>(ob->data);

      if (!cu) {
        return;
      }

      AbcObjectWriter *writer;
      if (m_settings.curves_as_mesh) {
        writer = new AbcCurveMeshWriter(ob, xform, m_shape_sampling_index, m_settings);
      }
      else {
        writer = new AbcNurbsWriter(ob, xform, m_shape_sampling_index, m_settings);
      }
      m_shapes.push_back(writer);
      break;
    }
    case OB_CURVE: {
      Curve *cu = static_cast<Curve *>(ob->data);

      if (!cu) {
        return;
      }

      AbcObjectWriter *writer;
      if (m_settings.curves_as_mesh) {
        writer = new AbcCurveMeshWriter(ob, xform, m_shape_sampling_index, m_settings);
      }
      else {
        writer = new AbcCurveWriter(ob, xform, m_shape_sampling_index, m_settings);
      }
      m_shapes.push_back(writer);
      break;
    }
    case OB_CAMERA: {
      Camera *cam = static_cast<Camera *>(ob->data);

      if (cam->type == CAM_PERSP) {
        m_shapes.push_back(new AbcCameraWriter(ob, xform, m_shape_sampling_index, m_settings));
      }

      break;
    }
    case OB_MBALL: {
      MetaBall *mball = static_cast<MetaBall *>(ob->data);
      if (!mball) {
        return;
      }

      m_shapes.push_back(
          new AbcMBallWriter(m_bmain, ob, xform, m_shape_sampling_index, m_settings));
      break;
    }
  }
}

AbcTransformWriter *AbcExporter::getXForm(const std::string &name)
{
  std::map<std::string, AbcTransformWriter *>::iterator it = m_xforms.find(name);

  if (it == m_xforms.end()) {
    return NULL;
  }

  return it->second;
}

void AbcExporter::setCurrentFrame(Main *bmain, double t)
{
  m_settings.scene->r.cfra = static_cast<int>(t);
  m_settings.scene->r.subframe = static_cast<float>(t) - m_settings.scene->r.cfra;
  BKE_scene_graph_update_for_newframe(m_settings.depsgraph, bmain);
}

}  // namespace alembic
}  // namespace io
}  // namespace blender
