/**
 * $Id$
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
 */
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "KX_PolygonMaterial.h"

#include "BKE_mesh.h"
#include "BKE_global.h"
#include "BKE_image.h"

#include "DNA_material_types.h"
#include "DNA_texture_types.h"
#include "DNA_image_types.h"
#include "DNA_meshdata_types.h"

#include "IMB_imbuf_types.h"

#include "GPU_draw.h"

#include "MEM_guardedalloc.h"

#include "RAS_LightObject.h"
#include "RAS_MaterialBucket.h"

#include "KX_PyMath.h"

KX_PolygonMaterial::KX_PolygonMaterial(PyTypeObject *T) 
		: PyObjectPlus(T),
		  RAS_IPolyMaterial(),

	m_tface(NULL),
	m_mcol(NULL),
	m_material(NULL),
	m_pymaterial(NULL),
	m_pass(0)
{
}

void KX_PolygonMaterial::Initialize(
		const STR_String &texname,
		Material* ma,
		int materialindex,
		int tile,
		int tilexrep,
		int tileyrep,
		int mode,
		int transp,
		bool alpha,
		bool zsort,
		int lightlayer,
		struct MTFace* tface,
		unsigned int* mcol)
{
	RAS_IPolyMaterial::Initialize(
							texname,
							ma?ma->id.name:"",
							materialindex,
							tile,
							tilexrep,
							tileyrep,
							mode,
							transp,
							alpha,
							zsort,
							lightlayer);
	m_tface = tface;
	m_mcol = mcol;
	m_material = ma;
	m_pymaterial = 0;
	m_pass = 0;
}

KX_PolygonMaterial::~KX_PolygonMaterial()
{
	if (m_pymaterial)
	{
		Py_DECREF(m_pymaterial);
	}
}

bool KX_PolygonMaterial::Activate(RAS_IRasterizer* rasty, TCachingInfo& cachingInfo) const 
{
	bool dopass = false;
	if (m_pymaterial)
	{
		PyObject *pyRasty = PyCObject_FromVoidPtr((void*)rasty, NULL);	/* new reference */
		PyObject *pyCachingInfo = PyCObject_FromVoidPtr((void*) &cachingInfo, NULL); /* new reference */
		PyObject *ret = PyObject_CallMethod(m_pymaterial, "activate", "(NNO)", pyRasty, pyCachingInfo, (PyObject*) this->m_proxy);
		if (ret)
		{
			bool value = PyInt_AsLong(ret);
			Py_DECREF(ret);
			dopass = value;
		}
		else
		{
			PyErr_Print();
			PyErr_Clear();
			PySys_SetObject( (char *)"last_traceback", NULL);
		}
	}
	else
	{
		switch (m_pass++)
		{
			case 0:
				DefaultActivate(rasty, cachingInfo);
				dopass = true;
				break;
			default:
				m_pass = 0;
				dopass = false;
				break;
		}
	}
	
	return dopass;
}

void KX_PolygonMaterial::DefaultActivate(RAS_IRasterizer* rasty, TCachingInfo& cachingInfo) const 
{
	if (GetCachingInfo() != cachingInfo)
	{
		if (!cachingInfo)
			GPU_set_tpage(NULL);

		cachingInfo = GetCachingInfo();

		if ((m_drawingmode & 4)&& (rasty->GetDrawingMode() == RAS_IRasterizer::KX_TEXTURED))
		{
			Image *ima = (Image*)m_tface->tpage;
			GPU_update_image_time(ima, rasty->GetTime());
			GPU_set_tpage(m_tface);
		}
		else
			GPU_set_tpage(NULL);
		
		if(m_drawingmode & RAS_IRasterizer::KX_TWOSIDE)
			rasty->SetCullFace(false);
		else
			rasty->SetCullFace(true);

		if ((m_drawingmode & RAS_IRasterizer::KX_LINES) ||
		    (rasty->GetDrawingMode() <= RAS_IRasterizer::KX_WIREFRAME))
			rasty->SetLines(true);
		else
			rasty->SetLines(false);
		rasty->SetSpecularity(m_specular[0],m_specular[1],m_specular[2],m_specularity);
		rasty->SetShinyness(m_shininess);
		rasty->SetDiffuse(m_diffuse[0], m_diffuse[1],m_diffuse[2], 1.0);
		if (m_material)
			rasty->SetPolygonOffset(-m_material->zoffs, 0.0);
	}

	//rasty->SetSpecularity(m_specular[0],m_specular[1],m_specular[2],m_specularity);
	//rasty->SetShinyness(m_shininess);
	//rasty->SetDiffuse(m_diffuse[0], m_diffuse[1],m_diffuse[2], 1.0);
	//if (m_material)
	//	rasty->SetPolygonOffset(-m_material->zoffs, 0.0);
}

void KX_PolygonMaterial::GetMaterialRGBAColor(unsigned char *rgba) const
{
	if (m_material) {
		*rgba++ = (unsigned char) (m_material->r*255.0);
		*rgba++ = (unsigned char) (m_material->g*255.0);
		*rgba++ = (unsigned char) (m_material->b*255.0);
		*rgba++ = (unsigned char) (m_material->alpha*255.0);
	} else
		RAS_IPolyMaterial::GetMaterialRGBAColor(rgba);
}


//----------------------------------------------------------------------------
//Python


PyMethodDef KX_PolygonMaterial::Methods[] = {
	KX_PYMETHODTABLE(KX_PolygonMaterial, setCustomMaterial),
	KX_PYMETHODTABLE(KX_PolygonMaterial, updateTexture),
	KX_PYMETHODTABLE(KX_PolygonMaterial, setTexture),
	KX_PYMETHODTABLE(KX_PolygonMaterial, activate),
//	KX_PYMETHODTABLE(KX_PolygonMaterial, setPerPixelLights),
	
	{NULL,NULL} //Sentinel
};

PyAttributeDef KX_PolygonMaterial::Attributes[] = {
	KX_PYATTRIBUTE_RO_FUNCTION("texture",	KX_PolygonMaterial, pyattr_get_texture),
	KX_PYATTRIBUTE_RO_FUNCTION("material",	KX_PolygonMaterial, pyattr_get_material), /* should probably be .name ? */
	
	KX_PYATTRIBUTE_INT_RW("tile", INT_MIN, INT_MAX, true, KX_PolygonMaterial, m_tile),
	KX_PYATTRIBUTE_INT_RW("tilexrep", INT_MIN, INT_MAX, true, KX_PolygonMaterial, m_tilexrep),
	KX_PYATTRIBUTE_INT_RW("tileyrep", INT_MIN, INT_MAX, true, KX_PolygonMaterial, m_tileyrep),
	KX_PYATTRIBUTE_INT_RW("drawingmode", INT_MIN, INT_MAX, true, KX_PolygonMaterial, m_drawingmode),	
	KX_PYATTRIBUTE_INT_RW("lightlayer", INT_MIN, INT_MAX, true, KX_PolygonMaterial, m_lightlayer),

	KX_PYATTRIBUTE_BOOL_RW("transparent", KX_PolygonMaterial, m_alpha),
	KX_PYATTRIBUTE_BOOL_RW("zsort", KX_PolygonMaterial, m_zsort),
	
	KX_PYATTRIBUTE_FLOAT_RW("shininess", 0.0f, 1000.0f, KX_PolygonMaterial, m_shininess),
	KX_PYATTRIBUTE_FLOAT_RW("specularity", 0.0f, 1000.0f, KX_PolygonMaterial, m_specularity),
	
	KX_PYATTRIBUTE_RW_FUNCTION("diffuse", KX_PolygonMaterial, pyattr_get_texture, pyattr_set_diffuse),
	KX_PYATTRIBUTE_RW_FUNCTION("specular",KX_PolygonMaterial, pyattr_get_specular, pyattr_set_specular),	
	
	KX_PYATTRIBUTE_RO_FUNCTION("tface",	KX_PolygonMaterial, pyattr_get_tface), /* How the heck is this even useful??? - Campbell */
	KX_PYATTRIBUTE_RO_FUNCTION("gl_texture", KX_PolygonMaterial, pyattr_get_gl_texture), /* could be called 'bindcode' */
	
	/* triangle used to be an attribute, removed for 2.49, nobody should be using it */
	{ NULL }	//Sentinel
};

PyTypeObject KX_PolygonMaterial::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
		"KX_PolygonMaterial",
		sizeof(PyObjectPlus_Proxy),
		0,
		py_base_dealloc,
		0,
		0,
		0,
		0,
		py_base_repr,
		0,0,0,0,0,0,
		py_base_getattro,
		py_base_setattro,
		0,0,0,0,0,0,0,0,0,
		Methods
};

PyParentObject KX_PolygonMaterial::Parents[] = {
	&KX_PolygonMaterial::Type,
	&PyObjectPlus::Type,
	NULL
};

PyObject* KX_PolygonMaterial::py_getattro(PyObject *attr)
{	
	py_getattro_up(PyObjectPlus);
}

PyObject* KX_PolygonMaterial::py_getattro_dict() {
	py_getattro_dict_up(PyObjectPlus);
}

int KX_PolygonMaterial::py_setattro(PyObject *attr, PyObject *value)
{
	py_setattro_up(PyObjectPlus);
}

KX_PYMETHODDEF_DOC(KX_PolygonMaterial, setCustomMaterial, "setCustomMaterial(material)")
{
	PyObject *material;
	if (PyArg_ParseTuple(args, "O:setCustomMaterial", &material))
	{
		if (m_pymaterial) {
			Py_DECREF(m_pymaterial);
		}
		m_pymaterial = material;
		Py_INCREF(m_pymaterial);
		Py_RETURN_NONE;
	}
	
	return NULL;
}

KX_PYMETHODDEF_DOC(KX_PolygonMaterial, updateTexture, "updateTexture(tface, rasty)")
{
	PyObject *pyrasty, *pytface;
	if (PyArg_ParseTuple(args, "O!O!:updateTexture", &PyCObject_Type, &pytface, &PyCObject_Type, &pyrasty))
	{
		MTFace *tface = (MTFace*) PyCObject_AsVoidPtr(pytface);
		RAS_IRasterizer *rasty = (RAS_IRasterizer*) PyCObject_AsVoidPtr(pyrasty);
		Image *ima = (Image*)tface->tpage;
		GPU_update_image_time(ima, rasty->GetTime());

		Py_RETURN_NONE;
	}
	
	return NULL;
}

KX_PYMETHODDEF_DOC(KX_PolygonMaterial, setTexture, "setTexture(tface)")
{
	PyObject *pytface;
	if (PyArg_ParseTuple(args, "O!:setTexture", &PyCObject_Type, &pytface))
	{
		MTFace *tface = (MTFace*) PyCObject_AsVoidPtr(pytface);
		GPU_set_tpage(tface);
		Py_RETURN_NONE;
	}
	
	return NULL;
}

KX_PYMETHODDEF_DOC(KX_PolygonMaterial, activate, "activate(rasty, cachingInfo)")
{
	PyObject *pyrasty, *pyCachingInfo;
	if (PyArg_ParseTuple(args, "O!O!:activate", &PyCObject_Type, &pyrasty, &PyCObject_Type, &pyCachingInfo))
	{
		RAS_IRasterizer *rasty = static_cast<RAS_IRasterizer*>(PyCObject_AsVoidPtr(pyrasty));
		TCachingInfo *cachingInfo = static_cast<TCachingInfo*>(PyCObject_AsVoidPtr(pyCachingInfo));
		if (rasty && cachingInfo)
		{
			DefaultActivate(rasty, *cachingInfo);
			Py_RETURN_NONE;
		}
	}
	
	return NULL;
}

PyObject* KX_PolygonMaterial::pyattr_get_texture(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	return PyString_FromString(self->m_texturename.ReadPtr());
}

PyObject* KX_PolygonMaterial::pyattr_get_material(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	return PyString_FromString(self->m_materialname.ReadPtr());
}

/* this does not seem useful */
PyObject* KX_PolygonMaterial::pyattr_get_tface(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	return PyCObject_FromVoidPtr(self->m_tface, NULL);
}

PyObject* KX_PolygonMaterial::pyattr_get_gl_texture(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	int bindcode= 0;
	if (self->m_tface && self->m_tface->tpage)
		bindcode= self->m_tface->tpage->bindcode;
	
	return PyInt_FromLong(bindcode);
}


PyObject* KX_PolygonMaterial::pyattr_get_diffuse(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	return PyObjectFrom(self->m_diffuse);
}

int KX_PolygonMaterial::pyattr_set_diffuse(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	MT_Vector3 vec;
	
	if (!PyVecTo(value, vec))
		return PY_SET_ATTR_FAIL;
	
	self->m_diffuse= vec;
	return PY_SET_ATTR_SUCCESS;
}

PyObject* KX_PolygonMaterial::pyattr_get_specular(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	return PyObjectFrom(self->m_specular);
}

int KX_PolygonMaterial::pyattr_set_specular(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_PolygonMaterial* self= static_cast<KX_PolygonMaterial*>(self_v);
	MT_Vector3 vec;
	
	if (!PyVecTo(value, vec))
		return PY_SET_ATTR_FAIL;
	
	self->m_specular= vec;
	return PY_SET_ATTR_SUCCESS;
}
