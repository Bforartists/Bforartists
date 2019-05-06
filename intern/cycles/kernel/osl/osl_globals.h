/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __OSL_GLOBALS_H__
#define __OSL_GLOBALS_H__

#ifdef WITH_OSL

#  include <OSL/oslexec.h>

#  include <OpenImageIO/refcnt.h>
#  include <OpenImageIO/unordered_map_concurrent.h>

#  include "util/util_map.h"
#  include "util/util_param.h"
#  include "util/util_thread.h"
#  include "util/util_vector.h"
#  include "util/util_unique_ptr.h"

#  ifndef WIN32
using std::isfinite;
#  endif

CCL_NAMESPACE_BEGIN

class OSLRenderServices;
class ColorSpaceProcessor;

/* OSL Texture Handle
 *
 * OSL texture lookups are string based. If those strings are known at compile
 * time, the OSL compiler can cache a texture handle to use instead of a string.
 *
 * By default it uses TextureSystem::TextureHandle. But since we want to support
 * different kinds of textures and color space conversions, this is our own handle
 * with additional data.
 *
 * These are stored in a concurrent hash map, because OSL can compile multiple
 * shaders in parallel. */

struct OSLTextureHandle : public OIIO::RefCnt {
  enum Type { OIIO, SVM, IES, BEVEL, AO };

  OSLTextureHandle(Type type = OIIO, int svm_slot = -1)
      : type(type), svm_slot(svm_slot), oiio_handle(NULL), processor(NULL)
  {
  }

  Type type;
  int svm_slot;
  OSL::TextureSystem::TextureHandle *oiio_handle;
  ColorSpaceProcessor *processor;
};

typedef OIIO::intrusive_ptr<OSLTextureHandle> OSLTextureHandleRef;
typedef OIIO::unordered_map_concurrent<ustring, OSLTextureHandleRef, ustringHash>
    OSLTextureHandleMap;

/* OSL Globals
 *
 * Data needed by OSL render services, that is global to a rendering session.
 * This includes all OSL shaders, name to attribute mapping and texture handles.
 * */

struct OSLGlobals {
  OSLGlobals()
  {
    ss = NULL;
    ts = NULL;
    services = NULL;
    use = false;
  }

  bool use;

  /* shading system */
  OSL::ShadingSystem *ss;
  OSL::TextureSystem *ts;
  OSLRenderServices *services;

  /* shader states */
  vector<OSL::ShaderGroupRef> surface_state;
  vector<OSL::ShaderGroupRef> volume_state;
  vector<OSL::ShaderGroupRef> displacement_state;
  vector<OSL::ShaderGroupRef> bump_state;
  OSL::ShaderGroupRef background_state;

  /* attributes */
  struct Attribute {
    TypeDesc type;
    AttributeDescriptor desc;
    ParamValue value;
  };

  typedef unordered_map<ustring, Attribute, ustringHash> AttributeMap;
  typedef unordered_map<ustring, int, ustringHash> ObjectNameMap;

  vector<AttributeMap> attribute_map;
  ObjectNameMap object_name_map;
  vector<ustring> object_names;

  /* textures */
  OSLTextureHandleMap textures;
};

/* trace() call result */
struct OSLTraceData {
  Ray ray;
  Intersection isect;
  ShaderData sd;
  bool setup;
  bool init;
};

/* thread key for thread specific data lookup */
struct OSLThreadData {
  OSL::ShaderGlobals globals;
  OSL::PerThreadInfo *osl_thread_info;
  OSLTraceData tracedata;
  OSL::ShadingContext *context;
  OIIO::TextureSystem::Perthread *oiio_thread_info;
};

CCL_NAMESPACE_END

#endif

#endif /* __OSL_GLOBALS_H__ */
