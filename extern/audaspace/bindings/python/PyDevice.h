/*******************************************************************************
 * Copyright 2009-2016 Jörg Müller
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

#pragma once

#include <Python.h>
#include "Audaspace.h"

typedef void Reference_IDevice;

typedef struct {
	PyObject_HEAD
	Reference_IDevice* device;
} Device;

extern AUD_API PyObject* Device_empty();
extern AUD_API Device* checkDevice(PyObject* device);

bool initializeDevice();
void addDeviceToModule(PyObject* module);
