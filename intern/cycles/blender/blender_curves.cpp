/*
 * Copyright 2011, Blender Foundation.
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#include "attribute.h"
#include "mesh.h"
#include "object.h"
#include "scene.h"
#include "curves.h"

#include "blender_sync.h"
#include "blender_util.h"

#include "util_foreach.h"

CCL_NAMESPACE_BEGIN

/* Utilities */

/* Hair curve functions */

void curveinterp_v3_v3v3v3v3(float3 *p, float3 *v1, float3 *v2, float3 *v3, float3 *v4, const float w[4]);
void interp_weights(float t, float data[4], int type);
float shaperadius(float shape, float root, float tip, float time);
void InterpolateKeySegments(int seg, int segno, int key, int curve, float3 *keyloc, float *time, ParticleCurveData *CData, int interpolation);
bool ObtainCacheParticleUV(Mesh *mesh, BL::Mesh *b_mesh, BL::Object *b_ob, ParticleCurveData *CData, bool background, int uv_num);
bool ObtainCacheParticleVcol(Mesh *mesh, BL::Mesh *b_mesh, BL::Object *b_ob, ParticleCurveData *CData, bool background, int vcol_num);
bool ObtainCacheParticleData(Mesh *mesh, BL::Mesh *b_mesh, BL::Object *b_ob, ParticleCurveData *CData, bool background);
void ExportCurveSegments(Scene *scene, Mesh *mesh, ParticleCurveData *CData);
void ExportCurveTrianglePlanes(Mesh *mesh, ParticleCurveData *CData, float3 RotCam);
void ExportCurveTriangleGeometry(Mesh *mesh, ParticleCurveData *CData, int resolution);
void ExportCurveTriangleUV(Mesh *mesh, ParticleCurveData *CData, int vert_offset, int resol, float3 *uvdata);
void ExportCurveTriangleVcol(Mesh *mesh, ParticleCurveData *CData, int vert_offset, int resol, float3 *fdata);

ParticleCurveData::ParticleCurveData()
{
}

ParticleCurveData::~ParticleCurveData()
{
	psys_firstcurve.clear();
	psys_curvenum.clear();
	psys_shader.clear();
	psys_rootradius.clear();
	psys_tipradius.clear();
	psys_shape.clear();

	curve_firstkey.clear();
	curve_keynum.clear();
	curve_length.clear();
	curve_uv.clear();
	curve_vcol.clear();

	curvekey_co.clear();
	curvekey_time.clear();
}

void interp_weights(float t, float data[4], int type)
{
	float t2, t3, fc;
	
	switch (type) {
		case CURVE_LINEAR:
			data[0] =          0.0f;
			data[1] = -t     + 1.0f;
			data[2] =  t;
			data[3] =          0.0f;
			break;
		case CURVE_CARDINAL:
			t2 = t * t;
			t3 = t2 * t;
			fc = 0.71f;

			data[0] = -fc          * t3  + 2.0f * fc          * t2 - fc * t;
			data[1] =  (2.0f - fc) * t3  + (fc - 3.0f)        * t2 + 1.0f;
			data[2] =  (fc - 2.0f) * t3  + (3.0f - 2.0f * fc) * t2 + fc * t;
			data[3] =  fc          * t3  - fc * t2;
			break;
		case CURVE_BSPLINE:
			t2 = t * t;
			t3 = t2 * t;

			data[0] = -0.16666666f * t3  + 0.5f * t2   - 0.5f * t    + 0.16666666f;
			data[1] =  0.5f        * t3  - t2                        + 0.66666666f;
			data[2] = -0.5f        * t3  + 0.5f * t2   + 0.5f * t    + 0.16666666f;
			data[3] =  0.16666666f * t3;
			break;
		default:
			break;
	}
}

void curveinterp_v3_v3v3v3v3(float3 *p, float3 *v1, float3 *v2, float3 *v3, float3 *v4, const float w[4])
{
	p->x = v1->x * w[0] + v2->x * w[1] + v3->x * w[2] + v4->x * w[3];
	p->y = v1->y * w[0] + v2->y * w[1] + v3->y * w[2] + v4->y * w[3];
	p->z = v1->z * w[0] + v2->z * w[1] + v3->z * w[2] + v4->z * w[3];
}

float shaperadius(float shape, float root, float tip, float time)
{
	float radius = 1.0f - time;
	
	if(shape != 0.0f) {
		if(shape < 0.0f)
			radius = powf(radius, 1.0f + shape);
		else
			radius = powf(radius, 1.0f / (1.0f - shape));
	}
	return (radius * (root - tip)) + tip;
}

/* curve functions */

void InterpolateKeySegments(int seg, int segno, int key, int curve, float3 *keyloc, float *time, ParticleCurveData *CData, int interpolation)
{
	float3 ckey_loc1 = CData->curvekey_co[key];
	float3 ckey_loc2 = ckey_loc1;
	float3 ckey_loc3 = CData->curvekey_co[key+1];
	float3 ckey_loc4 = ckey_loc3;

	if(key > CData->curve_firstkey[curve])
		ckey_loc1 = CData->curvekey_co[key - 1];

	if(key < CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 2)
		ckey_loc4 = CData->curvekey_co[key + 2];


	float time1 = CData->curvekey_time[key]/CData->curve_length[curve];
	float time2 = CData->curvekey_time[key + 1]/CData->curve_length[curve];

	float dfra = (time2 - time1) / (float)segno;

	if(time)
		*time = (dfra * seg) + time1;

	float t[4];

	interp_weights((float)seg / (float)segno, t, interpolation);

	if(keyloc)
		curveinterp_v3_v3v3v3v3(keyloc, &ckey_loc1, &ckey_loc2, &ckey_loc3, &ckey_loc4, t);
}

bool ObtainCacheParticleData(Mesh *mesh, BL::Mesh *b_mesh, BL::Object *b_ob, ParticleCurveData *CData, bool background)
{

	int curvenum = 0;
	int keyno = 0;

	if(!(mesh && b_mesh && b_ob && CData))
		return false;

	Transform tfm = get_transform(b_ob->matrix_world());
	Transform itfm = transform_quick_inverse(tfm);

	BL::Object::modifiers_iterator b_mod;
	for(b_ob->modifiers.begin(b_mod); b_mod != b_ob->modifiers.end(); ++b_mod) {
		if((b_mod->type() == b_mod->type_PARTICLE_SYSTEM) && (background ? b_mod->show_render() : b_mod->show_viewport())) {
			BL::ParticleSystemModifier psmd((const PointerRNA)b_mod->ptr);

			BL::ParticleSystem b_psys((const PointerRNA)psmd.particle_system().ptr);

			BL::ParticleSettings b_part((const PointerRNA)b_psys.settings().ptr);

			if((b_psys.settings().render_type()==BL::ParticleSettings::render_type_PATH)&&(b_psys.settings().type()==BL::ParticleSettings::type_HAIR)) {

				int mi = clamp(b_psys.settings().material()-1, 0, mesh->used_shaders.size()-1);
				int shader = mesh->used_shaders[mi];
				int draw_step = background ? b_psys.settings().render_step() : b_psys.settings().draw_step();
				int ren_step = (int)powf(2.0f, (float)draw_step);
				int totparts = b_psys.particles.length();
				int totchild = background ? b_psys.child_particles.length() : (int)((float)b_psys.child_particles.length() * (float)b_psys.settings().draw_percentage() / 100.0f);
				int totcurves = totchild;
				
				if(b_psys.settings().child_type() == 0)
					totcurves += totparts;

				if(totcurves == 0)
					continue;

				PointerRNA cpsys = RNA_pointer_get(&b_part.ptr, "cycles");

				CData->psys_firstcurve.push_back(curvenum);
				CData->psys_curvenum.push_back(totcurves);
				CData->psys_shader.push_back(shader);

				float radius = get_float(cpsys, "radius_scale") * 0.5f;
	
				CData->psys_rootradius.push_back(radius * get_float(cpsys, "root_width"));
				CData->psys_tipradius.push_back(radius * get_float(cpsys, "tip_width"));
				CData->psys_shape.push_back(get_float(cpsys, "shape"));
				CData->psys_closetip.push_back(get_boolean(cpsys, "use_closetip"));

				int pa_no = 0;
				if(!(b_psys.settings().child_type() == 0))
					pa_no = totparts;

				for(; pa_no < totparts+totchild; pa_no++) {

					CData->curve_firstkey.push_back(keyno);
					CData->curve_keynum.push_back(ren_step+1);
					
					float curve_length = 0.0f;
					float3 pcKey;
					for(int step_no = 0; step_no <= ren_step; step_no++) {
						float nco[3];
						b_psys.co_hair(*b_ob, psmd, pa_no, step_no, nco);
						float3 cKey = make_float3(nco[0],nco[1],nco[2]);
						cKey = transform_point(&itfm, cKey);
						if(step_no > 0)
							curve_length += len(cKey - pcKey);
						CData->curvekey_co.push_back(cKey);
						CData->curvekey_time.push_back(curve_length);
						pcKey = cKey;
						keyno++;
					}
					CData->curve_length.push_back(curve_length);

					curvenum++;

				}
			}

		}
	}

	return true;

}

bool ObtainCacheParticleUV(Mesh *mesh, BL::Mesh *b_mesh, BL::Object *b_ob, ParticleCurveData *CData, bool background, int uv_num)
{
#if 0
	int keyno = 0;
#endif

	if(!(mesh && b_mesh && b_ob && CData))
		return false;

#if 0
	Transform tfm = get_transform(b_ob->matrix_world());
	Transform itfm = transform_quick_inverse(tfm);
#endif

	CData->curve_uv.clear();

	BL::Object::modifiers_iterator b_mod;
	for(b_ob->modifiers.begin(b_mod); b_mod != b_ob->modifiers.end(); ++b_mod) {
		if((b_mod->type() == b_mod->type_PARTICLE_SYSTEM) && (background ? b_mod->show_render() : b_mod->show_viewport())) {
			BL::ParticleSystemModifier psmd((const PointerRNA)b_mod->ptr);

			BL::ParticleSystem b_psys((const PointerRNA)psmd.particle_system().ptr);

			BL::ParticleSettings b_part((const PointerRNA)b_psys.settings().ptr);

			if((b_psys.settings().render_type()==BL::ParticleSettings::render_type_PATH)&&(b_psys.settings().type()==BL::ParticleSettings::type_HAIR)) {
#if 0
				int mi = clamp(b_psys.settings().material()-1, 0, mesh->used_shaders.size()-1);
				int shader = mesh->used_shaders[mi];
#endif

				int totparts = b_psys.particles.length();
				int totchild = background ? b_psys.child_particles.length() : (int)((float)b_psys.child_particles.length() * (float)b_psys.settings().draw_percentage() / 100.0f);
				int totcurves = totchild;
				
				if (b_psys.settings().child_type() == 0)
					totcurves += totparts;

				if (totcurves == 0)
					continue;

				int pa_no = 0;
				if(!(b_psys.settings().child_type() == 0))
					pa_no = totparts;

				BL::ParticleSystem::particles_iterator b_pa;
				b_psys.particles.begin(b_pa);
				for(; pa_no < totparts+totchild; pa_no++) {

					/*add uvs*/
					BL::Mesh::tessface_uv_textures_iterator l;
					b_mesh->tessface_uv_textures.begin(l);

					float3 uv = make_float3(0.0f, 0.0f, 0.0f);
					if(b_mesh->tessface_uv_textures.length())
						b_psys.uv_on_emitter(psmd, *b_pa, pa_no, uv_num, &uv.x);
					CData->curve_uv.push_back(uv);

					if(pa_no < totparts && b_pa != b_psys.particles.end())
						++b_pa;

				}
			}

		}
	}

	return true;

}

bool ObtainCacheParticleVcol(Mesh *mesh, BL::Mesh *b_mesh, BL::Object *b_ob, ParticleCurveData *CData, bool background, int vcol_num)
{
#if 0
	int keyno = 0;
#endif
	if(!(mesh && b_mesh && b_ob && CData))
		return false;

#if 0
	Transform tfm = get_transform(b_ob->matrix_world());
	Transform itfm = transform_quick_inverse(tfm);
#endif

	CData->curve_vcol.clear();

	BL::Object::modifiers_iterator b_mod;
	for(b_ob->modifiers.begin(b_mod); b_mod != b_ob->modifiers.end(); ++b_mod) {
		if((b_mod->type() == b_mod->type_PARTICLE_SYSTEM) && (background ? b_mod->show_render() : b_mod->show_viewport())) {
			BL::ParticleSystemModifier psmd((const PointerRNA)b_mod->ptr);

			BL::ParticleSystem b_psys((const PointerRNA)psmd.particle_system().ptr);

			BL::ParticleSettings b_part((const PointerRNA)b_psys.settings().ptr);

			if((b_psys.settings().render_type()==BL::ParticleSettings::render_type_PATH)&&(b_psys.settings().type()==BL::ParticleSettings::type_HAIR)) {
#if 0
				int mi = clamp(b_psys.settings().material()-1, 0, mesh->used_shaders.size()-1);
				int shader = mesh->used_shaders[mi];
#endif
				int totparts = b_psys.particles.length();
				int totchild = background ? b_psys.child_particles.length() : (int)((float)b_psys.child_particles.length() * (float)b_psys.settings().draw_percentage() / 100.0f);
				int totcurves = totchild;
				
				if (b_psys.settings().child_type() == 0)
					totcurves += totparts;

				if (totcurves == 0)
					continue;

				int pa_no = 0;
				if(!(b_psys.settings().child_type() == 0))
					pa_no = totparts;

				BL::ParticleSystem::particles_iterator b_pa;
				b_psys.particles.begin(b_pa);
				for(; pa_no < totparts+totchild; pa_no++) {

					/*add uvs*/
					BL::Mesh::tessface_vertex_colors_iterator l;
					b_mesh->tessface_vertex_colors.begin(l);

					float3 vcol = make_float3(0.0f, 0.0f, 0.0f);
					if(b_mesh->tessface_vertex_colors.length())
						b_psys.mcol_on_emitter(psmd, *b_pa, pa_no, vcol_num, &vcol.x);
					CData->curve_vcol.push_back(vcol);

					if(pa_no < totparts && b_pa != b_psys.particles.end())
						++b_pa;

				}
			}

		}
	}

	return true;

}

static void set_resolution(Mesh *mesh, BL::Mesh *b_mesh, BL::Object *b_ob, BL::Scene *scene, bool render)
{
	BL::Object::modifiers_iterator b_mod;
	for(b_ob->modifiers.begin(b_mod); b_mod != b_ob->modifiers.end(); ++b_mod) {
		if ((b_mod->type() == b_mod->type_PARTICLE_SYSTEM) && ((b_mod->show_viewport()) || (b_mod->show_render()))) {
			BL::ParticleSystemModifier psmd((const PointerRNA)b_mod->ptr);
			BL::ParticleSystem b_psys((const PointerRNA)psmd.particle_system().ptr);
			b_psys.set_resolution(*scene, *b_ob, (render)? 2: 1);
		}
	}
}

void ExportCurveTrianglePlanes(Mesh *mesh, ParticleCurveData *CData, float3 RotCam)
{
	int vertexno = mesh->verts.size();
	int vertexindex = vertexno;

	for( int sys = 0; sys < CData->psys_firstcurve.size() ; sys++) {
		for( int curve = CData->psys_firstcurve[sys]; curve < CData->psys_firstcurve[sys] + CData->psys_curvenum[sys] ; curve++) {

			float3 xbasis;
			float3 v1;
			float time = 0.0f;
			float3 ickey_loc = CData->curvekey_co[CData->curve_firstkey[curve]];
			float radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], CData->psys_tipradius[sys], 0.0f);
			v1 = CData->curvekey_co[CData->curve_firstkey[curve] + 1] - CData->curvekey_co[CData->curve_firstkey[curve]];
			xbasis = normalize(cross(RotCam - ickey_loc,v1));
			float3 ickey_loc_shfl = ickey_loc - radius * xbasis;
			float3 ickey_loc_shfr = ickey_loc + radius * xbasis;
			mesh->verts.push_back(ickey_loc_shfl);
			mesh->verts.push_back(ickey_loc_shfr);
			vertexindex += 2;

			for( int curvekey = CData->curve_firstkey[curve] + 1; curvekey < CData->curve_firstkey[curve] + CData->curve_keynum[curve]; curvekey++) {
				ickey_loc = CData->curvekey_co[curvekey];

				if(curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1)
					v1 = CData->curvekey_co[curvekey] - CData->curvekey_co[max(curvekey - 1, CData->curve_firstkey[curve])];
				else 
					v1 = CData->curvekey_co[curvekey + 1] - CData->curvekey_co[curvekey - 1];

				time = CData->curvekey_time[curvekey]/CData->curve_length[curve];
				radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], CData->psys_tipradius[sys], time);

				if((curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1))
					radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], CData->psys_tipradius[sys], 0.95f);

				if(CData->psys_closetip[sys] && (curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1))
					radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], 0.0f, 0.95f);

				xbasis = normalize(cross(RotCam - ickey_loc,v1));
				float3 ickey_loc_shfl = ickey_loc - radius * xbasis;
				float3 ickey_loc_shfr = ickey_loc + radius * xbasis;
				mesh->verts.push_back(ickey_loc_shfl);
				mesh->verts.push_back(ickey_loc_shfr);
				mesh->add_triangle(vertexindex-2, vertexindex, vertexindex-1, CData->psys_shader[sys], true);
				mesh->add_triangle(vertexindex+1, vertexindex-1, vertexindex, CData->psys_shader[sys], true);
				vertexindex += 2;
			}
		}
	}

	mesh->reserve(mesh->verts.size(), mesh->triangles.size(), 0, 0);
	mesh->attributes.remove(ATTR_STD_VERTEX_NORMAL);
	mesh->attributes.remove(ATTR_STD_FACE_NORMAL);
	mesh->add_face_normals();
	mesh->add_vertex_normals();
	mesh->attributes.remove(ATTR_STD_FACE_NORMAL);

	/* texture coords still needed */
}

void ExportCurveTriangleGeometry(Mesh *mesh, ParticleCurveData *CData, int resolution)
{
	int vertexno = mesh->verts.size();
	int vertexindex = vertexno;

	for( int sys = 0; sys < CData->psys_firstcurve.size() ; sys++) {
		for( int curve = CData->psys_firstcurve[sys]; curve < CData->psys_firstcurve[sys] + CData->psys_curvenum[sys] ; curve++) {

			float3 firstxbasis = cross(make_float3(1.0f,0.0f,0.0f),CData->curvekey_co[CData->curve_firstkey[curve]+1] - CData->curvekey_co[CData->curve_firstkey[curve]]);
			if(len_squared(firstxbasis)!= 0.0f)
				firstxbasis = normalize(firstxbasis);
			else
				firstxbasis = normalize(cross(make_float3(0.0f,1.0f,0.0f),CData->curvekey_co[CData->curve_firstkey[curve]+1] - CData->curvekey_co[CData->curve_firstkey[curve]]));


			for( int curvekey = CData->curve_firstkey[curve]; curvekey < CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1; curvekey++) {

				float3 xbasis = firstxbasis;
				float3 v1;
				float3 v2;

				if(curvekey == CData->curve_firstkey[curve]) {
					v1 = CData->curvekey_co[min(curvekey+2,CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1)] - CData->curvekey_co[curvekey+1];
					v2 = CData->curvekey_co[curvekey+1] - CData->curvekey_co[curvekey];
				}
				else if(curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1) {
					v1 = CData->curvekey_co[curvekey] - CData->curvekey_co[curvekey-1];
					v2 = CData->curvekey_co[curvekey-1] - CData->curvekey_co[max(curvekey-2,CData->curve_firstkey[curve])];
				}
				else {
					v1 = CData->curvekey_co[curvekey+1] - CData->curvekey_co[curvekey];
					v2 = CData->curvekey_co[curvekey] - CData->curvekey_co[curvekey-1];
				}

				xbasis = cross(v1,v2);

				if(len_squared(xbasis) >= 0.05f * len_squared(v1) * len_squared(v2)) {
					firstxbasis = normalize(xbasis);
					break;
				}
			}

			for( int curvekey = CData->curve_firstkey[curve]; curvekey < CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1; curvekey++) {

				int subv = 1;
				float3 xbasis;
				float3 ybasis;
				float3 v1;
				float3 v2;

				if(curvekey == CData->curve_firstkey[curve]) {
					subv = 0;
					v1 = CData->curvekey_co[min(curvekey+2,CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1)] - CData->curvekey_co[curvekey+1];
					v2 = CData->curvekey_co[curvekey+1] - CData->curvekey_co[curvekey];
				}
				else if(curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1) {
					v1 = CData->curvekey_co[curvekey] - CData->curvekey_co[curvekey-1];
					v2 = CData->curvekey_co[curvekey-1] - CData->curvekey_co[max(curvekey-2,CData->curve_firstkey[curve])];
				}
				else {
					v1 = CData->curvekey_co[curvekey+1] - CData->curvekey_co[curvekey];
					v2 = CData->curvekey_co[curvekey] - CData->curvekey_co[curvekey-1];
				}

				xbasis = cross(v1,v2);

				if(len_squared(xbasis) >= 0.05f * len_squared(v1) * len_squared(v2)) {
					xbasis = normalize(xbasis);
					firstxbasis = xbasis;
				}
				else
					xbasis = firstxbasis;

				ybasis = normalize(cross(xbasis,v2));

				for (; subv <= 1; subv++) {

					float3 ickey_loc = make_float3(0.0f,0.0f,0.0f);
					float time = 0.0f;

					InterpolateKeySegments(subv, 1, curvekey, curve, &ickey_loc, &time, CData , 1);

					float radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], CData->psys_tipradius[sys], time);

					if((curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 2) && (subv == 1))
						radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], CData->psys_tipradius[sys], 0.95f);

					if(CData->psys_closetip[sys] && (subv == 1) && (curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 2))
						radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], 0.0f, 0.95f);

					float angle = M_2PI_F / (float)resolution;
					for(int section = 0 ; section < resolution; section++) {
						float3 ickey_loc_shf = ickey_loc + radius * (cosf(angle * section) * xbasis + sinf(angle * section) * ybasis);
						mesh->verts.push_back(ickey_loc_shf);
					}

					if(subv!=0) {
						for(int section = 0 ; section < resolution - 1; section++) {
							mesh->add_triangle(vertexindex - resolution + section, vertexindex + section, vertexindex - resolution + section + 1, CData->psys_shader[sys], true);
							mesh->add_triangle(vertexindex + section + 1, vertexindex - resolution + section + 1, vertexindex + section, CData->psys_shader[sys], true);
						}
						mesh->add_triangle(vertexindex-1, vertexindex + resolution - 1, vertexindex - resolution, CData->psys_shader[sys], true);
						mesh->add_triangle(vertexindex, vertexindex - resolution , vertexindex + resolution - 1, CData->psys_shader[sys], true);
					}
					vertexindex += resolution;
				}
			}
		}
	}

	mesh->reserve(mesh->verts.size(), mesh->triangles.size(), 0, 0);
	mesh->attributes.remove(ATTR_STD_VERTEX_NORMAL);
	mesh->attributes.remove(ATTR_STD_FACE_NORMAL);
	mesh->add_face_normals();
	mesh->add_vertex_normals();
	mesh->attributes.remove(ATTR_STD_FACE_NORMAL);

	/* texture coords still needed */
}

static void ExportCurveSegments(Scene *scene, Mesh *mesh, ParticleCurveData *CData)
{
	int num_keys = 0;
	int num_curves = 0;

	if(!(mesh->curves.empty() && mesh->curve_keys.empty()))
		return;

	Attribute *attr_intercept = NULL;
	
	if(mesh->need_attribute(scene, ATTR_STD_CURVE_INTERCEPT))
		attr_intercept = mesh->curve_attributes.add(ATTR_STD_CURVE_INTERCEPT);

	for( int sys = 0; sys < CData->psys_firstcurve.size() ; sys++) {

		if(CData->psys_curvenum[sys] == 0)
			continue;

		for( int curve = CData->psys_firstcurve[sys]; curve < CData->psys_firstcurve[sys] + CData->psys_curvenum[sys] ; curve++) {

			if(CData->curve_keynum[curve] <= 1)
				continue;

			size_t num_curve_keys = 0;

			for( int curvekey = CData->curve_firstkey[curve]; curvekey < CData->curve_firstkey[curve] + CData->curve_keynum[curve]; curvekey++) {
				float3 ickey_loc = CData->curvekey_co[curvekey];
				float time = CData->curvekey_time[curvekey]/CData->curve_length[curve];
				float radius = shaperadius(CData->psys_shape[sys], CData->psys_rootradius[sys], CData->psys_tipradius[sys], time);

				if(CData->psys_closetip[sys] && (curvekey == CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1))
					radius =0.0f;

				mesh->add_curve_key(ickey_loc, radius);
				if(attr_intercept)
					attr_intercept->add(time);

				num_curve_keys++;
			}

			mesh->add_curve(num_keys, num_curve_keys, CData->psys_shader[sys]);
			num_keys += num_curve_keys;
			num_curves++;
		}
	}

	/* check allocation*/
	if((mesh->curve_keys.size() !=  num_keys) || (mesh->curves.size() !=  num_curves)) {
		/* allocation failed -> clear data */
		mesh->curve_keys.clear();
		mesh->curves.clear();
		mesh->curve_attributes.clear();
	}
}

void ExportCurveTriangleUV(Mesh *mesh, ParticleCurveData *CData, int vert_offset, int resol, float3 *uvdata)
{
	if(uvdata == NULL)
		return;

	float time = 0.0f;
	float prevtime = 0.0f;

	int vertexindex = vert_offset;

	for( int sys = 0; sys < CData->psys_firstcurve.size() ; sys++) {
		for( int curve = CData->psys_firstcurve[sys]; curve < CData->psys_firstcurve[sys] + CData->psys_curvenum[sys] ; curve++) {

			for( int curvekey = CData->curve_firstkey[curve]; curvekey < CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1; curvekey++) {

				time = CData->curvekey_time[curvekey]/CData->curve_length[curve];

				for(int section = 0 ; section < resol; section++) {
					uvdata[vertexindex] = CData->curve_uv[curve];
					uvdata[vertexindex].z = prevtime;
					vertexindex++;
					uvdata[vertexindex] = CData->curve_uv[curve];
					uvdata[vertexindex].z = time;
					vertexindex++;
					uvdata[vertexindex] = CData->curve_uv[curve];
					uvdata[vertexindex].z = prevtime;
					vertexindex++;
					uvdata[vertexindex] = CData->curve_uv[curve];
					uvdata[vertexindex].z = time;
					vertexindex++;
					uvdata[vertexindex] = CData->curve_uv[curve];
					uvdata[vertexindex].z = prevtime;
					vertexindex++;
					uvdata[vertexindex] = CData->curve_uv[curve];
					uvdata[vertexindex].z = time;
					vertexindex++;
				}

				prevtime = time;			
				
			}
		}
	}

}

void ExportCurveTriangleVcol(Mesh *mesh, ParticleCurveData *CData, int vert_offset, int resol, float3 *fdata)
{
	if(fdata == NULL)
		return;

	int vertexindex = vert_offset;

	for( int sys = 0; sys < CData->psys_firstcurve.size() ; sys++) {
		for( int curve = CData->psys_firstcurve[sys]; curve < CData->psys_firstcurve[sys] + CData->psys_curvenum[sys] ; curve++) {

			for( int curvekey = CData->curve_firstkey[curve]; curvekey < CData->curve_firstkey[curve] + CData->curve_keynum[curve] - 1; curvekey++) {

				for(int section = 0 ; section < resol; section++) {
					fdata[vertexindex] = color_srgb_to_scene_linear(CData->curve_vcol[curve]);
					vertexindex++;
					fdata[vertexindex] = color_srgb_to_scene_linear(CData->curve_vcol[curve]);
					vertexindex++;
					fdata[vertexindex] = color_srgb_to_scene_linear(CData->curve_vcol[curve]);
					vertexindex++;
					fdata[vertexindex] = color_srgb_to_scene_linear(CData->curve_vcol[curve]);
					vertexindex++;
					fdata[vertexindex] = color_srgb_to_scene_linear(CData->curve_vcol[curve]);
					vertexindex++;
					fdata[vertexindex] = color_srgb_to_scene_linear(CData->curve_vcol[curve]);
					vertexindex++;
				}
			}
		}
	}

}

/* Hair Curve Sync */

void BlenderSync::sync_curve_settings()
{
	PointerRNA csscene = RNA_pointer_get(&b_scene.ptr, "cycles_curves");
	
	int preset = CURVE_ACCURATE_PRESET;

	CurveSystemManager *curve_system_manager = scene->curve_system_manager;
	CurveSystemManager prev_curve_system_manager = *curve_system_manager;

	curve_system_manager->use_curves = get_boolean(csscene, "use_curves");
	curve_system_manager->minimum_width = get_float(csscene, "minimum_width");
	curve_system_manager->maximum_width = get_float(csscene, "maximum_width");

	curve_system_manager->primitive = get_enum(csscene, "primitive");
	curve_system_manager->curve_shape = get_enum(csscene, "shape");
	curve_system_manager->resolution = get_int(csscene, "resolution");
	curve_system_manager->subdivisions = get_int(csscene, "subdivisions");
	curve_system_manager->use_backfacing = !get_boolean(csscene, "cull_backfacing");

	curve_system_manager->encasing_ratio = 1.01f;

	if(curve_system_manager->primitive == CURVE_TRIANGLES && curve_system_manager->curve_shape == CURVE_RIBBON) {
		/*camera facing planes*/
		curve_system_manager->triangle_method = CURVE_CAMERA_TRIANGLES;
		curve_system_manager->resolution = 1;
	}
	if(curve_system_manager->primitive == CURVE_TRIANGLES && curve_system_manager->curve_shape == CURVE_THICK) {
		/*camera facing planes*/
		curve_system_manager->triangle_method = CURVE_TESSELATED_TRIANGLES;
	}
	if(curve_system_manager->primitive == CURVE_LINE_SEGMENTS && curve_system_manager->curve_shape == CURVE_RIBBON) {
		/*tangent shading*/
		curve_system_manager->line_method = CURVE_UNCORRECTED;
		curve_system_manager->use_encasing = true;
		curve_system_manager->use_backfacing = false;
		curve_system_manager->use_tangent_normal = true;
		curve_system_manager->use_tangent_normal_geometry = true;
	}
	if(curve_system_manager->primitive == CURVE_LINE_SEGMENTS && curve_system_manager->curve_shape == CURVE_THICK) {
		curve_system_manager->line_method = CURVE_ACCURATE;
		curve_system_manager->use_encasing = false;
		curve_system_manager->use_tangent_normal = false;
		curve_system_manager->use_tangent_normal_geometry = false;
	}
	if(curve_system_manager->primitive == CURVE_SEGMENTS && curve_system_manager->curve_shape == CURVE_RIBBON) {
		curve_system_manager->primitive = CURVE_RIBBONS;
		curve_system_manager->use_backfacing = false;
	}

	if(curve_system_manager->modified_mesh(prev_curve_system_manager))
	{
		BL::BlendData::objects_iterator b_ob;

		for(b_data.objects.begin(b_ob); b_ob != b_data.objects.end(); ++b_ob) {
			if(object_is_mesh(*b_ob)) {
				BL::Object::particle_systems_iterator b_psys;
				for(b_ob->particle_systems.begin(b_psys); b_psys != b_ob->particle_systems.end(); ++b_psys) {
					if((b_psys->settings().render_type()==BL::ParticleSettings::render_type_PATH)&&(b_psys->settings().type()==BL::ParticleSettings::type_HAIR)) {
						BL::ID key = BKE_object_is_modified(*b_ob)? *b_ob: b_ob->data();
						mesh_map.set_recalc(key);
						object_map.set_recalc(*b_ob);
					}
				}
			}
		}
	}

	if(curve_system_manager->modified(prev_curve_system_manager))
		curve_system_manager->tag_update(scene);

}

void BlenderSync::sync_curves(Mesh *mesh, BL::Mesh b_mesh, BL::Object b_ob, bool object_updated)
{
	/* Clear stored curve data */
	mesh->curve_keys.clear();
	mesh->curves.clear();
	mesh->curve_attributes.clear();

	/* obtain general settings */
	bool use_curves = scene->curve_system_manager->use_curves;

	if(!(use_curves && b_ob.mode() == b_ob.mode_OBJECT)) {
		mesh->compute_bounds();
		return;
	}

	int primitive = scene->curve_system_manager->primitive;
	int triangle_method = scene->curve_system_manager->triangle_method;
	int resolution = scene->curve_system_manager->resolution;
	size_t vert_num = mesh->verts.size();
	size_t tri_num = mesh->triangles.size();
	int used_res = 1;

	/* extract particle hair data - should be combined with connecting to mesh later*/

	ParticleCurveData CData;

	if(!preview)
		set_resolution(mesh, &b_mesh, &b_ob, &b_scene, true);

	ObtainCacheParticleData(mesh, &b_mesh, &b_ob, &CData, !preview);

	/* obtain camera parameters */
	BL::Object b_CamOb = b_scene.camera();
	float3 RotCam = make_float3(0.0f, 0.0f, 0.0f);
	if(b_CamOb) {
		Transform ctfm = get_transform(b_CamOb.matrix_world());
		Transform tfm = get_transform(b_ob.matrix_world());
		Transform itfm = transform_quick_inverse(tfm);
		RotCam = transform_point(&itfm, make_float3(ctfm.x.w, ctfm.y.w, ctfm.z.w));
	}

	/* add hair geometry to mesh */
	if(primitive == CURVE_TRIANGLES){
		if(triangle_method == CURVE_CAMERA_TRIANGLES)
			ExportCurveTrianglePlanes(mesh, &CData, RotCam);
		else {
			ExportCurveTriangleGeometry(mesh, &CData, resolution);
			used_res = resolution;
		}
	}
	else {
		ExportCurveSegments(scene, mesh, &CData);
	}


	/* generated coordinates from first key. we should ideally get this from
	 * blender to handle deforming objects */
	{
		if(mesh->need_attribute(scene, ATTR_STD_GENERATED)) {
			float3 loc, size;
			mesh_texture_space(b_mesh, loc, size);

			if(primitive == CURVE_TRIANGLES) {
				Attribute *attr_generated = mesh->attributes.add(ATTR_STD_GENERATED);
				float3 *generated = attr_generated->data_float3();

				for(size_t i = vert_num; i < mesh->verts.size(); i++)
					generated[i] = mesh->verts[i]*size - loc;
			}
			else {
				Attribute *attr_generated = mesh->curve_attributes.add(ATTR_STD_GENERATED);
				float3 *generated = attr_generated->data_float3();
				size_t i = 0;

				foreach(Mesh::Curve& curve, mesh->curves) {
					float3 co = mesh->curve_keys[curve.first_key].co;
					generated[i++] = co*size - loc;
				}
			}
		}
	}

	/* create vertex color attributes */
	{
		BL::Mesh::tessface_vertex_colors_iterator l;
		int vcol_num = 0;

		for(b_mesh.tessface_vertex_colors.begin(l); l != b_mesh.tessface_vertex_colors.end(); ++l, vcol_num++) {
			if(!mesh->need_attribute(scene, ustring(l->name().c_str())))
				continue;

			ObtainCacheParticleVcol(mesh, &b_mesh, &b_ob, &CData, !preview, vcol_num);

			if(primitive == CURVE_TRIANGLES) {

				Attribute *attr_vcol = mesh->attributes.add(
					ustring(l->name().c_str()), TypeDesc::TypeColor, ATTR_ELEMENT_CORNER);

				float3 *fdata = attr_vcol->data_float3();

				ExportCurveTriangleVcol(mesh, &CData, tri_num * 3, used_res, fdata);
			}
			else {
				Attribute *attr_vcol = mesh->curve_attributes.add(
					ustring(l->name().c_str()), TypeDesc::TypeColor, ATTR_ELEMENT_CURVE);

				float3 *fdata = attr_vcol->data_float3();

				if(fdata) {
					for(size_t curve = 0; curve < CData.curve_vcol.size() ;curve++)
						fdata[curve] = color_srgb_to_scene_linear(CData.curve_vcol[curve]);
				}
			}
		}
	}

	/* create UV attributes */
	{
		BL::Mesh::tessface_uv_textures_iterator l;
		int uv_num = 0;

		for(b_mesh.tessface_uv_textures.begin(l); l != b_mesh.tessface_uv_textures.end(); ++l, uv_num++) {
			bool active_render = l->active_render();
			AttributeStandard std = (active_render)? ATTR_STD_UV: ATTR_STD_NONE;
			ustring name = ustring(l->name().c_str());

			/* UV map */
			if(mesh->need_attribute(scene, name) || mesh->need_attribute(scene, std)) {
				Attribute *attr_uv;

				ObtainCacheParticleUV(mesh, &b_mesh, &b_ob, &CData, !preview, uv_num);

				if(primitive == CURVE_TRIANGLES) {
					if(active_render)
						attr_uv = mesh->attributes.add(std, name);
					else
						attr_uv = mesh->attributes.add(name, TypeDesc::TypePoint, ATTR_ELEMENT_CORNER);

					float3 *uv = attr_uv->data_float3();

					ExportCurveTriangleUV(mesh, &CData, tri_num * 3, used_res, uv);
				}
				else {
					if(active_render)
						attr_uv = mesh->curve_attributes.add(std, name);
					else
						attr_uv = mesh->curve_attributes.add(name, TypeDesc::TypePoint,  ATTR_ELEMENT_CURVE);

					float3 *uv = attr_uv->data_float3();

					if(uv) {
						for(size_t curve = 0; curve < CData.curve_uv.size(); curve++)
							uv[curve] = CData.curve_uv[curve];
					}
				}
			}
		}
	}

	if(!preview)
		set_resolution(mesh, &b_mesh, &b_ob, &b_scene, false);

	mesh->compute_bounds();
}


CCL_NAMESPACE_END

