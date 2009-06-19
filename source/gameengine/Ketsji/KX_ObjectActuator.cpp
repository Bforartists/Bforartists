/**
 * Do translation/rotation actions
 *
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
 */

#include "KX_ObjectActuator.h"
#include "KX_GameObject.h"
#include "KX_PyMath.h" // For PyVecTo - should this include be put in PyObjectPlus?
#include "KX_IPhysicsController.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

KX_ObjectActuator::
KX_ObjectActuator(
	SCA_IObject* gameobj,
	KX_GameObject* refobj,
	const MT_Vector3& force,
	const MT_Vector3& torque,
	const MT_Vector3& dloc,
	const MT_Vector3& drot,
	const MT_Vector3& linV,
	const MT_Vector3& angV,
	const short damping,
	const KX_LocalFlags& flag,
	PyTypeObject* T
) : 
	SCA_IActuator(gameobj,T),
	m_force(force),
	m_torque(torque),
	m_dloc(dloc),
	m_drot(drot),
	m_linear_velocity(linV),
	m_angular_velocity(angV),
	m_linear_length2(0.0),
	m_current_linear_factor(0.0),
	m_current_angular_factor(0.0),
	m_damping(damping),
	m_previous_error(0.0,0.0,0.0),
	m_error_accumulator(0.0,0.0,0.0),
	m_bitLocalFlag (flag),
	m_reference(refobj),
	m_active_combined_velocity (false),
	m_linear_damping_active(false),
	m_angular_damping_active(false)
{
	if (m_bitLocalFlag.ServoControl)
	{
		// in servo motion, the force is local if the target velocity is local
		m_bitLocalFlag.Force = m_bitLocalFlag.LinearVelocity;

		m_pid = m_torque;
	}
	if (m_reference)
		m_reference->RegisterActuator(this);
	UpdateFuzzyFlags();
}

KX_ObjectActuator::~KX_ObjectActuator()
{
	if (m_reference)
		m_reference->UnregisterActuator(this);
}

bool KX_ObjectActuator::Update()
{
	
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();
		
	KX_GameObject *parent = static_cast<KX_GameObject *>(GetParent()); 

	if (bNegativeEvent) {
		// If we previously set the linear velocity we now have to inform
		// the physics controller that we no longer wish to apply it and that
		// it should reconcile the externally set velocity with it's 
		// own velocity.
		if (m_active_combined_velocity) {
			if (parent)
				parent->ResolveCombinedVelocities(
						m_linear_velocity,
						m_angular_velocity,
						(m_bitLocalFlag.LinearVelocity) != 0,
						(m_bitLocalFlag.AngularVelocity) != 0
					);
			m_active_combined_velocity = false;
		} 
		m_linear_damping_active = false;
		m_angular_damping_active = false;
		m_error_accumulator.setValue(0.0,0.0,0.0);
		m_previous_error.setValue(0.0,0.0,0.0);
		return false; 

	} else if (parent)
	{
		if (m_bitLocalFlag.ServoControl) 
		{
			// In this mode, we try to reach a target speed using force
			// As we don't know the friction, we must implement a generic 
			// servo control to achieve the speed in a configurable
			// v = current velocity
			// V = target velocity
			// e = V-v = speed error
			// dt = time interval since previous update
			// I = sum(e(t)*dt)
			// dv = e(t) - e(t-1)
			// KP, KD, KI : coefficient
			// F = KP*e+KI*I+KD*dv
			MT_Scalar mass = parent->GetMass();
			if (mass < MT_EPSILON)
				return false;
			MT_Vector3 v = parent->GetLinearVelocity(m_bitLocalFlag.LinearVelocity);
			if (m_reference)
			{
				const MT_Point3& mypos = parent->NodeGetWorldPosition();
				const MT_Point3& refpos = m_reference->NodeGetWorldPosition();
				MT_Point3 relpos;
				relpos = (mypos-refpos);
				MT_Vector3 vel= m_reference->GetVelocity(relpos);
				if (m_bitLocalFlag.LinearVelocity)
					// must convert in local space
					vel = parent->NodeGetWorldOrientation().transposed()*vel;
				v -= vel;
			}
			MT_Vector3 e = m_linear_velocity - v;
			MT_Vector3 dv = e - m_previous_error;
			MT_Vector3 I = m_error_accumulator + e;

			m_force = m_pid.x()*e+m_pid.y()*I+m_pid.z()*dv;
			// to automatically adapt the PID coefficient to mass;
			m_force *= mass;
			if (m_bitLocalFlag.Torque) 
			{
				if (m_force[0] > m_dloc[0])
				{
					m_force[0] = m_dloc[0];
					I[0] = m_error_accumulator[0];
				} else if (m_force[0] < m_drot[0])
				{
					m_force[0] = m_drot[0];
					I[0] = m_error_accumulator[0];
				}
			}
			if (m_bitLocalFlag.DLoc) 
			{
				if (m_force[1] > m_dloc[1])
				{
					m_force[1] = m_dloc[1];
					I[1] = m_error_accumulator[1];
				} else if (m_force[1] < m_drot[1])
				{
					m_force[1] = m_drot[1];
					I[1] = m_error_accumulator[1];
				}
			}
			if (m_bitLocalFlag.DRot) 
			{
				if (m_force[2] > m_dloc[2])
				{
					m_force[2] = m_dloc[2];
					I[2] = m_error_accumulator[2];
				} else if (m_force[2] < m_drot[2])
				{
					m_force[2] = m_drot[2];
					I[2] = m_error_accumulator[2];
				}
			}
			m_previous_error = e;
			m_error_accumulator = I;
			parent->ApplyForce(m_force,(m_bitLocalFlag.LinearVelocity) != 0);
		} else
		{
			if (!m_bitLocalFlag.ZeroForce)
			{
				parent->ApplyForce(m_force,(m_bitLocalFlag.Force) != 0);
			}
			if (!m_bitLocalFlag.ZeroTorque)
			{
				parent->ApplyTorque(m_torque,(m_bitLocalFlag.Torque) != 0);
			}
			if (!m_bitLocalFlag.ZeroDLoc)
			{
				parent->ApplyMovement(m_dloc,(m_bitLocalFlag.DLoc) != 0);
			}
			if (!m_bitLocalFlag.ZeroDRot)
			{
				parent->ApplyRotation(m_drot,(m_bitLocalFlag.DRot) != 0);
			}
			if (!m_bitLocalFlag.ZeroLinearVelocity)
			{
				if (m_bitLocalFlag.AddOrSetLinV) {
					parent->addLinearVelocity(m_linear_velocity,(m_bitLocalFlag.LinearVelocity) != 0);
				} else {
					m_active_combined_velocity = true;
					if (m_damping > 0) {
						MT_Vector3 linV;
						if (!m_linear_damping_active) {
							// delta and the start speed (depends on the existing speed in that direction)
							linV = parent->GetLinearVelocity(m_bitLocalFlag.LinearVelocity);
							// keep only the projection along the desired direction
							m_current_linear_factor = linV.dot(m_linear_velocity)/m_linear_length2;
							m_linear_damping_active = true;
						}
						if (m_current_linear_factor < 1.0)
							m_current_linear_factor += 1.0/m_damping;
						if (m_current_linear_factor > 1.0)
							m_current_linear_factor = 1.0;
						linV = m_current_linear_factor * m_linear_velocity;
	 					parent->setLinearVelocity(linV,(m_bitLocalFlag.LinearVelocity) != 0);
					} else {
	 					parent->setLinearVelocity(m_linear_velocity,(m_bitLocalFlag.LinearVelocity) != 0);
					}
				}
			}
			if (!m_bitLocalFlag.ZeroAngularVelocity)
			{
				m_active_combined_velocity = true;
				if (m_damping > 0) {
					MT_Vector3 angV;
					if (!m_angular_damping_active) {
						// delta and the start speed (depends on the existing speed in that direction)
						angV = parent->GetAngularVelocity(m_bitLocalFlag.AngularVelocity);
						// keep only the projection along the desired direction
						m_current_angular_factor = angV.dot(m_angular_velocity)/m_angular_length2;
						m_angular_damping_active = true;
					}
					if (m_current_angular_factor < 1.0)
						m_current_angular_factor += 1.0/m_damping;
					if (m_current_angular_factor > 1.0)
						m_current_angular_factor = 1.0;
					angV = m_current_angular_factor * m_angular_velocity;
	 				parent->setAngularVelocity(angV,(m_bitLocalFlag.AngularVelocity) != 0);
				} else {
					parent->setAngularVelocity(m_angular_velocity,(m_bitLocalFlag.AngularVelocity) != 0);
				}
			}
		}
		
	}
	return true;
}



CValue* KX_ObjectActuator::GetReplica()
{
	KX_ObjectActuator* replica = new KX_ObjectActuator(*this);//m_float,GetName());
	replica->ProcessReplica();

	return replica;
}

void KX_ObjectActuator::ProcessReplica()
{
	SCA_IActuator::ProcessReplica();
	if (m_reference)
		m_reference->RegisterActuator(this);
}

bool KX_ObjectActuator::UnlinkObject(SCA_IObject* clientobj)
{
	if (clientobj == (SCA_IObject*)m_reference)
	{
		// this object is being deleted, we cannot continue to use it as reference.
		m_reference = NULL;
		return true;
	}
	return false;
}

void KX_ObjectActuator::Relink(GEN_Map<GEN_HashedPtr, void*> *obj_map)
{
	void **h_obj = (*obj_map)[m_reference];
	if (h_obj) {
		if (m_reference)
			m_reference->UnregisterActuator(this);
		m_reference = (KX_GameObject*)(*h_obj);
		m_reference->RegisterActuator(this);
	}
}

/* some 'standard' utilities... */
bool KX_ObjectActuator::isValid(KX_ObjectActuator::KX_OBJECT_ACT_VEC_TYPE type)
{
	bool res = false;
	res = (type > KX_OBJECT_ACT_NODEF) && (type < KX_OBJECT_ACT_MAX);
	return res;
}



/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_ObjectActuator::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"KX_ObjectActuator",
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

PyParentObject KX_ObjectActuator::Parents[] = {
	&KX_ObjectActuator::Type,
	&SCA_IActuator::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};

PyMethodDef KX_ObjectActuator::Methods[] = {
	// Deprecated ----->
	{"getForce", (PyCFunction) KX_ObjectActuator::sPyGetForce, METH_NOARGS},
	{"setForce", (PyCFunction) KX_ObjectActuator::sPySetForce, METH_VARARGS},
	{"getTorque", (PyCFunction) KX_ObjectActuator::sPyGetTorque, METH_NOARGS},
	{"setTorque", (PyCFunction) KX_ObjectActuator::sPySetTorque, METH_VARARGS},
	{"getDLoc", (PyCFunction) KX_ObjectActuator::sPyGetDLoc, METH_NOARGS},
	{"setDLoc", (PyCFunction) KX_ObjectActuator::sPySetDLoc, METH_VARARGS},
	{"getDRot", (PyCFunction) KX_ObjectActuator::sPyGetDRot, METH_NOARGS},
	{"setDRot", (PyCFunction) KX_ObjectActuator::sPySetDRot, METH_VARARGS},
	{"getLinearVelocity", (PyCFunction) KX_ObjectActuator::sPyGetLinearVelocity, METH_NOARGS},
	{"setLinearVelocity", (PyCFunction) KX_ObjectActuator::sPySetLinearVelocity, METH_VARARGS},
	{"getAngularVelocity", (PyCFunction) KX_ObjectActuator::sPyGetAngularVelocity, METH_NOARGS},
	{"setAngularVelocity", (PyCFunction) KX_ObjectActuator::sPySetAngularVelocity, METH_VARARGS},
	{"setDamping", (PyCFunction) KX_ObjectActuator::sPySetDamping, METH_VARARGS},
	{"getDamping", (PyCFunction) KX_ObjectActuator::sPyGetDamping, METH_NOARGS},
	{"setForceLimitX", (PyCFunction) KX_ObjectActuator::sPySetForceLimitX, METH_VARARGS},
	{"getForceLimitX", (PyCFunction) KX_ObjectActuator::sPyGetForceLimitX, METH_NOARGS},
	{"setForceLimitY", (PyCFunction) KX_ObjectActuator::sPySetForceLimitY, METH_VARARGS},
	{"getForceLimitY", (PyCFunction) KX_ObjectActuator::sPyGetForceLimitY, METH_NOARGS},
	{"setForceLimitZ", (PyCFunction) KX_ObjectActuator::sPySetForceLimitZ, METH_VARARGS},
	{"getForceLimitZ", (PyCFunction) KX_ObjectActuator::sPyGetForceLimitZ, METH_NOARGS},
	{"setPID", (PyCFunction) KX_ObjectActuator::sPyGetPID, METH_NOARGS},
	{"getPID", (PyCFunction) KX_ObjectActuator::sPySetPID, METH_VARARGS},

	// <----- Deprecated

	{NULL,NULL} //Sentinel
};

PyAttributeDef KX_ObjectActuator::Attributes[] = {
	KX_PYATTRIBUTE_VECTOR_RW_CHECK("force", -1000, 1000, false, KX_ObjectActuator, m_force, PyUpdateFuzzyFlags),
	KX_PYATTRIBUTE_BOOL_RW("useLocalForce", KX_ObjectActuator, m_bitLocalFlag.Force),
	KX_PYATTRIBUTE_VECTOR_RW_CHECK("torque", -1000, 1000, false, KX_ObjectActuator, m_torque, PyUpdateFuzzyFlags),
	KX_PYATTRIBUTE_BOOL_RW("useLocalTorque", KX_ObjectActuator, m_bitLocalFlag.Torque),
	KX_PYATTRIBUTE_VECTOR_RW_CHECK("dLoc", -1000, 1000, false, KX_ObjectActuator, m_dloc, PyUpdateFuzzyFlags),
	KX_PYATTRIBUTE_BOOL_RW("useLocalDLoc", KX_ObjectActuator, m_bitLocalFlag.DLoc),
	KX_PYATTRIBUTE_VECTOR_RW_CHECK("dRot", -1000, 1000, false, KX_ObjectActuator, m_drot, PyUpdateFuzzyFlags),
	KX_PYATTRIBUTE_BOOL_RW("useLocalDRot", KX_ObjectActuator, m_bitLocalFlag.DRot),
	KX_PYATTRIBUTE_VECTOR_RW_CHECK("linV", -1000, 1000, false, KX_ObjectActuator, m_linear_velocity, PyUpdateFuzzyFlags),
	KX_PYATTRIBUTE_BOOL_RW("useLocalLinV", KX_ObjectActuator, m_bitLocalFlag.LinearVelocity),
	KX_PYATTRIBUTE_VECTOR_RW_CHECK("angV", -1000, 1000, false, KX_ObjectActuator, m_angular_velocity, PyUpdateFuzzyFlags),
	KX_PYATTRIBUTE_BOOL_RW("useLocalAngV", KX_ObjectActuator, m_bitLocalFlag.AngularVelocity),
	KX_PYATTRIBUTE_SHORT_RW("damping", 0, 1000, false, KX_ObjectActuator, m_damping),
	KX_PYATTRIBUTE_RW_FUNCTION("forceLimitX", KX_ObjectActuator, pyattr_get_forceLimitX, pyattr_set_forceLimitX),
	KX_PYATTRIBUTE_RW_FUNCTION("forceLimitY", KX_ObjectActuator, pyattr_get_forceLimitY, pyattr_set_forceLimitY),
	KX_PYATTRIBUTE_RW_FUNCTION("forceLimitZ", KX_ObjectActuator, pyattr_get_forceLimitZ, pyattr_set_forceLimitZ),
	KX_PYATTRIBUTE_VECTOR_RW_CHECK("pid", -100, 200, true, KX_ObjectActuator, m_pid, PyCheckPid),
	KX_PYATTRIBUTE_RW_FUNCTION("reference", KX_ObjectActuator,pyattr_get_reference,pyattr_set_reference),
	{ NULL }	//Sentinel
};

PyObject* KX_ObjectActuator::py_getattro(PyObject *attr) {
	py_getattro_up(SCA_IActuator);
}


PyObject* KX_ObjectActuator::py_getattro_dict() {
	py_getattro_dict_up(SCA_IActuator);
}

int KX_ObjectActuator::py_setattro(PyObject *attr, PyObject *value)
{
	py_setattro_up(SCA_IActuator);
}

/* Attribute get/set functions */

PyObject* KX_ObjectActuator::pyattr_get_forceLimitX(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_ObjectActuator* self = reinterpret_cast<KX_ObjectActuator*>(self_v);
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(self->m_drot[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(self->m_dloc[0]));
	PyList_SET_ITEM(retVal, 2, PyBool_FromLong(self->m_bitLocalFlag.Torque));
	
	return retVal;
}

int KX_ObjectActuator::pyattr_set_forceLimitX(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_ObjectActuator* self = reinterpret_cast<KX_ObjectActuator*>(self_v);

	PyObject* seq = PySequence_Fast(value, "");
	if (seq && PySequence_Fast_GET_SIZE(seq) == 3)
	{
		self->m_drot[0] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(value, 0));
		self->m_dloc[0] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(value, 1));
		self->m_bitLocalFlag.Torque = (PyInt_AsLong(PySequence_Fast_GET_ITEM(value, 2)) != 0);

		if (!PyErr_Occurred())
		{
			Py_DECREF(seq);
			return PY_SET_ATTR_SUCCESS;
		}
	}

	Py_XDECREF(seq);

	PyErr_SetString(PyExc_ValueError, "expected a sequence of 2 floats and a bool");
	return PY_SET_ATTR_FAIL;
}

PyObject* KX_ObjectActuator::pyattr_get_forceLimitY(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_ObjectActuator* self = reinterpret_cast<KX_ObjectActuator*>(self_v);
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(self->m_drot[1]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(self->m_dloc[1]));
	PyList_SET_ITEM(retVal, 2, PyBool_FromLong(self->m_bitLocalFlag.DLoc));
	
	return retVal;
}

int	KX_ObjectActuator::pyattr_set_forceLimitY(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_ObjectActuator* self = reinterpret_cast<KX_ObjectActuator*>(self_v);

	PyObject* seq = PySequence_Fast(value, "");
	if (seq && PySequence_Fast_GET_SIZE(seq) == 3)
	{
		self->m_drot[1] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(value, 0));
		self->m_dloc[1] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(value, 1));
		self->m_bitLocalFlag.DLoc = (PyInt_AsLong(PySequence_Fast_GET_ITEM(value, 2)) != 0);

		if (!PyErr_Occurred())
		{
			Py_DECREF(seq);
			return PY_SET_ATTR_SUCCESS;
		}
	}

	Py_XDECREF(seq);

	PyErr_SetString(PyExc_ValueError, "expected a sequence of 2 floats and a bool");
	return PY_SET_ATTR_FAIL;
}

PyObject* KX_ObjectActuator::pyattr_get_forceLimitZ(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_ObjectActuator* self = reinterpret_cast<KX_ObjectActuator*>(self_v);
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(self->m_drot[2]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(self->m_dloc[2]));
	PyList_SET_ITEM(retVal, 2, PyBool_FromLong(self->m_bitLocalFlag.DRot));
	
	return retVal;
}

int	KX_ObjectActuator::pyattr_set_forceLimitZ(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_ObjectActuator* self = reinterpret_cast<KX_ObjectActuator*>(self_v);

	PyObject* seq = PySequence_Fast(value, "");
	if (seq && PySequence_Fast_GET_SIZE(seq) == 3)
	{
		self->m_drot[2] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(value, 0));
		self->m_dloc[2] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(value, 1));
		self->m_bitLocalFlag.DRot = (PyInt_AsLong(PySequence_Fast_GET_ITEM(value, 2)) != 0);

		if (!PyErr_Occurred())
		{
			Py_DECREF(seq);
			return PY_SET_ATTR_SUCCESS;
		}
	}

	Py_XDECREF(seq);

	PyErr_SetString(PyExc_ValueError, "expected a sequence of 2 floats and a bool");
	return PY_SET_ATTR_FAIL;
}

PyObject* KX_ObjectActuator::pyattr_get_reference(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_ObjectActuator* actuator = static_cast<KX_ObjectActuator*>(self);
	if (!actuator->m_reference)
		Py_RETURN_NONE;
	
	return actuator->m_reference->GetProxy();
}

int KX_ObjectActuator::pyattr_set_reference(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_ObjectActuator* actuator = static_cast<KX_ObjectActuator*>(self);
	KX_GameObject *refOb;
	
	if (!ConvertPythonToGameObject(value, &refOb, true, "actu.reference = value: KX_ObjectActuator"))
		return PY_SET_ATTR_FAIL;
	
	if (actuator->m_reference)
		actuator->m_reference->UnregisterActuator(actuator);
	
	if(refOb==NULL) {
		actuator->m_reference= NULL;
	}
	else {	
		actuator->m_reference = refOb;
		actuator->m_reference->RegisterActuator(actuator);
	}
	
	return PY_SET_ATTR_SUCCESS;
}


/* 1. set ------------------------------------------------------------------ */
/* Removed! */

/* 2. getForce                                                               */
PyObject* KX_ObjectActuator::PyGetForce()
{
	ShowDeprecationWarning("getForce()", "the force and the useLocalForce properties");
	PyObject *retVal = PyList_New(4);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_force[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_force[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_force[2]));
	PyList_SET_ITEM(retVal, 3, BoolToPyArg(m_bitLocalFlag.Force));
	
	return retVal;
}
/* 3. setForce                                                               */
PyObject* KX_ObjectActuator::PySetForce(PyObject* args)
{
	ShowDeprecationWarning("setForce()", "the force and the useLocalForce properties");
	float vecArg[3];
	int bToggle = 0;
	if (!PyArg_ParseTuple(args, "fffi:setForce", &vecArg[0], &vecArg[1], 
						  &vecArg[2], &bToggle)) {
		return NULL;
	}
	m_force.setValue(vecArg);
	m_bitLocalFlag.Force = PyArgToBool(bToggle);
	UpdateFuzzyFlags();
	Py_RETURN_NONE;
}

/* 4. getTorque                                                              */
PyObject* KX_ObjectActuator::PyGetTorque()
{
	ShowDeprecationWarning("getTorque()", "the torque and the useLocalTorque properties");
	PyObject *retVal = PyList_New(4);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_torque[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_torque[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_torque[2]));
	PyList_SET_ITEM(retVal, 3, BoolToPyArg(m_bitLocalFlag.Torque));
	
	return retVal;
}
/* 5. setTorque                                                              */
PyObject* KX_ObjectActuator::PySetTorque(PyObject* args)
{
	ShowDeprecationWarning("setTorque()", "the torque and the useLocalTorque properties");
	float vecArg[3];
	int bToggle = 0;
	if (!PyArg_ParseTuple(args, "fffi:setTorque", &vecArg[0], &vecArg[1], 
						  &vecArg[2], &bToggle)) {
		return NULL;
	}
	m_torque.setValue(vecArg);
	m_bitLocalFlag.Torque = PyArgToBool(bToggle);
	UpdateFuzzyFlags();
	Py_RETURN_NONE;
}

/* 6. getDLoc                                                                */
PyObject* KX_ObjectActuator::PyGetDLoc()
{
	ShowDeprecationWarning("getDLoc()", "the dLoc and the useLocalDLoc properties");
	PyObject *retVal = PyList_New(4);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_dloc[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_dloc[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_dloc[2]));
	PyList_SET_ITEM(retVal, 3, BoolToPyArg(m_bitLocalFlag.DLoc));
	
	return retVal;
}
/* 7. setDLoc                                                                */
PyObject* KX_ObjectActuator::PySetDLoc(PyObject* args)
{
	ShowDeprecationWarning("setDLoc()", "the dLoc and the useLocalDLoc properties");
	float vecArg[3];
	int bToggle = 0;
	if(!PyArg_ParseTuple(args, "fffi:setDLoc", &vecArg[0], &vecArg[1], 
						 &vecArg[2], &bToggle)) {
		return NULL;
	}
	m_dloc.setValue(vecArg);
	m_bitLocalFlag.DLoc = PyArgToBool(bToggle);
	UpdateFuzzyFlags();
	Py_RETURN_NONE;
}

/* 8. getDRot                                                                */
PyObject* KX_ObjectActuator::PyGetDRot()
{
	ShowDeprecationWarning("getDRot()", "the dRot and the useLocalDRot properties");
	PyObject *retVal = PyList_New(4);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_drot[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_drot[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_drot[2]));
	PyList_SET_ITEM(retVal, 3, BoolToPyArg(m_bitLocalFlag.DRot));
	
	return retVal;
}
/* 9. setDRot                                                                */
PyObject* KX_ObjectActuator::PySetDRot(PyObject* args)
{
	ShowDeprecationWarning("setDRot()", "the dRot and the useLocalDRot properties");
	float vecArg[3];
	int bToggle = 0;
	if (!PyArg_ParseTuple(args, "fffi:setDRot", &vecArg[0], &vecArg[1], 
						  &vecArg[2], &bToggle)) {
		return NULL;
	}
	m_drot.setValue(vecArg);
	m_bitLocalFlag.DRot = PyArgToBool(bToggle);
	UpdateFuzzyFlags();
	Py_RETURN_NONE;
}

/* 10. getLinearVelocity                                                 */
PyObject* KX_ObjectActuator::PyGetLinearVelocity() {
	ShowDeprecationWarning("getLinearVelocity()", "the linV and the useLocalLinV properties");
	PyObject *retVal = PyList_New(4);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_linear_velocity[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_linear_velocity[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_linear_velocity[2]));
	PyList_SET_ITEM(retVal, 3, BoolToPyArg(m_bitLocalFlag.LinearVelocity));
	
	return retVal;
}

/* 11. setLinearVelocity                                                 */
PyObject* KX_ObjectActuator::PySetLinearVelocity(PyObject* args) {
	ShowDeprecationWarning("setLinearVelocity()", "the linV and the useLocalLinV properties");
	float vecArg[3];
	int bToggle = 0;
	if (!PyArg_ParseTuple(args, "fffi:setLinearVelocity", &vecArg[0], &vecArg[1], 
						  &vecArg[2], &bToggle)) {
		return NULL;
	}
	m_linear_velocity.setValue(vecArg);
	m_bitLocalFlag.LinearVelocity = PyArgToBool(bToggle);
	UpdateFuzzyFlags();
	Py_RETURN_NONE;
}


/* 12. getAngularVelocity                                                */
PyObject* KX_ObjectActuator::PyGetAngularVelocity() {
	ShowDeprecationWarning("getAngularVelocity()", "the angV and the useLocalAngV properties");
	PyObject *retVal = PyList_New(4);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_angular_velocity[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_angular_velocity[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_angular_velocity[2]));
	PyList_SET_ITEM(retVal, 3, BoolToPyArg(m_bitLocalFlag.AngularVelocity));
	
	return retVal;
}
/* 13. setAngularVelocity                                                */
PyObject* KX_ObjectActuator::PySetAngularVelocity(PyObject* args) {
	ShowDeprecationWarning("setAngularVelocity()", "the angV and the useLocalAngV properties");
	float vecArg[3];
	int bToggle = 0;
	if (!PyArg_ParseTuple(args, "fffi:setAngularVelocity", &vecArg[0], &vecArg[1], 
						  &vecArg[2], &bToggle)) {
		return NULL;
	}
	m_angular_velocity.setValue(vecArg);
	m_bitLocalFlag.AngularVelocity = PyArgToBool(bToggle);
	UpdateFuzzyFlags();
	Py_RETURN_NONE;
}

/* 13. setDamping                                                */
PyObject* KX_ObjectActuator::PySetDamping(PyObject* args) {
	ShowDeprecationWarning("setDamping()", "the damping property");
	int damping = 0;
	if (!PyArg_ParseTuple(args, "i:setDamping", &damping) || damping < 0 || damping > 1000) {
		return NULL;
	}
	m_damping = damping;
	Py_RETURN_NONE;
}

/* 13. getVelocityDamping                                                */
PyObject* KX_ObjectActuator::PyGetDamping() {
	ShowDeprecationWarning("getDamping()", "the damping property");
	return Py_BuildValue("i",m_damping);
}
/* 6. getForceLimitX                                                                */
PyObject* KX_ObjectActuator::PyGetForceLimitX()
{
	ShowDeprecationWarning("getForceLimitX()", "the forceLimitX property");
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_drot[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_dloc[0]));
	PyList_SET_ITEM(retVal, 2, BoolToPyArg(m_bitLocalFlag.Torque));
	
	return retVal;
}
/* 7. setForceLimitX                                                         */
PyObject* KX_ObjectActuator::PySetForceLimitX(PyObject* args)
{
	ShowDeprecationWarning("setForceLimitX()", "the forceLimitX property");
	float vecArg[2];
	int bToggle = 0;
	if(!PyArg_ParseTuple(args, "ffi:setForceLimitX", &vecArg[0], &vecArg[1], &bToggle)) {
		return NULL;
	}
	m_drot[0] = vecArg[0];
	m_dloc[0] = vecArg[1];
	m_bitLocalFlag.Torque = PyArgToBool(bToggle);
	Py_RETURN_NONE;
}

/* 6. getForceLimitY                                                                */
PyObject* KX_ObjectActuator::PyGetForceLimitY()
{
	ShowDeprecationWarning("getForceLimitY()", "the forceLimitY property");
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_drot[1]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_dloc[1]));
	PyList_SET_ITEM(retVal, 2, BoolToPyArg(m_bitLocalFlag.DLoc));
	
	return retVal;
}
/* 7. setForceLimitY                                                                */
PyObject* KX_ObjectActuator::PySetForceLimitY(PyObject* args)
{
	ShowDeprecationWarning("setForceLimitY()", "the forceLimitY property");
	float vecArg[2];
	int bToggle = 0;
	if(!PyArg_ParseTuple(args, "ffi:setForceLimitY", &vecArg[0], &vecArg[1], &bToggle)) {
		return NULL;
	}
	m_drot[1] = vecArg[0];
	m_dloc[1] = vecArg[1];
	m_bitLocalFlag.DLoc = PyArgToBool(bToggle);
	Py_RETURN_NONE;
}

/* 6. getForceLimitZ                                                                */
PyObject* KX_ObjectActuator::PyGetForceLimitZ()
{
	ShowDeprecationWarning("getForceLimitZ()", "the forceLimitZ property");
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_drot[2]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_dloc[2]));
	PyList_SET_ITEM(retVal, 2, BoolToPyArg(m_bitLocalFlag.DRot));
	
	return retVal;
}
/* 7. setForceLimitZ                                                                */
PyObject* KX_ObjectActuator::PySetForceLimitZ(PyObject* args)
{
	ShowDeprecationWarning("setForceLimitZ()", "the forceLimitZ property");
	float vecArg[2];
	int bToggle = 0;
	if(!PyArg_ParseTuple(args, "ffi:setForceLimitZ", &vecArg[0], &vecArg[1], &bToggle)) {
		return NULL;
	}
	m_drot[2] = vecArg[0];
	m_dloc[2] = vecArg[1];
	m_bitLocalFlag.DRot = PyArgToBool(bToggle);
	Py_RETURN_NONE;
}

/* 4. getPID                                                              */
PyObject* KX_ObjectActuator::PyGetPID()
{
	ShowDeprecationWarning("getPID()", "the pid property");
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_pid[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_pid[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_pid[2]));
	
	return retVal;
}
/* 5. setPID                                                              */
PyObject* KX_ObjectActuator::PySetPID(PyObject* args)
{
	ShowDeprecationWarning("setPID()", "the pid property");
	float vecArg[3];
	if (!PyArg_ParseTuple(args, "fff:setPID", &vecArg[0], &vecArg[1], &vecArg[2])) {
		return NULL;
	}
	m_pid.setValue(vecArg);
	Py_RETURN_NONE;
}





/* eof */
