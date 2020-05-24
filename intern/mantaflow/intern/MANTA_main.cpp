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
 *
 * The Original Code is Copyright (C) 2016 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup mantaflow
 */

#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <zlib.h>

#if OPENVDB == 1
#  include "openvdb/openvdb.h"
#endif

#include "MANTA_main.h"
#include "Python.h"
#include "fluid_script.h"
#include "liquid_script.h"
#include "manta.h"
#include "smoke_script.h"

#include "BLI_fileops.h"
#include "BLI_path_util.h"
#include "BLI_utildefines.h"

#include "DNA_fluid_types.h"
#include "DNA_modifier_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

using std::cerr;
using std::cout;
using std::endl;
using std::ifstream;
using std::istringstream;
using std::ofstream;
using std::ostringstream;
using std::to_string;

atomic<int> MANTA::solverID(0);
int MANTA::with_debug(0);

/* Number of particles that the cache reads at once (with zlib). */
#define PARTICLE_CHUNK 20000
/* Number of mesh nodes that the cache reads at once (with zlib). */
#define NODE_CHUNK 20000
/* Number of mesh triangles that the cache reads at once (with zlib). */
#define TRIANGLE_CHUNK 20000

MANTA::MANTA(int *res, FluidModifierData *mmd) : mCurrentID(++solverID)
{
  if (with_debug)
    cout << "FLUID: " << mCurrentID << " with res(" << res[0] << ", " << res[1] << ", " << res[2]
         << ")" << endl;

  FluidDomainSettings *mds = mmd->domain;
  mds->fluid = this;

  mUsingLiquid = (mds->type == FLUID_DOMAIN_TYPE_LIQUID);
  mUsingSmoke = (mds->type == FLUID_DOMAIN_TYPE_GAS);
  mUsingNoise = (mds->flags & FLUID_DOMAIN_USE_NOISE) && mUsingSmoke;
  mUsingFractions = (mds->flags & FLUID_DOMAIN_USE_FRACTIONS) && mUsingLiquid;
  mUsingMesh = (mds->flags & FLUID_DOMAIN_USE_MESH) && mUsingLiquid;
  mUsingDiffusion = (mds->flags & FLUID_DOMAIN_USE_DIFFUSION) && mUsingLiquid;
  mUsingMVel = (mds->flags & FLUID_DOMAIN_USE_SPEED_VECTORS) && mUsingLiquid;
  mUsingGuiding = (mds->flags & FLUID_DOMAIN_USE_GUIDE);
  mUsingDrops = (mds->particle_type & FLUID_DOMAIN_PARTICLE_SPRAY) && mUsingLiquid;
  mUsingBubbles = (mds->particle_type & FLUID_DOMAIN_PARTICLE_BUBBLE) && mUsingLiquid;
  mUsingFloats = (mds->particle_type & FLUID_DOMAIN_PARTICLE_FOAM) && mUsingLiquid;
  mUsingTracers = (mds->particle_type & FLUID_DOMAIN_PARTICLE_TRACER) && mUsingLiquid;

  mUsingHeat = (mds->active_fields & FLUID_DOMAIN_ACTIVE_HEAT) && mUsingSmoke;
  mUsingFire = (mds->active_fields & FLUID_DOMAIN_ACTIVE_FIRE) && mUsingSmoke;
  mUsingColors = (mds->active_fields & FLUID_DOMAIN_ACTIVE_COLORS) && mUsingSmoke;
  mUsingObstacle = (mds->active_fields & FLUID_DOMAIN_ACTIVE_OBSTACLE);
  mUsingInvel = (mds->active_fields & FLUID_DOMAIN_ACTIVE_INVEL);
  mUsingOutflow = (mds->active_fields & FLUID_DOMAIN_ACTIVE_OUTFLOW);

  // Simulation constants
  mTempAmb = 0;  // TODO: Maybe use this later for buoyancy calculation
  mResX = res[0];
  mResY = res[1];
  mResZ = res[2];
  mMaxRes = MAX3(mResX, mResY, mResZ);
  mTotalCells = mResX * mResY * mResZ;
  mResGuiding = mds->res;

  // Smoke low res grids
  mDensity = nullptr;
  mShadow = nullptr;
  mHeat = nullptr;
  mVelocityX = nullptr;
  mVelocityY = nullptr;
  mVelocityZ = nullptr;
  mForceX = nullptr;
  mForceY = nullptr;
  mForceZ = nullptr;
  mFlame = nullptr;
  mFuel = nullptr;
  mReact = nullptr;
  mColorR = nullptr;
  mColorG = nullptr;
  mColorB = nullptr;
  mFlags = nullptr;
  mDensityIn = nullptr;
  mHeatIn = nullptr;
  mColorRIn = nullptr;
  mColorGIn = nullptr;
  mColorBIn = nullptr;
  mFuelIn = nullptr;
  mReactIn = nullptr;
  mEmissionIn = nullptr;

  // Smoke high res grids
  mDensityHigh = nullptr;
  mFlameHigh = nullptr;
  mFuelHigh = nullptr;
  mReactHigh = nullptr;
  mColorRHigh = nullptr;
  mColorGHigh = nullptr;
  mColorBHigh = nullptr;
  mTextureU = nullptr;
  mTextureV = nullptr;
  mTextureW = nullptr;
  mTextureU2 = nullptr;
  mTextureV2 = nullptr;
  mTextureW2 = nullptr;

  // Fluid low res grids
  mPhiIn = nullptr;
  mPhiStaticIn = nullptr;
  mPhiOutIn = nullptr;
  mPhiOutStaticIn = nullptr;
  mPhi = nullptr;

  // Mesh
  mMeshNodes = nullptr;
  mMeshTriangles = nullptr;
  mMeshVelocities = nullptr;

  // Fluid obstacle
  mPhiObsIn = nullptr;
  mPhiObsStaticIn = nullptr;
  mNumObstacle = nullptr;
  mObVelocityX = nullptr;
  mObVelocityY = nullptr;
  mObVelocityZ = nullptr;

  // Fluid guiding
  mPhiGuideIn = nullptr;
  mNumGuide = nullptr;
  mGuideVelocityX = nullptr;
  mGuideVelocityY = nullptr;
  mGuideVelocityZ = nullptr;

  // Fluid initial velocity
  mInVelocityX = nullptr;
  mInVelocityY = nullptr;
  mInVelocityZ = nullptr;

  // Secondary particles
  mFlipParticleData = nullptr;
  mFlipParticleVelocity = nullptr;
  mSndParticleData = nullptr;
  mSndParticleVelocity = nullptr;
  mSndParticleLife = nullptr;

  // Cache read success indicators
  mFlipFromFile = false;
  mMeshFromFile = false;
  mParticlesFromFile = false;

  // Setup Mantaflow in Python
  initializeMantaflow();

  // Initializa RNA map with values that Python will need
  initializeRNAMap(mmd);

  // Initialize Mantaflow variables in Python
  // Liquid
  if (mUsingLiquid) {
    initDomain();
    initLiquid();
    if (mUsingObstacle)
      initObstacle();
    if (mUsingInvel)
      initInVelocity();
    if (mUsingOutflow)
      initOutflow();

    if (mUsingDrops || mUsingBubbles || mUsingFloats || mUsingTracers) {
      mUpresParticle = mds->particle_scale;
      mResXParticle = mUpresParticle * mResX;
      mResYParticle = mUpresParticle * mResY;
      mResZParticle = mUpresParticle * mResZ;
      mTotalCellsParticles = mResXParticle * mResYParticle * mResZParticle;

      initSndParts();
      initLiquidSndParts();
    }

    if (mUsingMesh) {
      mUpresMesh = mds->mesh_scale;
      mResXMesh = mUpresMesh * mResX;
      mResYMesh = mUpresMesh * mResY;
      mResZMesh = mUpresMesh * mResZ;
      mTotalCellsMesh = mResXMesh * mResYMesh * mResZMesh;

      // Initialize Mantaflow variables in Python
      initMesh();
      initLiquidMesh();
    }

    if (mUsingDiffusion) {
      initCurvature();
    }

    if (mUsingGuiding) {
      mResGuiding = (mds->guide_parent) ? mds->guide_res : mds->res;
      initGuiding();
    }
    if (mUsingFractions) {
      initFractions();
    }
  }

  // Smoke
  if (mUsingSmoke) {
    initDomain();
    initSmoke();
    if (mUsingHeat)
      initHeat();
    if (mUsingFire)
      initFire();
    if (mUsingColors)
      initColors();
    if (mUsingObstacle)
      initObstacle();
    if (mUsingInvel)
      initInVelocity();
    if (mUsingOutflow)
      initOutflow();

    if (mUsingGuiding) {
      mResGuiding = (mds->guide_parent) ? mds->guide_res : mds->res;
      initGuiding();
    }

    if (mUsingNoise) {
      int amplify = mds->noise_scale;
      mResXNoise = amplify * mResX;
      mResYNoise = amplify * mResY;
      mResZNoise = amplify * mResZ;
      mTotalCellsHigh = mResXNoise * mResYNoise * mResZNoise;

      // Initialize Mantaflow variables in Python
      initNoise();
      initSmokeNoise();
      if (mUsingFire)
        initFireHigh();
      if (mUsingColors)
        initColorsHigh();
    }
  }
  updatePointers();
}

void MANTA::initDomain(FluidModifierData *mmd)
{
  // Vector will hold all python commands that are to be executed
  vector<string> pythonCommands;

  // Set manta debug level first
  pythonCommands.push_back(manta_import + manta_debuglevel);

  ostringstream ss;
  ss << "set_manta_debuglevel(" << with_debug << ")";
  pythonCommands.push_back(ss.str());

  // Now init basic fluid domain
  string tmpString = fluid_variables + fluid_solver + fluid_alloc + fluid_cache_helper +
                     fluid_bake_multiprocessing + fluid_bake_data + fluid_bake_noise +
                     fluid_bake_mesh + fluid_bake_particles + fluid_bake_guiding +
                     fluid_file_import + fluid_file_export + fluid_save_data + fluid_load_data +
                     fluid_pre_step + fluid_post_step + fluid_adapt_time_step +
                     fluid_time_stepping;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);
  runPythonString(pythonCommands);
}

void MANTA::initNoise(FluidModifierData *mmd)
{
  vector<string> pythonCommands;
  string tmpString = fluid_variables_noise + fluid_solver_noise;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
}

void MANTA::initSmoke(FluidModifierData *mmd)
{
  vector<string> pythonCommands;
  string tmpString = smoke_variables + smoke_alloc + smoke_adaptive_step + smoke_save_data +
                     smoke_load_data + smoke_step;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
}

void MANTA::initSmokeNoise(FluidModifierData *mmd)
{
  vector<string> pythonCommands;
  string tmpString = smoke_variables_noise + smoke_alloc_noise + smoke_wavelet_noise +
                     smoke_save_noise + smoke_load_noise + smoke_step_noise;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
  mUsingNoise = true;
}

void MANTA::initHeat(FluidModifierData *mmd)
{
  if (!mHeat) {
    vector<string> pythonCommands;
    string tmpString = smoke_alloc_heat + smoke_with_heat;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingHeat = true;
  }
}

void MANTA::initFire(FluidModifierData *mmd)
{
  if (!mFuel) {
    vector<string> pythonCommands;
    string tmpString = smoke_alloc_fire + smoke_with_fire;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingFire = true;
  }
}

void MANTA::initFireHigh(FluidModifierData *mmd)
{
  if (!mFuelHigh) {
    vector<string> pythonCommands;
    string tmpString = smoke_alloc_fire_noise + smoke_with_fire;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingFire = true;
  }
}

void MANTA::initColors(FluidModifierData *mmd)
{
  if (!mColorR) {
    vector<string> pythonCommands;
    string tmpString = smoke_alloc_colors + smoke_init_colors + smoke_with_colors;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingColors = true;
  }
}

void MANTA::initColorsHigh(FluidModifierData *mmd)
{
  if (!mColorRHigh) {
    vector<string> pythonCommands;
    string tmpString = smoke_alloc_colors_noise + smoke_init_colors_noise + smoke_with_colors;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingColors = true;
  }
}

void MANTA::initLiquid(FluidModifierData *mmd)
{
  if (!mPhiIn) {
    vector<string> pythonCommands;
    string tmpString = liquid_variables + liquid_alloc + liquid_init_phi + liquid_save_data +
                       liquid_load_data + liquid_adaptive_step + liquid_step;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingLiquid = true;
  }
}

void MANTA::initMesh(FluidModifierData *mmd)
{
  vector<string> pythonCommands;
  string tmpString = fluid_variables_mesh + fluid_solver_mesh + liquid_load_mesh;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
  mUsingMesh = true;
}

void MANTA::initLiquidMesh(FluidModifierData *mmd)
{
  vector<string> pythonCommands;
  string tmpString = liquid_alloc_mesh + liquid_step_mesh + liquid_save_mesh;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
  mUsingMesh = true;
}

void MANTA::initCurvature(FluidModifierData *mmd)
{
  std::vector<std::string> pythonCommands;
  std::string finalString = parseScript(liquid_alloc_curvature, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
  mUsingDiffusion = true;
}

void MANTA::initObstacle(FluidModifierData *mmd)
{
  if (!mPhiObsIn) {
    vector<string> pythonCommands;
    string tmpString = fluid_alloc_obstacle + fluid_with_obstacle;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingObstacle = true;
  }
}

void MANTA::initGuiding(FluidModifierData *mmd)
{
  if (!mPhiGuideIn) {
    vector<string> pythonCommands;
    string tmpString = fluid_variables_guiding + fluid_solver_guiding + fluid_alloc_guiding +
                       fluid_save_guiding + fluid_load_vel + fluid_load_guiding;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingGuiding = true;
  }
}

void MANTA::initFractions(FluidModifierData *mmd)
{
  vector<string> pythonCommands;
  string tmpString = fluid_alloc_fractions + fluid_with_fractions;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
  mUsingFractions = true;
}

void MANTA::initInVelocity(FluidModifierData *mmd)
{
  if (!mInVelocityX) {
    vector<string> pythonCommands;
    string tmpString = fluid_alloc_invel + fluid_with_invel;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingInvel = true;
  }
}

void MANTA::initOutflow(FluidModifierData *mmd)
{
  if (!mPhiOutIn) {
    vector<string> pythonCommands;
    string tmpString = fluid_alloc_outflow + fluid_with_outflow;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
    mUsingOutflow = true;
  }
}

void MANTA::initSndParts(FluidModifierData *mmd)
{
  vector<string> pythonCommands;
  string tmpString = fluid_variables_particles + fluid_solver_particles;
  string finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  runPythonString(pythonCommands);
}

void MANTA::initLiquidSndParts(FluidModifierData *mmd)
{
  if (!mSndParticleData) {
    vector<string> pythonCommands;
    string tmpString = liquid_alloc_particles + liquid_variables_particles +
                       liquid_step_particles + fluid_with_sndparts + liquid_load_particles +
                       liquid_save_particles;
    string finalString = parseScript(tmpString, mmd);
    pythonCommands.push_back(finalString);

    runPythonString(pythonCommands);
  }
}

MANTA::~MANTA()
{
  if (with_debug)
    cout << "~FLUID: " << mCurrentID << " with res(" << mResX << ", " << mResY << ", " << mResZ
         << ")" << endl;

  // Destruction string for Python
  string tmpString = "";
  vector<string> pythonCommands;
  bool result = false;

  tmpString += manta_import;
  tmpString += fluid_delete_all;

  // Initializa RNA map with values that Python will need
  initializeRNAMap();

  // Leave out mmd argument in parseScript since only looking up IDs
  string finalString = parseScript(tmpString);
  pythonCommands.push_back(finalString);
  result = runPythonString(pythonCommands);

  assert(result);
  UNUSED_VARS(result);
}

/**
 * Store a pointer to the __main__ module used by mantaflow. This is necessary, because sometimes
 * Blender will overwrite that module. That happens when e.g. scripts are executed in the text
 * editor.
 *
 * Mantaflow stores many variables in the globals() dict of the __main__ module. To be able to
 * access these variables, the same __main__ module has to be used every time.
 *
 * Unfortunately, we also depend on the fact that mantaflow dumps variables into this module using
 * PyRun_SimpleString. So we can't easily create a separate module without changing mantaflow.
 */
static PyObject *manta_main_module = nullptr;

bool MANTA::runPythonString(vector<string> commands)
{
  bool success = true;
  PyGILState_STATE gilstate = PyGILState_Ensure();

  if (manta_main_module == nullptr) {
    manta_main_module = PyImport_ImportModule("__main__");
  }

  for (vector<string>::iterator it = commands.begin(); it != commands.end(); ++it) {
    string command = *it;

    PyObject *globals_dict = PyModule_GetDict(manta_main_module);
    PyObject *return_value = PyRun_String(
        command.c_str(), Py_file_input, globals_dict, globals_dict);

    if (return_value == nullptr) {
      success = false;
      if (PyErr_Occurred()) {
        PyErr_Print();
      }
    }
    else {
      Py_DECREF(return_value);
    }
  }
  PyGILState_Release(gilstate);

  assert(success);
  return success;
}

void MANTA::initializeMantaflow()
{
  if (with_debug)
    cout << "Fluid: Initializing Mantaflow framework" << endl;

  string filename = "manta_scene_" + to_string(mCurrentID) + ".py";
  vector<string> fill = vector<string>();

  // Initialize extension classes and wrappers
  srand(0);
  PyGILState_STATE gilstate = PyGILState_Ensure();
  Pb::setup(filename, fill);  // Namespace from Mantaflow (registry)
  PyGILState_Release(gilstate);
}

void MANTA::terminateMantaflow()
{
  if (with_debug)
    cout << "Fluid: Releasing Mantaflow framework" << endl;

  PyGILState_STATE gilstate = PyGILState_Ensure();
  Pb::finalize();  // Namespace from Mantaflow (registry)
  PyGILState_Release(gilstate);
}

static string getCacheFileEnding(char cache_format)
{
  if (MANTA::with_debug)
    cout << "MANTA::getCacheFileEnding()" << endl;

  switch (cache_format) {
    case FLUID_DOMAIN_FILE_UNI:
      return FLUID_DOMAIN_EXTENSION_UNI;
    case FLUID_DOMAIN_FILE_OPENVDB:
      return FLUID_DOMAIN_EXTENSION_OPENVDB;
    case FLUID_DOMAIN_FILE_RAW:
      return FLUID_DOMAIN_EXTENSION_RAW;
    case FLUID_DOMAIN_FILE_BIN_OBJECT:
      return FLUID_DOMAIN_EXTENSION_BINOBJ;
    case FLUID_DOMAIN_FILE_OBJECT:
      return FLUID_DOMAIN_EXTENSION_OBJ;
    default:
      cerr << "Fluid Error -- Could not find file extension. Using default file extension."
           << endl;
      return FLUID_DOMAIN_EXTENSION_UNI;
  }
}

static string getBooleanString(int value)
{
  return (value) ? "True" : "False";
}

void MANTA::initializeRNAMap(FluidModifierData *mmd)
{
  if (with_debug)
    cout << "MANTA::initializeRNAMap()" << endl;

  mRNAMap["ID"] = to_string(mCurrentID);

  if (!mmd) {
    if (with_debug)
      cout << "No modifier data given in RNA map setup - returning early" << endl;
    return;
  }

  FluidDomainSettings *mds = mmd->domain;
  bool is2D = (mds->solver_res == 2);

  string borderCollisions = "";
  if ((mds->border_collisions & FLUID_DOMAIN_BORDER_LEFT) == 0)
    borderCollisions += "x";
  if ((mds->border_collisions & FLUID_DOMAIN_BORDER_RIGHT) == 0)
    borderCollisions += "X";
  if ((mds->border_collisions & FLUID_DOMAIN_BORDER_FRONT) == 0)
    borderCollisions += "y";
  if ((mds->border_collisions & FLUID_DOMAIN_BORDER_BACK) == 0)
    borderCollisions += "Y";
  if ((mds->border_collisions & FLUID_DOMAIN_BORDER_BOTTOM) == 0)
    borderCollisions += "z";
  if ((mds->border_collisions & FLUID_DOMAIN_BORDER_TOP) == 0)
    borderCollisions += "Z";

  string simulationMethod = "";
  if (mds->simulation_method & FLUID_DOMAIN_METHOD_FLIP)
    simulationMethod += "'FLIP'";
  else if (mds->simulation_method & FLUID_DOMAIN_METHOD_APIC)
    simulationMethod += "'APIC'";

  string particleTypesStr = "";
  if (mds->particle_type & FLUID_DOMAIN_PARTICLE_SPRAY)
    particleTypesStr += "PtypeSpray";
  if (mds->particle_type & FLUID_DOMAIN_PARTICLE_BUBBLE) {
    if (!particleTypesStr.empty())
      particleTypesStr += "|";
    particleTypesStr += "PtypeBubble";
  }
  if (mds->particle_type & FLUID_DOMAIN_PARTICLE_FOAM) {
    if (!particleTypesStr.empty())
      particleTypesStr += "|";
    particleTypesStr += "PtypeFoam";
  }
  if (mds->particle_type & FLUID_DOMAIN_PARTICLE_TRACER) {
    if (!particleTypesStr.empty())
      particleTypesStr += "|";
    particleTypesStr += "PtypeTracer";
  }
  if (particleTypesStr.empty())
    particleTypesStr = "0";

  int particleTypes = (FLUID_DOMAIN_PARTICLE_SPRAY | FLUID_DOMAIN_PARTICLE_BUBBLE |
                       FLUID_DOMAIN_PARTICLE_FOAM | FLUID_DOMAIN_PARTICLE_TRACER);

  string cacheDirectory(mds->cache_directory);

  float viscosity = mds->viscosity_base * pow(10.0f, -mds->viscosity_exponent);
  float domainSize = MAX3(mds->global_size[0], mds->global_size[1], mds->global_size[2]);

  mRNAMap["USING_SMOKE"] = getBooleanString(mds->type == FLUID_DOMAIN_TYPE_GAS);
  mRNAMap["USING_LIQUID"] = getBooleanString(mds->type == FLUID_DOMAIN_TYPE_LIQUID);
  mRNAMap["USING_COLORS"] = getBooleanString(mds->active_fields & FLUID_DOMAIN_ACTIVE_COLORS);
  mRNAMap["USING_HEAT"] = getBooleanString(mds->active_fields & FLUID_DOMAIN_ACTIVE_HEAT);
  mRNAMap["USING_FIRE"] = getBooleanString(mds->active_fields & FLUID_DOMAIN_ACTIVE_FIRE);
  mRNAMap["USING_NOISE"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_NOISE);
  mRNAMap["USING_OBSTACLE"] = getBooleanString(mds->active_fields & FLUID_DOMAIN_ACTIVE_OBSTACLE);
  mRNAMap["USING_GUIDING"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_GUIDE);
  mRNAMap["USING_INVEL"] = getBooleanString(mds->active_fields & FLUID_DOMAIN_ACTIVE_INVEL);
  mRNAMap["USING_OUTFLOW"] = getBooleanString(mds->active_fields & FLUID_DOMAIN_ACTIVE_OUTFLOW);
  mRNAMap["USING_LOG_DISSOLVE"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_DISSOLVE_LOG);
  mRNAMap["USING_DISSOLVE"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_DISSOLVE);
  mRNAMap["DO_OPEN"] = getBooleanString(mds->border_collisions == 0);
  mRNAMap["CACHE_RESUMABLE"] = getBooleanString(mds->cache_type != FLUID_DOMAIN_CACHE_FINAL);
  mRNAMap["USING_ADAPTIVETIME"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_ADAPTIVE_TIME);
  mRNAMap["USING_SPEEDVECTORS"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_SPEED_VECTORS);
  mRNAMap["USING_FRACTIONS"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_FRACTIONS);
  mRNAMap["DELETE_IN_OBSTACLE"] = getBooleanString(mds->flags & FLUID_DOMAIN_DELETE_IN_OBSTACLE);
  mRNAMap["USING_DIFFUSION"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_DIFFUSION);
  mRNAMap["USING_MESH"] = getBooleanString(mds->flags & FLUID_DOMAIN_USE_MESH);
  mRNAMap["USING_IMPROVED_MESH"] = getBooleanString(mds->mesh_generator ==
                                                    FLUID_DOMAIN_MESH_IMPROVED);
  mRNAMap["USING_SNDPARTS"] = getBooleanString(mds->particle_type & particleTypes);
  mRNAMap["SNDPARTICLE_BOUNDARY_DELETE"] = getBooleanString(mds->sndparticle_boundary ==
                                                            SNDPARTICLE_BOUNDARY_DELETE);
  mRNAMap["SNDPARTICLE_BOUNDARY_PUSHOUT"] = getBooleanString(mds->sndparticle_boundary ==
                                                             SNDPARTICLE_BOUNDARY_PUSHOUT);

  mRNAMap["SOLVER_DIM"] = to_string(mds->solver_res);
  mRNAMap["BOUND_CONDITIONS"] = borderCollisions;
  mRNAMap["BOUNDARY_WIDTH"] = to_string(mds->boundary_width);
  mRNAMap["RES"] = to_string(mMaxRes);
  mRNAMap["RESX"] = to_string(mResX);
  mRNAMap["RESY"] = (is2D) ? to_string(mResZ) : to_string(mResY);
  mRNAMap["RESZ"] = (is2D) ? to_string(1) : to_string(mResZ);
  mRNAMap["TIME_SCALE"] = to_string(mds->time_scale);
  mRNAMap["FRAME_LENGTH"] = to_string(mds->frame_length);
  mRNAMap["CFL"] = to_string(mds->cfl_condition);
  mRNAMap["DT"] = to_string(mds->dt);
  mRNAMap["TIMESTEPS_MIN"] = to_string(mds->timesteps_minimum);
  mRNAMap["TIMESTEPS_MAX"] = to_string(mds->timesteps_maximum);
  mRNAMap["TIME_TOTAL"] = to_string(mds->time_total);
  mRNAMap["TIME_PER_FRAME"] = to_string(mds->time_per_frame);
  mRNAMap["VORTICITY"] = to_string(mds->vorticity);
  mRNAMap["FLAME_VORTICITY"] = to_string(mds->flame_vorticity);
  mRNAMap["NOISE_SCALE"] = to_string(mds->noise_scale);
  mRNAMap["MESH_SCALE"] = to_string(mds->mesh_scale);
  mRNAMap["PARTICLE_SCALE"] = to_string(mds->particle_scale);
  mRNAMap["NOISE_RESX"] = to_string(mResXNoise);
  mRNAMap["NOISE_RESY"] = (is2D) ? to_string(mResZNoise) : to_string(mResYNoise);
  mRNAMap["NOISE_RESZ"] = (is2D) ? to_string(1) : to_string(mResZNoise);
  mRNAMap["MESH_RESX"] = to_string(mResXMesh);
  mRNAMap["MESH_RESY"] = (is2D) ? to_string(mResZMesh) : to_string(mResYMesh);
  mRNAMap["MESH_RESZ"] = (is2D) ? to_string(1) : to_string(mResZMesh);
  mRNAMap["PARTICLE_RESX"] = to_string(mResXParticle);
  mRNAMap["PARTICLE_RESY"] = (is2D) ? to_string(mResZParticle) : to_string(mResYParticle);
  mRNAMap["PARTICLE_RESZ"] = (is2D) ? to_string(1) : to_string(mResZParticle);
  mRNAMap["GUIDING_RESX"] = to_string(mResGuiding[0]);
  mRNAMap["GUIDING_RESY"] = (is2D) ? to_string(mResGuiding[2]) : to_string(mResGuiding[1]);
  mRNAMap["GUIDING_RESZ"] = (is2D) ? to_string(1) : to_string(mResGuiding[2]);
  mRNAMap["MIN_RESX"] = to_string(mds->res_min[0]);
  mRNAMap["MIN_RESY"] = to_string(mds->res_min[1]);
  mRNAMap["MIN_RESZ"] = to_string(mds->res_min[2]);
  mRNAMap["BASE_RESX"] = to_string(mds->base_res[0]);
  mRNAMap["BASE_RESY"] = to_string(mds->base_res[1]);
  mRNAMap["BASE_RESZ"] = to_string(mds->base_res[2]);
  mRNAMap["WLT_STR"] = to_string(mds->noise_strength);
  mRNAMap["NOISE_POSSCALE"] = to_string(mds->noise_pos_scale);
  mRNAMap["NOISE_TIMEANIM"] = to_string(mds->noise_time_anim);
  mRNAMap["COLOR_R"] = to_string(mds->active_color[0]);
  mRNAMap["COLOR_G"] = to_string(mds->active_color[1]);
  mRNAMap["COLOR_B"] = to_string(mds->active_color[2]);
  mRNAMap["BUOYANCY_ALPHA"] = to_string(mds->alpha);
  mRNAMap["BUOYANCY_BETA"] = to_string(mds->beta);
  mRNAMap["DISSOLVE_SPEED"] = to_string(mds->diss_speed);
  mRNAMap["BURNING_RATE"] = to_string(mds->burning_rate);
  mRNAMap["FLAME_SMOKE"] = to_string(mds->flame_smoke);
  mRNAMap["IGNITION_TEMP"] = to_string(mds->flame_ignition);
  mRNAMap["MAX_TEMP"] = to_string(mds->flame_max_temp);
  mRNAMap["FLAME_SMOKE_COLOR_X"] = to_string(mds->flame_smoke_color[0]);
  mRNAMap["FLAME_SMOKE_COLOR_Y"] = to_string(mds->flame_smoke_color[1]);
  mRNAMap["FLAME_SMOKE_COLOR_Z"] = to_string(mds->flame_smoke_color[2]);
  mRNAMap["CURRENT_FRAME"] = to_string(int(mmd->time));
  mRNAMap["START_FRAME"] = to_string(mds->cache_frame_start);
  mRNAMap["END_FRAME"] = to_string(mds->cache_frame_end);
  mRNAMap["CACHE_DATA_FORMAT"] = getCacheFileEnding(mds->cache_data_format);
  mRNAMap["CACHE_MESH_FORMAT"] = getCacheFileEnding(mds->cache_mesh_format);
  mRNAMap["CACHE_NOISE_FORMAT"] = getCacheFileEnding(mds->cache_noise_format);
  mRNAMap["CACHE_PARTICLE_FORMAT"] = getCacheFileEnding(mds->cache_particle_format);
  mRNAMap["SIMULATION_METHOD"] = simulationMethod;
  mRNAMap["FLIP_RATIO"] = to_string(mds->flip_ratio);
  mRNAMap["PARTICLE_RANDOMNESS"] = to_string(mds->particle_randomness);
  mRNAMap["PARTICLE_NUMBER"] = to_string(mds->particle_number);
  mRNAMap["PARTICLE_MINIMUM"] = to_string(mds->particle_minimum);
  mRNAMap["PARTICLE_MAXIMUM"] = to_string(mds->particle_maximum);
  mRNAMap["PARTICLE_RADIUS"] = to_string(mds->particle_radius);
  mRNAMap["FRACTIONS_THRESHOLD"] = to_string(mds->fractions_threshold);
  mRNAMap["MESH_CONCAVE_UPPER"] = to_string(mds->mesh_concave_upper);
  mRNAMap["MESH_CONCAVE_LOWER"] = to_string(mds->mesh_concave_lower);
  mRNAMap["MESH_PARTICLE_RADIUS"] = to_string(mds->mesh_particle_radius);
  mRNAMap["MESH_SMOOTHEN_POS"] = to_string(mds->mesh_smoothen_pos);
  mRNAMap["MESH_SMOOTHEN_NEG"] = to_string(mds->mesh_smoothen_neg);
  mRNAMap["PARTICLE_BAND_WIDTH"] = to_string(mds->particle_band_width);
  mRNAMap["SNDPARTICLE_TAU_MIN_WC"] = to_string(mds->sndparticle_tau_min_wc);
  mRNAMap["SNDPARTICLE_TAU_MAX_WC"] = to_string(mds->sndparticle_tau_max_wc);
  mRNAMap["SNDPARTICLE_TAU_MIN_TA"] = to_string(mds->sndparticle_tau_min_ta);
  mRNAMap["SNDPARTICLE_TAU_MAX_TA"] = to_string(mds->sndparticle_tau_max_ta);
  mRNAMap["SNDPARTICLE_TAU_MIN_K"] = to_string(mds->sndparticle_tau_min_k);
  mRNAMap["SNDPARTICLE_TAU_MAX_K"] = to_string(mds->sndparticle_tau_max_k);
  mRNAMap["SNDPARTICLE_K_WC"] = to_string(mds->sndparticle_k_wc);
  mRNAMap["SNDPARTICLE_K_TA"] = to_string(mds->sndparticle_k_ta);
  mRNAMap["SNDPARTICLE_K_B"] = to_string(mds->sndparticle_k_b);
  mRNAMap["SNDPARTICLE_K_D"] = to_string(mds->sndparticle_k_d);
  mRNAMap["SNDPARTICLE_L_MIN"] = to_string(mds->sndparticle_l_min);
  mRNAMap["SNDPARTICLE_L_MAX"] = to_string(mds->sndparticle_l_max);
  mRNAMap["SNDPARTICLE_POTENTIAL_RADIUS"] = to_string(mds->sndparticle_potential_radius);
  mRNAMap["SNDPARTICLE_UPDATE_RADIUS"] = to_string(mds->sndparticle_update_radius);
  mRNAMap["LIQUID_SURFACE_TENSION"] = to_string(mds->surface_tension);
  mRNAMap["FLUID_VISCOSITY"] = to_string(viscosity);
  mRNAMap["FLUID_DOMAIN_SIZE"] = to_string(domainSize);
  mRNAMap["SNDPARTICLE_TYPES"] = particleTypesStr;
  mRNAMap["GUIDING_ALPHA"] = to_string(mds->guide_alpha);
  mRNAMap["GUIDING_BETA"] = to_string(mds->guide_beta);
  mRNAMap["GUIDING_FACTOR"] = to_string(mds->guide_vel_factor);
  mRNAMap["GRAVITY_X"] = to_string(mds->gravity[0]);
  mRNAMap["GRAVITY_Y"] = to_string(mds->gravity[1]);
  mRNAMap["GRAVITY_Z"] = to_string(mds->gravity[2]);
  mRNAMap["CACHE_DIR"] = cacheDirectory;
  mRNAMap["NAME_DENSITY"] = FLUID_GRIDNAME_DENSITY;
  mRNAMap["NAME_SHADOW"] = FLUID_GRIDNAME_SHADOW;
  mRNAMap["NAME_HEAT"] = FLUID_GRIDNAME_HEAT;
  mRNAMap["NAME_VELOCITY"] = FLUID_GRIDNAME_VELOCITY;
  mRNAMap["NAME_COLORR"] = FLUID_GRIDNAME_COLORR;
  mRNAMap["NAME_COLORG"] = FLUID_GRIDNAME_COLORG;
  mRNAMap["NAME_COLORB"] = FLUID_GRIDNAME_COLORB;
  mRNAMap["NAME_FLAME"] = FLUID_GRIDNAME_FLAME;
  mRNAMap["NAME_FUEL"] = FLUID_GRIDNAME_FUEL;
  mRNAMap["NAME_REACT"] = FLUID_GRIDNAME_REACT;
  mRNAMap["NAME_DENSITYNOISE"] = FLUID_GRIDNAME_DENSITYNOISE;
  mRNAMap["NAME_COLORRNOISE"] = FLUID_GRIDNAME_COLORRNOISE;
  mRNAMap["NAME_COLORGNOISE"] = FLUID_GRIDNAME_COLORGNOISE;
  mRNAMap["NAME_COLORBNOISE"] = FLUID_GRIDNAME_COLORBNOISE;
  mRNAMap["NAME_FLAMENOISE"] = FLUID_GRIDNAME_FLAMENOISE;
  mRNAMap["NAME_FUELNOISE"] = FLUID_GRIDNAME_FUELNOISE;
  mRNAMap["NAME_REACTNOISE"] = FLUID_GRIDNAME_REACTNOISE;
}

string MANTA::getRealValue(const string &varName)
{
  if (with_debug)
    cout << "MANTA::getRealValue()" << endl;

  unordered_map<string, string>::iterator it;
  it = mRNAMap.find(varName);

  if (it == mRNAMap.end()) {
    cerr << "Fluid Error -- variable " << varName << " not found in RNA map " << it->second
         << endl;
    return "";
  }
  if (with_debug) {
    cout << "Found variable " << varName << " with value " << it->second << endl;
  }

  return it->second;
}

string MANTA::parseLine(const string &line)
{
  if (line.size() == 0)
    return "";
  string res = "";
  int currPos = 0, start_del = 0, end_del = -1;
  bool readingVar = false;
  const char delimiter = '$';
  while (currPos < line.size()) {
    if (line[currPos] == delimiter && !readingVar) {
      readingVar = true;
      start_del = currPos + 1;
      res += line.substr(end_del + 1, currPos - end_del - 1);
    }
    else if (line[currPos] == delimiter && readingVar) {
      readingVar = false;
      end_del = currPos;
      res += getRealValue(line.substr(start_del, currPos - start_del));
    }
    currPos++;
  }
  res += line.substr(end_del + 1, line.size() - end_del);
  return res;
}

string MANTA::parseScript(const string &setup_string, FluidModifierData *mmd)
{
  if (MANTA::with_debug)
    cout << "MANTA::parseScript()" << endl;

  istringstream f(setup_string);
  ostringstream res;
  string line = "";

  // Update RNA map if modifier data is handed over
  if (mmd) {
    initializeRNAMap(mmd);
  }
  while (getline(f, line)) {
    res << parseLine(line) << "\n";
  }
  return res.str();
}

bool MANTA::updateFlipStructures(FluidModifierData *mmd, int framenr)
{
  if (MANTA::with_debug)
    cout << "MANTA::updateFlipStructures()" << endl;

  FluidDomainSettings *mds = mmd->domain;
  mFlipFromFile = false;

  if (!mUsingLiquid)
    return false;
  if (BLI_path_is_rel(mds->cache_directory))
    return false;

  int result = 0;
  int expected = 0; /* Expected number of read successes for this frame. */

  /* Ensure empty data structures at start. */
  if (!mFlipParticleData || !mFlipParticleVelocity)
    return false;

  mFlipParticleData->clear();
  mFlipParticleVelocity->clear();

  string pformat = getCacheFileEnding(mds->cache_particle_format);
  string file = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_PP, pformat, framenr);

  expected += 1;
  if (BLI_exists(file.c_str())) {
    result += updateParticlesFromFile(file, false, false);
    assert(result == expected);
  }

  file = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_PVEL, pformat, framenr);
  expected += 1;
  if (BLI_exists(file.c_str())) {
    result += updateParticlesFromFile(file, false, true);
    assert(result == expected);
  }

  return mFlipFromFile = (result == expected);
}

bool MANTA::updateMeshStructures(FluidModifierData *mmd, int framenr)
{
  if (MANTA::with_debug)
    cout << "MANTA::updateMeshStructures()" << endl;

  FluidDomainSettings *mds = mmd->domain;
  mMeshFromFile = false;

  if (!mUsingMesh)
    return false;
  if (BLI_path_is_rel(mds->cache_directory))
    return false;

  int result = 0;
  int expected = 0; /* Expected number of read successes for this frame. */

  /* Ensure empty data structures at start. */
  if (!mMeshNodes || !mMeshTriangles)
    return false;

  mMeshNodes->clear();
  mMeshTriangles->clear();

  if (mMeshVelocities)
    mMeshVelocities->clear();

  string mformat = getCacheFileEnding(mds->cache_mesh_format);
  string dformat = getCacheFileEnding(mds->cache_data_format);
  string file = getFile(mmd, FLUID_DOMAIN_DIR_MESH, FLUID_FILENAME_MESH, mformat, framenr);

  expected += 1;
  if (BLI_exists(file.c_str())) {
    result += updateMeshFromFile(file);
    assert(result == expected);
  }

  if (mUsingMVel) {
    file = getFile(mmd, FLUID_DOMAIN_DIR_MESH, FLUID_FILENAME_MESHVEL, dformat, framenr);
    expected += 1;
    if (BLI_exists(file.c_str())) {
      result += updateMeshFromFile(file);
      assert(result == expected);
    }
  }

  return mMeshFromFile = (result == expected);
}

bool MANTA::updateParticleStructures(FluidModifierData *mmd, int framenr)
{
  if (MANTA::with_debug)
    cout << "MANTA::updateParticleStructures()" << endl;

  FluidDomainSettings *mds = mmd->domain;
  mParticlesFromFile = false;

  if (!mUsingDrops && !mUsingBubbles && !mUsingFloats && !mUsingTracers)
    return false;
  if (BLI_path_is_rel(mds->cache_directory))
    return false;

  int result = 0;
  int expected = 0; /* Expected number of read successes for this frame. */

  /* Ensure empty data structures at start. */
  if (!mSndParticleData || !mSndParticleVelocity || !mSndParticleLife)
    return false;

  mSndParticleData->clear();
  mSndParticleVelocity->clear();
  mSndParticleLife->clear();

  string pformat = getCacheFileEnding(mds->cache_particle_format);
  string file = getFile(mmd, FLUID_DOMAIN_DIR_PARTICLES, FLUID_FILENAME_PPSND, pformat, framenr);

  expected += 1;
  if (BLI_exists(file.c_str())) {
    result += updateParticlesFromFile(file, true, false);
    assert(result == expected);
  }

  file = getFile(mmd, FLUID_DOMAIN_DIR_PARTICLES, FLUID_FILENAME_PVELSND, pformat, framenr);
  expected += 1;
  if (BLI_exists(file.c_str())) {
    result += updateParticlesFromFile(file, true, true);
    assert(result == expected);
  }

  file = getFile(mmd, FLUID_DOMAIN_DIR_PARTICLES, FLUID_FILENAME_PLIFESND, pformat, framenr);
  expected += 1;
  if (BLI_exists(file.c_str())) {
    result += updateParticlesFromFile(file, true, false);
    assert(result == expected);
  }

  return mParticlesFromFile = (result == expected);
}

static void assertGridItems(vector<MANTA::GridItem> gList)
{
  vector<MANTA::GridItem>::iterator gIter = gList.begin();
  int *resPrev = (*gIter).res;

  for (vector<MANTA::GridItem>::iterator it = gList.begin(); it != gList.end(); ++it) {
    MANTA::GridItem item = *it;
    assert(
        ELEM(item.type, FLUID_DOMAIN_GRID_FLOAT, FLUID_DOMAIN_GRID_INT, FLUID_DOMAIN_GRID_VEC3F));
    assert(item.pointer[0]);
    if (item.type == FLUID_DOMAIN_GRID_VEC3F) {
      assert(item.pointer[1] && item.pointer[2]);
    }
    assert(item.res[0] == resPrev[0] && item.res[1] == resPrev[1] && item.res[2] == resPrev[2]);
    assert((item.name).compare("") != 0);
  }

  UNUSED_VARS(resPrev);
}

bool MANTA::updateSmokeStructures(FluidModifierData *mmd, int framenr)
{
  if (MANTA::with_debug)
    cout << "MANTA::updateGridStructures()" << endl;

  FluidDomainSettings *mds = mmd->domain;
  mSmokeFromFile = false;

  if (!mUsingSmoke)
    return false;
  if (BLI_path_is_rel(mds->cache_directory))
    return false;

  int result = 0;
  string dformat = getCacheFileEnding(mds->cache_data_format);

  vector<FileItem> filesData;
  vector<GridItem> gridsData;

  int res[] = {mResX, mResY, mResZ};

  /* Put grid pointers into pointer lists, some grids have more than 1 pointer. */
  void *aDensity[] = {mDensity};
  void *aShadow[] = {mShadow};
  void *aVelocities[] = {mVelocityX, mVelocityY, mVelocityZ};
  void *aHeat[] = {mHeat};
  void *aColorR[] = {mColorR};
  void *aColorG[] = {mColorG};
  void *aColorB[] = {mColorB};
  void *aFlame[] = {mFlame};
  void *aFuel[] = {mFuel};
  void *aReact[] = {mReact};

  /* File names for grids. */
  string fDensity = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_DENSITY, dformat, framenr);
  string fShadow = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_SHADOW, dformat, framenr);
  string fVel = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_VELOCITY, dformat, framenr);
  string fHeat = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_HEAT, dformat, framenr);
  string fColorR = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_COLORR, dformat, framenr);
  string fColorG = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_COLORG, dformat, framenr);
  string fColorB = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_COLORB, dformat, framenr);
  string fFlame = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_FLAME, dformat, framenr);
  string fFuel = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_FUEL, dformat, framenr);
  string fReact = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_REACT, dformat, framenr);
  string fFluid = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_DATA, dformat, framenr);

  /* Prepare grid info containers. */
  GridItem gDensity = {aDensity, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_DENSITY};
  GridItem gShadow = {aShadow, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_SHADOW};
  GridItem gVel = {aVelocities, FLUID_DOMAIN_GRID_VEC3F, res, FLUID_GRIDNAME_VELOCITY};
  GridItem gHeat = {aHeat, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_HEAT};
  GridItem gColorR = {aColorR, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_COLORR};
  GridItem gColorG = {aColorG, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_COLORG};
  GridItem gColorB = {aColorB, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_COLORB};
  GridItem gFlame = {aFlame, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_FLAME};
  GridItem gFuel = {aFuel, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_FUEL};
  GridItem gReact = {aReact, FLUID_DOMAIN_GRID_FLOAT, res, FLUID_GRIDNAME_REACT};

  /* TODO (sebbas): For now, only allow single file mode. Combined grid file export is todo. */
  const int fileMode = FLUID_DOMAIN_CACHE_FILES_SINGLE;
  if (fileMode == FLUID_DOMAIN_CACHE_FILES_SINGLE) {

    filesData.push_back({fDensity, {gDensity}});
    filesData.push_back({fShadow, {gShadow}});
    filesData.push_back({fVel, {gVel}});
    if (mUsingHeat) {
      filesData.push_back({fHeat, {gHeat}});
    }
    if (mUsingColors) {
      filesData.push_back({fColorR, {gColorR}});
      filesData.push_back({fColorG, {gColorG}});
      filesData.push_back({fColorB, {gColorB}});
    }
    if (mUsingFire) {
      filesData.push_back({fFlame, {gFlame}});
      filesData.push_back({fFuel, {gFuel}});
      filesData.push_back({fReact, {gReact}});
    }
  }
  else if (fileMode == FLUID_DOMAIN_CACHE_FILES_COMBINED) {

    gridsData.push_back(gDensity);
    gridsData.push_back(gShadow);
    gridsData.push_back(gVel);
    if (mUsingHeat) {
      gridsData.push_back(gHeat);
    }
    if (mUsingColors) {
      gridsData.push_back(gColorR);
      gridsData.push_back(gColorG);
      gridsData.push_back(gColorB);
    }
    if (mUsingFire) {
      gridsData.push_back(gFlame);
      gridsData.push_back(gFuel);
      gridsData.push_back(gReact);
    }

    if (with_debug) {
      assertGridItems(gridsData);
    }
    filesData.push_back({fFluid, gridsData});
  }

  /* Update files from data directory. */
  for (vector<FileItem>::iterator it = filesData.begin(); it != filesData.end(); ++it) {
    FileItem item = *it;
    if (BLI_exists(item.filename.c_str())) {
      result += updateGridsFromFile(item.filename, item.grids);
      assert(result);
    }
  }

  return mSmokeFromFile = result;
}

bool MANTA::updateNoiseStructures(FluidModifierData *mmd, int framenr)
{
  if (MANTA::with_debug)
    cout << "MANTA::updateNoiseStructures()" << endl;

  FluidDomainSettings *mds = mmd->domain;
  mNoiseFromFile = false;

  if (!mUsingSmoke || !mUsingNoise)
    return false;
  if (BLI_path_is_rel(mds->cache_directory))
    return false;

  int result = 0;
  string dformat = getCacheFileEnding(mds->cache_data_format);
  string nformat = getCacheFileEnding(mds->cache_noise_format);

  vector<FileItem> filesData, filesNoise;
  vector<GridItem> gridsData, gridsNoise;

  int resData[] = {mResX, mResY, mResZ};
  int resNoise[] = {mResXNoise, mResYNoise, mResZNoise};

  /* Put grid pointers into pointer lists, some grids have more than 1 pointer. */
  void *aShadow[] = {mShadow};
  void *aVelocities[] = {mVelocityX, mVelocityY, mVelocityZ};
  void *aDensity[] = {mDensityHigh};
  void *aColorR[] = {mColorRHigh};
  void *aColorG[] = {mColorGHigh};
  void *aColorB[] = {mColorBHigh};
  void *aFlame[] = {mFlameHigh};
  void *aFuel[] = {mFuelHigh};
  void *aReact[] = {mReactHigh};

  /* File names for grids. */
  string fShadow = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_SHADOW, dformat, framenr);
  string fVel = getFile(mmd, FLUID_DOMAIN_DIR_DATA, FLUID_FILENAME_VELOCITY, dformat, framenr);
  string fFluid = getFile(mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_DATA, dformat, framenr);

  string fDensity = getFile(
      mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_DENSITYNOISE, nformat, framenr);
  string fColorR = getFile(
      mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_COLORRNOISE, nformat, framenr);
  string fColorG = getFile(
      mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_COLORGNOISE, nformat, framenr);
  string fColorB = getFile(
      mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_COLORBNOISE, nformat, framenr);
  string fFlame = getFile(
      mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_FLAMENOISE, nformat, framenr);
  string fFuel = getFile(mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_FUELNOISE, nformat, framenr);
  string fReact = getFile(
      mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_REACTNOISE, nformat, framenr);
  string fNoise = getFile(mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_NOISE, nformat, framenr);

  /* Prepare grid info containers. */
  GridItem gShadow = {aShadow, FLUID_DOMAIN_GRID_FLOAT, resData, FLUID_GRIDNAME_SHADOW};
  GridItem gVel = {aVelocities, FLUID_DOMAIN_GRID_VEC3F, resData, FLUID_GRIDNAME_VELOCITY};

  GridItem gDensity = {aDensity, FLUID_DOMAIN_GRID_FLOAT, resNoise, FLUID_GRIDNAME_DENSITYNOISE};
  GridItem gColorR = {aColorR, FLUID_DOMAIN_GRID_FLOAT, resNoise, FLUID_GRIDNAME_COLORRNOISE};
  GridItem gColorG = {aColorG, FLUID_DOMAIN_GRID_FLOAT, resNoise, FLUID_GRIDNAME_COLORGNOISE};
  GridItem gColorB = {aColorB, FLUID_DOMAIN_GRID_FLOAT, resNoise, FLUID_GRIDNAME_COLORBNOISE};
  GridItem gFlame = {aFlame, FLUID_DOMAIN_GRID_FLOAT, resNoise, FLUID_GRIDNAME_FLAMENOISE};
  GridItem gFuel = {aFuel, FLUID_DOMAIN_GRID_FLOAT, resNoise, FLUID_GRIDNAME_FUELNOISE};
  GridItem gReact = {aReact, FLUID_DOMAIN_GRID_FLOAT, resNoise, FLUID_GRIDNAME_REACTNOISE};

  /* TODO (sebbas): For now, only allow single file mode. Combined grid file export is todo. */
  const int fileMode = FLUID_DOMAIN_CACHE_FILES_SINGLE;
  if (fileMode == FLUID_DOMAIN_CACHE_FILES_SINGLE) {

    filesData.push_back({fShadow, {gShadow}});
    filesData.push_back({fVel, {gVel}});

    filesNoise.push_back({fDensity, {gDensity}});
    if (mUsingColors) {
      filesNoise.push_back({fColorR, {gColorR}});
      filesNoise.push_back({fColorG, {gColorG}});
      filesNoise.push_back({fColorB, {gColorB}});
    }
    if (mUsingFire) {
      filesNoise.push_back({fFlame, {gFlame}});
      filesNoise.push_back({fFuel, {gFuel}});
      filesNoise.push_back({fReact, {gReact}});
    }
  }
  else if (fileMode == FLUID_DOMAIN_CACHE_FILES_COMBINED) {

    gridsData.push_back(gShadow);
    gridsData.push_back(gVel);

    gridsNoise.push_back(gDensity);
    if (mUsingColors) {
      gridsNoise.push_back(gColorR);
      gridsNoise.push_back(gColorG);
      gridsNoise.push_back(gColorB);
    }
    if (mUsingFire) {
      gridsNoise.push_back(gFlame);
      gridsNoise.push_back(gFuel);
      gridsNoise.push_back(gReact);
    }

    if (with_debug) {
      assertGridItems(gridsData);
      assertGridItems(gridsNoise);
    }
    filesData.push_back({fFluid, gridsData});
    filesNoise.push_back({fNoise, gridsNoise});
  }

  /* Update files from data directory. */
  for (vector<FileItem>::iterator it = filesData.begin(); it != filesData.end(); ++it) {
    FileItem item = *it;
    if (BLI_exists(item.filename.c_str())) {
      result += updateGridsFromFile(item.filename, item.grids);
      assert(result);
    }
  }

  /* Update files from noise directory. */
  for (vector<FileItem>::iterator it = filesNoise.begin(); it != filesNoise.end(); ++it) {
    FileItem item = *it;
    if (BLI_exists(item.filename.c_str())) {
      result += updateGridsFromFile(item.filename, item.grids);
      assert(result);
    }
  }

  return mNoiseFromFile = result;
}

/* Dirty hack: Needed to format paths from python code that is run via PyRun_SimpleString */
static string escapeSlashes(string const &s)
{
  string result = "";
  for (string::const_iterator i = s.begin(), end = s.end(); i != end; ++i) {
    unsigned char c = *i;
    if (c == '\\')
      result += "\\\\";
    else
      result += c;
  }
  return result;
}

bool MANTA::writeConfiguration(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::writeConfiguration()" << endl;

  FluidDomainSettings *mds = mmd->domain;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_CONFIG);
  string format = FLUID_DOMAIN_EXTENSION_UNI;
  string file = getFile(mmd, FLUID_DOMAIN_DIR_CONFIG, FLUID_FILENAME_CONFIG, format, framenr);

  /* Create 'config' subdir if it does not exist already. */
  BLI_dir_create_recursive(directory.c_str());

  gzFile gzf = (gzFile)BLI_gzopen(file.c_str(), "wb1");  // do some compression
  if (!gzf) {
    cerr << "Fluid Error -- Cannot open file " << file << endl;
    return false;
  }

  gzwrite(gzf, &mds->active_fields, sizeof(int));
  gzwrite(gzf, &mds->res, 3 * sizeof(int));
  gzwrite(gzf, &mds->dx, sizeof(float));
  gzwrite(gzf, &mds->dt, sizeof(float));
  gzwrite(gzf, &mds->p0, 3 * sizeof(float));
  gzwrite(gzf, &mds->p1, 3 * sizeof(float));
  gzwrite(gzf, &mds->dp0, 3 * sizeof(float));
  gzwrite(gzf, &mds->shift, 3 * sizeof(int));
  gzwrite(gzf, &mds->obj_shift_f, 3 * sizeof(float));
  gzwrite(gzf, &mds->obmat, 16 * sizeof(float));
  gzwrite(gzf, &mds->base_res, 3 * sizeof(int));
  gzwrite(gzf, &mds->res_min, 3 * sizeof(int));
  gzwrite(gzf, &mds->res_max, 3 * sizeof(int));
  gzwrite(gzf, &mds->active_color, 3 * sizeof(float));
  gzwrite(gzf, &mds->time_total, sizeof(int));

  return (gzclose(gzf) == Z_OK);
}

bool MANTA::writeData(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::writeData()" << endl;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_DATA);
  string dformat = getCacheFileEnding(mds->cache_data_format);
  string pformat = getCacheFileEnding(mds->cache_particle_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  ss.str("");
  ss << "fluid_save_data_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
     << ", '" << dformat << "', " << resumable_cache << ")";
  pythonCommands.push_back(ss.str());

  if (mUsingSmoke) {
    ss.str("");
    ss << "smoke_save_data_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
       << ", '" << dformat << "', " << resumable_cache << ")";
    pythonCommands.push_back(ss.str());
  }
  if (mUsingLiquid) {
    ss.str("");
    ss << "liquid_save_data_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
       << ", '" << dformat << "', " << resumable_cache << ")";
    pythonCommands.push_back(ss.str());
  }
  return runPythonString(pythonCommands);
}

bool MANTA::writeNoise(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::writeNoise()" << endl;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_NOISE);
  string nformat = getCacheFileEnding(mds->cache_noise_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  if (mUsingSmoke && mUsingNoise) {
    ss.str("");
    ss << "smoke_save_noise_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
       << ", '" << nformat << "', " << resumable_cache << ")";
    pythonCommands.push_back(ss.str());
  }
  return runPythonString(pythonCommands);
}

bool MANTA::readConfiguration(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::readConfiguration()" << endl;

  FluidDomainSettings *mds = mmd->domain;
  float dummy;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_CONFIG);
  string format = FLUID_DOMAIN_EXTENSION_UNI;
  string file = getFile(mmd, FLUID_DOMAIN_DIR_CONFIG, FLUID_FILENAME_CONFIG, format, framenr);

  if (!hasConfig(mmd, framenr))
    return false;

  gzFile gzf = (gzFile)BLI_gzopen(file.c_str(), "rb");  // do some compression
  if (!gzf) {
    cerr << "Fluid Error -- Cannot open file " << file << endl;
    return false;
  }

  gzread(gzf, &mds->active_fields, sizeof(int));
  gzread(gzf, &mds->res, 3 * sizeof(int));
  gzread(gzf, &mds->dx, sizeof(float));
  gzread(gzf, &dummy, sizeof(float));  // dt not needed right now
  gzread(gzf, &mds->p0, 3 * sizeof(float));
  gzread(gzf, &mds->p1, 3 * sizeof(float));
  gzread(gzf, &mds->dp0, 3 * sizeof(float));
  gzread(gzf, &mds->shift, 3 * sizeof(int));
  gzread(gzf, &mds->obj_shift_f, 3 * sizeof(float));
  gzread(gzf, &mds->obmat, 16 * sizeof(float));
  gzread(gzf, &mds->base_res, 3 * sizeof(int));
  gzread(gzf, &mds->res_min, 3 * sizeof(int));
  gzread(gzf, &mds->res_max, 3 * sizeof(int));
  gzread(gzf, &mds->active_color, 3 * sizeof(float));
  gzread(gzf, &mds->time_total, sizeof(int));

  mds->total_cells = mds->res[0] * mds->res[1] * mds->res[2];

  return (gzclose(gzf) == Z_OK);
}

bool MANTA::readData(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::readData()" << endl;

  if (!mUsingSmoke && !mUsingLiquid)
    return false;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;
  bool result = true;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_DATA);
  string dformat = getCacheFileEnding(mds->cache_data_format);
  string pformat = getCacheFileEnding(mds->cache_particle_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  /* Sanity check: Are cache files present? */
  if (!hasData(mmd, framenr))
    return false;

  ss.str("");
  ss << "fluid_load_data_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
     << ", '" << dformat << "', " << resumable_cache << ")";
  pythonCommands.push_back(ss.str());

  if (mUsingSmoke) {
    ss.str("");
    ss << "smoke_load_data_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
       << ", '" << dformat << "', " << resumable_cache << ")";
    pythonCommands.push_back(ss.str());
    result &= runPythonString(pythonCommands);
  }
  if (mUsingLiquid) {
    ss.str("");
    ss << "liquid_load_data_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
       << ", '" << dformat << "', " << resumable_cache << ")";
    pythonCommands.push_back(ss.str());
    result &= runPythonString(pythonCommands);
  }
  return result;
}

bool MANTA::readNoise(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::readNoise()" << endl;

  if (!mUsingSmoke || !mUsingNoise)
    return false;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_NOISE);
  string nformat = getCacheFileEnding(mds->cache_noise_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  /* Sanity check: Are cache files present? */
  if (!hasNoise(mmd, framenr))
    return false;

  ss.str("");
  ss << "smoke_load_noise_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
     << ", '" << nformat << "', " << resumable_cache << ")";
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

/* Deprecated! This function reads mesh data via the Manta Python API.
 * MANTA:updateMeshStructures() reads cache files directly from disk
 * and is preferred due to its better performance. */
bool MANTA::readMesh(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::readMesh()" << endl;

  if (!mUsingLiquid || !mUsingMesh)
    return false;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_MESH);
  string mformat = getCacheFileEnding(mds->cache_mesh_format);
  string dformat = getCacheFileEnding(mds->cache_data_format);

  /* Sanity check: Are cache files present? */
  if (!hasMesh(mmd, framenr))
    return false;

  ss.str("");
  ss << "liquid_load_mesh_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
     << ", '" << mformat << "')";
  pythonCommands.push_back(ss.str());

  if (mUsingMVel) {
    ss.str("");
    ss << "liquid_load_meshvel_" << mCurrentID << "('" << escapeSlashes(directory) << "', "
       << framenr << ", '" << dformat << "')";
    pythonCommands.push_back(ss.str());
  }

  return runPythonString(pythonCommands);
}

/* Deprecated! This function reads particle data via the Manta Python API.
 * MANTA:updateParticleStructures() reads cache files directly from disk
 * and is preferred due to its better performance. */
bool MANTA::readParticles(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::readParticles()" << endl;

  if (!mUsingLiquid)
    return false;
  if (!mUsingDrops && !mUsingBubbles && !mUsingFloats && !mUsingTracers)
    return false;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  string directory = getDirectory(mmd, FLUID_DOMAIN_DIR_PARTICLES);
  string pformat = getCacheFileEnding(mds->cache_particle_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  /* Sanity check: Are cache files present? */
  if (!hasParticles(mmd, framenr))
    return false;

  ss.str("");
  ss << "liquid_load_particles_" << mCurrentID << "('" << escapeSlashes(directory) << "', "
     << framenr << ", '" << pformat << "', " << resumable_cache << ")";
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

bool MANTA::readGuiding(FluidModifierData *mmd, int framenr, bool sourceDomain)
{
  if (with_debug)
    cout << "MANTA::readGuiding()" << endl;

  FluidDomainSettings *mds = mmd->domain;

  if (!mUsingGuiding)
    return false;
  if (!mds)
    return false;

  ostringstream ss;
  vector<string> pythonCommands;

  string directory = (sourceDomain) ? getDirectory(mmd, FLUID_DOMAIN_DIR_DATA) :
                                      getDirectory(mmd, FLUID_DOMAIN_DIR_GUIDE);
  string gformat = getCacheFileEnding(mds->cache_data_format);

  /* Sanity check: Are cache files present? */
  if (!hasGuiding(mmd, framenr, sourceDomain))
    return false;

  if (sourceDomain) {
    ss.str("");
    ss << "fluid_load_vel_" << mCurrentID << "('" << escapeSlashes(directory) << "', " << framenr
       << ", '" << gformat << "')";
  }
  else {
    ss.str("");
    ss << "fluid_load_guiding_" << mCurrentID << "('" << escapeSlashes(directory) << "', "
       << framenr << ", '" << gformat << "')";
  }
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

bool MANTA::bakeData(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::bakeData()" << endl;

  string tmpString, finalString;
  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  char cacheDirData[FILE_MAX], cacheDirGuiding[FILE_MAX];
  cacheDirData[0] = '\0';
  cacheDirGuiding[0] = '\0';

  string dformat = getCacheFileEnding(mds->cache_data_format);
  string pformat = getCacheFileEnding(mds->cache_particle_format);
  string gformat = dformat;  // Use same data format for guiding format

  BLI_path_join(
      cacheDirData, sizeof(cacheDirData), mds->cache_directory, FLUID_DOMAIN_DIR_DATA, nullptr);
  BLI_path_join(cacheDirGuiding,
                sizeof(cacheDirGuiding),
                mds->cache_directory,
                FLUID_DOMAIN_DIR_GUIDE,
                nullptr);
  BLI_path_make_safe(cacheDirData);
  BLI_path_make_safe(cacheDirGuiding);

  ss.str("");
  ss << "bake_fluid_data_" << mCurrentID << "('" << escapeSlashes(cacheDirData) << "', '"
     << escapeSlashes(cacheDirGuiding) << "', " << framenr << ", '" << dformat << "', '" << pformat
     << "', '" << gformat << "')";
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

bool MANTA::bakeNoise(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::bakeNoise()" << endl;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  char cacheDirData[FILE_MAX], cacheDirNoise[FILE_MAX];
  cacheDirData[0] = '\0';
  cacheDirNoise[0] = '\0';

  string dformat = getCacheFileEnding(mds->cache_data_format);
  string nformat = getCacheFileEnding(mds->cache_noise_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  BLI_path_join(
      cacheDirData, sizeof(cacheDirData), mds->cache_directory, FLUID_DOMAIN_DIR_DATA, nullptr);
  BLI_path_join(
      cacheDirNoise, sizeof(cacheDirNoise), mds->cache_directory, FLUID_DOMAIN_DIR_NOISE, nullptr);
  BLI_path_make_safe(cacheDirData);
  BLI_path_make_safe(cacheDirNoise);

  ss.str("");
  ss << "bake_noise_" << mCurrentID << "('" << escapeSlashes(cacheDirData) << "', '"
     << escapeSlashes(cacheDirNoise) << "', " << framenr << ", '" << dformat << "', '" << nformat
     << "', " << resumable_cache << ")";
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

bool MANTA::bakeMesh(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::bakeMesh()" << endl;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  char cacheDirData[FILE_MAX], cacheDirMesh[FILE_MAX];
  cacheDirData[0] = '\0';
  cacheDirMesh[0] = '\0';

  string dformat = getCacheFileEnding(mds->cache_data_format);
  string mformat = getCacheFileEnding(mds->cache_mesh_format);
  string pformat = getCacheFileEnding(mds->cache_particle_format);

  BLI_path_join(
      cacheDirData, sizeof(cacheDirData), mds->cache_directory, FLUID_DOMAIN_DIR_DATA, nullptr);
  BLI_path_join(
      cacheDirMesh, sizeof(cacheDirMesh), mds->cache_directory, FLUID_DOMAIN_DIR_MESH, nullptr);
  BLI_path_make_safe(cacheDirData);
  BLI_path_make_safe(cacheDirMesh);

  ss.str("");
  ss << "bake_mesh_" << mCurrentID << "('" << escapeSlashes(cacheDirData) << "', '"
     << escapeSlashes(cacheDirMesh) << "', " << framenr << ", '" << dformat << "', '" << mformat
     << "', '" << pformat << "')";
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

bool MANTA::bakeParticles(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::bakeParticles()" << endl;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  char cacheDirData[FILE_MAX], cacheDirParticles[FILE_MAX];
  cacheDirData[0] = '\0';
  cacheDirParticles[0] = '\0';

  string dformat = getCacheFileEnding(mds->cache_data_format);
  string pformat = getCacheFileEnding(mds->cache_particle_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  BLI_path_join(
      cacheDirData, sizeof(cacheDirData), mds->cache_directory, FLUID_DOMAIN_DIR_DATA, nullptr);
  BLI_path_join(cacheDirParticles,
                sizeof(cacheDirParticles),
                mds->cache_directory,
                FLUID_DOMAIN_DIR_PARTICLES,
                nullptr);
  BLI_path_make_safe(cacheDirData);
  BLI_path_make_safe(cacheDirParticles);

  ss.str("");
  ss << "bake_particles_" << mCurrentID << "('" << escapeSlashes(cacheDirData) << "', '"
     << escapeSlashes(cacheDirParticles) << "', " << framenr << ", '" << dformat << "', '"
     << pformat << "', " << resumable_cache << ")";
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

bool MANTA::bakeGuiding(FluidModifierData *mmd, int framenr)
{
  if (with_debug)
    cout << "MANTA::bakeGuiding()" << endl;

  ostringstream ss;
  vector<string> pythonCommands;
  FluidDomainSettings *mds = mmd->domain;

  char cacheDirGuiding[FILE_MAX];
  cacheDirGuiding[0] = '\0';

  string gformat = getCacheFileEnding(mds->cache_data_format);

  bool final_cache = (mds->cache_type == FLUID_DOMAIN_CACHE_FINAL);
  string resumable_cache = (final_cache) ? "False" : "True";

  BLI_path_join(cacheDirGuiding,
                sizeof(cacheDirGuiding),
                mds->cache_directory,
                FLUID_DOMAIN_DIR_GUIDE,
                nullptr);
  BLI_path_make_safe(cacheDirGuiding);

  ss.str("");
  ss << "bake_guiding_" << mCurrentID << "('" << escapeSlashes(cacheDirGuiding) << "', " << framenr
     << ", '" << gformat << "', " << resumable_cache << ")";
  pythonCommands.push_back(ss.str());

  return runPythonString(pythonCommands);
}

bool MANTA::updateVariables(FluidModifierData *mmd)
{
  string tmpString, finalString;
  vector<string> pythonCommands;

  tmpString += fluid_variables;
  if (mUsingSmoke)
    tmpString += smoke_variables;
  if (mUsingLiquid)
    tmpString += liquid_variables;
  if (mUsingGuiding)
    tmpString += fluid_variables_guiding;
  if (mUsingNoise) {
    tmpString += fluid_variables_noise;
    tmpString += smoke_variables_noise;
    tmpString += smoke_wavelet_noise;
  }
  if (mUsingDrops || mUsingBubbles || mUsingFloats || mUsingTracers) {
    tmpString += fluid_variables_particles;
    tmpString += liquid_variables_particles;
  }
  if (mUsingMesh)
    tmpString += fluid_variables_mesh;

  finalString = parseScript(tmpString, mmd);
  pythonCommands.push_back(finalString);

  return runPythonString(pythonCommands);
}

void MANTA::exportSmokeScript(FluidModifierData *mmd)
{
  if (with_debug)
    cout << "MANTA::exportSmokeScript()" << endl;

  char cacheDir[FILE_MAX] = "\0";
  char cacheDirScript[FILE_MAX] = "\0";

  FluidDomainSettings *mds = mmd->domain;

  BLI_path_join(
      cacheDir, sizeof(cacheDir), mds->cache_directory, FLUID_DOMAIN_DIR_SCRIPT, nullptr);
  BLI_path_make_safe(cacheDir);
  /* Create 'script' subdir if it does not exist already */
  BLI_dir_create_recursive(cacheDir);
  BLI_path_join(
      cacheDirScript, sizeof(cacheDirScript), cacheDir, FLUID_DOMAIN_SMOKE_SCRIPT, nullptr);
  BLI_path_make_safe(cacheDir);

  bool noise = mds->flags & FLUID_DOMAIN_USE_NOISE;
  bool heat = mds->active_fields & FLUID_DOMAIN_ACTIVE_HEAT;
  bool colors = mds->active_fields & FLUID_DOMAIN_ACTIVE_COLORS;
  bool fire = mds->active_fields & FLUID_DOMAIN_ACTIVE_FIRE;
  bool obstacle = mds->active_fields & FLUID_DOMAIN_ACTIVE_OBSTACLE;
  bool guiding = mds->active_fields & FLUID_DOMAIN_ACTIVE_GUIDE;
  bool invel = mds->active_fields & FLUID_DOMAIN_ACTIVE_INVEL;
  bool outflow = mds->active_fields & FLUID_DOMAIN_ACTIVE_OUTFLOW;

  string manta_script;

  // Libraries
  manta_script += header_libraries + manta_import;

  // Variables
  manta_script += header_variables + fluid_variables + smoke_variables;
  if (noise) {
    manta_script += fluid_variables_noise + smoke_variables_noise;
  }
  if (guiding)
    manta_script += fluid_variables_guiding;

  // Solvers
  manta_script += header_solvers + fluid_solver;
  if (noise)
    manta_script += fluid_solver_noise;
  if (guiding)
    manta_script += fluid_solver_guiding;

  // Grids
  manta_script += header_grids + fluid_alloc + smoke_alloc;
  if (noise) {
    manta_script += smoke_alloc_noise;
    if (colors)
      manta_script += smoke_alloc_colors_noise;
    if (fire)
      manta_script += smoke_alloc_fire_noise;
  }
  if (heat)
    manta_script += smoke_alloc_heat;
  if (colors)
    manta_script += smoke_alloc_colors;
  if (fire)
    manta_script += smoke_alloc_fire;
  if (guiding)
    manta_script += fluid_alloc_guiding;
  if (obstacle)
    manta_script += fluid_alloc_obstacle;
  if (invel)
    manta_script += fluid_alloc_invel;
  if (outflow)
    manta_script += fluid_alloc_outflow;

  // Noise field
  if (noise)
    manta_script += smoke_wavelet_noise;

  // Time
  manta_script += header_time + fluid_time_stepping + fluid_adapt_time_step;

  // Import
  manta_script += header_import + fluid_file_import + fluid_cache_helper + fluid_load_data +
                  smoke_load_data;
  if (noise)
    manta_script += smoke_load_noise;
  if (guiding)
    manta_script += fluid_load_guiding;

  // Pre/Post Steps
  manta_script += header_prepost + fluid_pre_step + fluid_post_step;

  // Steps
  manta_script += header_steps + smoke_adaptive_step + smoke_step;
  if (noise) {
    manta_script += smoke_step_noise;
  }

  // Main
  manta_script += header_main + smoke_standalone + fluid_standalone;

  // Fill in missing variables in script
  string final_script = MANTA::parseScript(manta_script, mmd);

  // Write script
  ofstream myfile;
  myfile.open(cacheDirScript);
  myfile << final_script;
  myfile.close();
}

void MANTA::exportLiquidScript(FluidModifierData *mmd)
{
  if (with_debug)
    cout << "MANTA::exportLiquidScript()" << endl;

  char cacheDir[FILE_MAX] = "\0";
  char cacheDirScript[FILE_MAX] = "\0";

  FluidDomainSettings *mds = mmd->domain;

  BLI_path_join(
      cacheDir, sizeof(cacheDir), mds->cache_directory, FLUID_DOMAIN_DIR_SCRIPT, nullptr);
  BLI_path_make_safe(cacheDir);
  /* Create 'script' subdir if it does not exist already */
  BLI_dir_create_recursive(cacheDir);
  BLI_path_join(
      cacheDirScript, sizeof(cacheDirScript), cacheDir, FLUID_DOMAIN_LIQUID_SCRIPT, nullptr);
  BLI_path_make_safe(cacheDirScript);

  bool mesh = mds->flags & FLUID_DOMAIN_USE_MESH;
  bool drops = mds->particle_type & FLUID_DOMAIN_PARTICLE_SPRAY;
  bool bubble = mds->particle_type & FLUID_DOMAIN_PARTICLE_BUBBLE;
  bool floater = mds->particle_type & FLUID_DOMAIN_PARTICLE_FOAM;
  bool tracer = mds->particle_type & FLUID_DOMAIN_PARTICLE_TRACER;
  bool obstacle = mds->active_fields & FLUID_DOMAIN_ACTIVE_OBSTACLE;
  bool fractions = mds->flags & FLUID_DOMAIN_USE_FRACTIONS;
  bool guiding = mds->active_fields & FLUID_DOMAIN_ACTIVE_GUIDE;
  bool invel = mds->active_fields & FLUID_DOMAIN_ACTIVE_INVEL;
  bool outflow = mds->active_fields & FLUID_DOMAIN_ACTIVE_OUTFLOW;

  string manta_script;

  // Libraries
  manta_script += header_libraries + manta_import;

  // Variables
  manta_script += header_variables + fluid_variables + liquid_variables;
  if (mesh)
    manta_script += fluid_variables_mesh;
  if (drops || bubble || floater || tracer)
    manta_script += fluid_variables_particles + liquid_variables_particles;
  if (guiding)
    manta_script += fluid_variables_guiding;

  // Solvers
  manta_script += header_solvers + fluid_solver;
  if (mesh)
    manta_script += fluid_solver_mesh;
  if (drops || bubble || floater || tracer)
    manta_script += fluid_solver_particles;
  if (guiding)
    manta_script += fluid_solver_guiding;

  // Grids
  manta_script += header_grids + fluid_alloc + liquid_alloc;
  if (mesh)
    manta_script += liquid_alloc_mesh;
  if (drops || bubble || floater || tracer)
    manta_script += liquid_alloc_particles;
  if (guiding)
    manta_script += fluid_alloc_guiding;
  if (obstacle)
    manta_script += fluid_alloc_obstacle;
  if (fractions)
    manta_script += fluid_alloc_fractions;
  if (invel)
    manta_script += fluid_alloc_invel;
  if (outflow)
    manta_script += fluid_alloc_outflow;

  // Domain init
  manta_script += header_gridinit + liquid_init_phi;

  // Time
  manta_script += header_time + fluid_time_stepping + fluid_adapt_time_step;

  // Import
  manta_script += header_import + fluid_file_import + fluid_cache_helper + fluid_load_data +
                  liquid_load_data;
  if (mesh)
    manta_script += liquid_load_mesh;
  if (drops || bubble || floater || tracer)
    manta_script += liquid_load_particles;
  if (guiding)
    manta_script += fluid_load_guiding;

  // Pre/Post Steps
  manta_script += header_prepost + fluid_pre_step + fluid_post_step;

  // Steps
  manta_script += header_steps + liquid_adaptive_step + liquid_step;
  if (mesh)
    manta_script += liquid_step_mesh;
  if (drops || bubble || floater || tracer)
    manta_script += liquid_step_particles;

  // Main
  manta_script += header_main + liquid_standalone + fluid_standalone;

  // Fill in missing variables in script
  string final_script = MANTA::parseScript(manta_script, mmd);

  // Write script
  ofstream myfile;
  myfile.open(cacheDirScript);
  myfile << final_script;
  myfile.close();
}

/* Call Mantaflow Python functions through this function. Use isAttribute for object attributes,
 * e.g. s.cfl (here 's' is varname, 'cfl' functionName, and isAttribute true) or
 *      grid.getDataPointer (here 's' is varname, 'getDataPointer' functionName, and isAttribute
 * false)
 *
 * Important! Return value: New reference or nullptr
 * Caller of this function needs to handle reference count of returned object. */
static PyObject *callPythonFunction(string varName, string functionName, bool isAttribute = false)
{
  if ((varName == "") || (functionName == "")) {
    if (MANTA::with_debug)
      cout << "Missing Python variable name and/or function name -- name is: " << varName
           << ", function name is: " << functionName << endl;
    return nullptr;
  }

  PyGILState_STATE gilstate = PyGILState_Ensure();
  PyObject *var = nullptr, *func = nullptr, *returnedValue = nullptr;

  /* Be sure to initialize Python before using it. */
  Py_Initialize();

  // Get pyobject that holds result value
  if (!manta_main_module) {
    PyGILState_Release(gilstate);
    return nullptr;
  }

  var = PyObject_GetAttrString(manta_main_module, varName.c_str());
  if (!var) {
    PyGILState_Release(gilstate);
    return nullptr;
  }

  func = PyObject_GetAttrString(var, functionName.c_str());

  Py_DECREF(var);
  if (!func) {
    PyGILState_Release(gilstate);
    return nullptr;
  }

  if (!isAttribute) {
    returnedValue = PyObject_CallObject(func, nullptr);
    Py_DECREF(func);
  }

  PyGILState_Release(gilstate);
  return (!isAttribute) ? returnedValue : func;
}

/* Argument of this function may be a nullptr.
 * If it's not function will handle the reference count decrement of that argument. */
static void *pyObjectToPointer(PyObject *inputObject)
{
  if (!inputObject)
    return nullptr;

  PyGILState_STATE gilstate = PyGILState_Ensure();

  PyObject *encoded = PyUnicode_AsUTF8String(inputObject);
  char *result = PyBytes_AsString(encoded);

  Py_DECREF(inputObject);

  string str(result);
  istringstream in(str);
  void *dataPointer = nullptr;
  in >> dataPointer;

  Py_DECREF(encoded);

  PyGILState_Release(gilstate);
  return dataPointer;
}

/* Argument of this function may be a nullptr.
 * If it's not function will handle the reference count decrement of that argument. */
static double pyObjectToDouble(PyObject *inputObject)
{
  if (!inputObject)
    return 0.0;

  PyGILState_STATE gilstate = PyGILState_Ensure();

  /* Cannot use PyFloat_AsDouble() since its error check crashes.
   * Likely because of typedef 'Real' for 'float' types in Mantaflow. */
  double result = PyFloat_AS_DOUBLE(inputObject);
  Py_DECREF(inputObject);

  PyGILState_Release(gilstate);
  return result;
}

/* Argument of this function may be a nullptr.
 * If it's not function will handle the reference count decrement of that argument. */
static long pyObjectToLong(PyObject *inputObject)
{
  if (!inputObject)
    return 0;

  PyGILState_STATE gilstate = PyGILState_Ensure();

  long result = PyLong_AsLong(inputObject);
  Py_DECREF(inputObject);

  PyGILState_Release(gilstate);
  return result;
}

int MANTA::getFrame()
{
  if (with_debug)
    cout << "MANTA::getFrame()" << endl;

  string func = "frame";
  string id = to_string(mCurrentID);
  string solver = "s" + id;

  return pyObjectToLong(callPythonFunction(solver, func, true));
}

float MANTA::getTimestep()
{
  if (with_debug)
    cout << "MANTA::getTimestep()" << endl;

  string func = "timestep";
  string id = to_string(mCurrentID);
  string solver = "s" + id;

  return (float)pyObjectToDouble(callPythonFunction(solver, func, true));
}

bool MANTA::needsRealloc(FluidModifierData *mmd)
{
  FluidDomainSettings *mds = mmd->domain;
  return (mds->res[0] != mResX || mds->res[1] != mResY || mds->res[2] != mResZ);
}

void MANTA::adaptTimestep()
{
  if (with_debug)
    cout << "MANTA::adaptTimestep()" << endl;

  vector<string> pythonCommands;
  ostringstream ss;

  ss << "fluid_adapt_time_step_" << mCurrentID << "()";
  pythonCommands.push_back(ss.str());

  runPythonString(pythonCommands);
}

bool MANTA::updateMeshFromFile(string filename)
{
  string fname(filename);
  string::size_type idx;

  idx = fname.rfind('.');
  if (idx != string::npos) {
    string extension = fname.substr(idx + 1);

    if (extension.compare("gz") == 0)
      return updateMeshFromBobj(filename);
    else if (extension.compare("obj") == 0)
      return updateMeshFromObj(filename);
    else if (extension.compare("uni") == 0)
      return updateMeshFromUni(filename);
    else
      cerr << "Fluid Error -- updateMeshFromFile(): Invalid file extension in file: " << filename
           << endl;
  }
  else {
    cerr << "Fluid Error -- updateMeshFromFile(): Unable to open file: " << filename << endl;
  }
  return false;
}

bool MANTA::updateMeshFromBobj(string filename)
{
  if (with_debug)
    cout << "MANTA::updateMeshFromBobj()" << endl;

  gzFile gzf;

  gzf = (gzFile)BLI_gzopen(filename.c_str(), "rb1");  // do some compression
  if (!gzf) {
    cerr << "Fluid Error -- updateMeshFromBobj(): Unable to open file: " << filename << endl;
    return false;
  }

  int numBuffer = 0, readBytes = 0;

  // Num vertices
  readBytes = gzread(gzf, &numBuffer, sizeof(int));
  if (!readBytes) {
    cerr << "Fluid Error -- updateMeshFromBobj(): Unable to read number of mesh vertices from "
         << filename << endl;
    gzclose(gzf);
    return false;
  }

  if (with_debug)
    cout << "read mesh , num verts: " << numBuffer << " , in file: " << filename << endl;

  int numChunks = (int)(ceil((float)numBuffer / NODE_CHUNK));
  int readLen, readStart, readEnd, k;

  if (numBuffer) {
    // Vertices
    int todoVertices = numBuffer;
    float *bufferVerts = (float *)MEM_malloc_arrayN(
        NODE_CHUNK, sizeof(float) * 3, "fluid_mesh_vertices");

    mMeshNodes->resize(numBuffer);

    for (int i = 0; i < numChunks && todoVertices > 0; ++i) {
      readLen = NODE_CHUNK;
      if (todoVertices < NODE_CHUNK) {
        readLen = todoVertices;
      }

      readBytes = gzread(gzf, bufferVerts, readLen * sizeof(float) * 3);
      if (!readBytes) {
        cerr << "Fluid Error -- updateMeshFromBobj(): Unable to read mesh vertices from "
             << filename << endl;
        MEM_freeN(bufferVerts);
        gzclose(gzf);
        return false;
      }

      readStart = (numBuffer - todoVertices);
      CLAMP(readStart, 0, numBuffer);
      readEnd = readStart + readLen;
      CLAMP(readEnd, 0, numBuffer);

      k = 0;
      for (vector<MANTA::Node>::size_type j = readStart; j < readEnd; j++, k += 3) {
        mMeshNodes->at(j).pos[0] = bufferVerts[k];
        mMeshNodes->at(j).pos[1] = bufferVerts[k + 1];
        mMeshNodes->at(j).pos[2] = bufferVerts[k + 2];
      }
      todoVertices -= readLen;
    }
    MEM_freeN(bufferVerts);
  }

  // Num normals
  readBytes = gzread(gzf, &numBuffer, sizeof(int));
  if (!readBytes) {
    cerr << "Fluid Error -- updateMeshFromBobj(): Unable to read number of mesh normals from "
         << filename << endl;
    gzclose(gzf);
    return false;
  }

  if (with_debug)
    cout << "read mesh , num normals : " << numBuffer << " , in file: " << filename << endl;

  if (numBuffer) {
    // Normals
    int todoNormals = numBuffer;
    float *bufferNormals = (float *)MEM_malloc_arrayN(
        NODE_CHUNK, sizeof(float) * 3, "fluid_mesh_normals");

    if (!getNumVertices())
      mMeshNodes->resize(numBuffer);

    for (int i = 0; i < numChunks && todoNormals > 0; ++i) {
      readLen = NODE_CHUNK;
      if (todoNormals < NODE_CHUNK) {
        readLen = todoNormals;
      }

      readBytes = gzread(gzf, bufferNormals, readLen * sizeof(float) * 3);
      if (!readBytes) {
        cerr << "Fluid Error -- updateMeshFromBobj(): Unable to read mesh normals from "
             << filename << endl;
        MEM_freeN(bufferNormals);
        gzclose(gzf);
        return false;
      }

      readStart = (numBuffer - todoNormals);
      CLAMP(readStart, 0, numBuffer);
      readEnd = readStart + readLen;
      CLAMP(readEnd, 0, numBuffer);

      k = 0;
      for (vector<MANTA::Node>::size_type j = readStart; j < readEnd; j++, k += 3) {
        mMeshNodes->at(j).normal[0] = bufferNormals[k];
        mMeshNodes->at(j).normal[1] = bufferNormals[k + 1];
        mMeshNodes->at(j).normal[2] = bufferNormals[k + 2];
      }
      todoNormals -= readLen;
    }
    MEM_freeN(bufferNormals);
  }

  // Num triangles
  readBytes = gzread(gzf, &numBuffer, sizeof(int));
  if (!readBytes) {
    cerr << "Fluid Error -- updateMeshFromBobj(): Unable to read number of mesh triangles from "
         << filename << endl;
    gzclose(gzf);
    return false;
  }

  if (with_debug)
    cout << "Fluid: Read mesh , num triangles : " << numBuffer << " , in file: " << filename
         << endl;

  numChunks = (int)(ceil((float)numBuffer / TRIANGLE_CHUNK));

  if (numBuffer) {
    // Triangles
    int todoTriangles = numBuffer;
    int *bufferTriangles = (int *)MEM_malloc_arrayN(
        TRIANGLE_CHUNK, sizeof(int) * 3, "fluid_mesh_triangles");

    mMeshTriangles->resize(numBuffer);

    for (int i = 0; i < numChunks && todoTriangles > 0; ++i) {
      readLen = TRIANGLE_CHUNK;
      if (todoTriangles < TRIANGLE_CHUNK) {
        readLen = todoTriangles;
      }

      readBytes = gzread(gzf, bufferTriangles, readLen * sizeof(int) * 3);
      if (!readBytes) {
        cerr << "Fluid Error -- updateMeshFromBobj(): Unable to read mesh triangles from "
             << filename << endl;
        MEM_freeN(bufferTriangles);
        gzclose(gzf);
        return false;
      }

      readStart = (numBuffer - todoTriangles);
      CLAMP(readStart, 0, numBuffer);
      readEnd = readStart + readLen;
      CLAMP(readEnd, 0, numBuffer);

      k = 0;
      for (vector<MANTA::Triangle>::size_type j = readStart; j < readEnd; j++, k += 3) {
        mMeshTriangles->at(j).c[0] = bufferTriangles[k];
        mMeshTriangles->at(j).c[1] = bufferTriangles[k + 1];
        mMeshTriangles->at(j).c[2] = bufferTriangles[k + 2];
      }
      todoTriangles -= readLen;
    }
    MEM_freeN(bufferTriangles);
  }
  return (gzclose(gzf) == Z_OK);
}

bool MANTA::updateMeshFromObj(string filename)
{
  if (with_debug)
    cout << "MANTA::updateMeshFromObj()" << endl;

  ifstream ifs(filename);
  float fbuffer[3];
  int ibuffer[3];
  int cntVerts = 0, cntNormals = 0, cntTris = 0;

  if (!ifs.good()) {
    cerr << "Fluid Error -- updateMeshFromObj(): Unable to open file: " << filename << endl;
    return false;
  }

  while (ifs.good() && !ifs.eof()) {
    string id;
    ifs >> id;

    if (id[0] == '#') {
      // comment
      getline(ifs, id);
      continue;
    }
    if (id == "vt") {
      // tex coord, ignore
    }
    else if (id == "vn") {
      // normals
      if (getNumVertices() != cntVerts) {
        cerr << "Fluid Error -- updateMeshFromObj(): Invalid number of mesh nodes in file: "
             << filename << endl;
        return false;
      }

      ifs >> fbuffer[0] >> fbuffer[1] >> fbuffer[2];
      MANTA::Node *node = &mMeshNodes->at(cntNormals);
      (*node).normal[0] = fbuffer[0];
      (*node).normal[1] = fbuffer[1];
      (*node).normal[2] = fbuffer[2];
      cntNormals++;
    }
    else if (id == "v") {
      // vertex
      ifs >> fbuffer[0] >> fbuffer[1] >> fbuffer[2];
      MANTA::Node node;
      node.pos[0] = fbuffer[0];
      node.pos[1] = fbuffer[1];
      node.pos[2] = fbuffer[2];
      mMeshNodes->push_back(node);
      cntVerts++;
    }
    else if (id == "g") {
      // group
      string group;
      ifs >> group;
    }
    else if (id == "f") {
      // face
      string face;
      for (int i = 0; i < 3; i++) {
        ifs >> face;
        if (face.find('/') != string::npos)
          face = face.substr(0, face.find('/'));  // ignore other indices
        int idx = atoi(face.c_str()) - 1;
        if (idx < 0) {
          cerr << "Fluid Error -- updateMeshFromObj(): Invalid face encountered in file: "
               << filename << endl;
          return false;
        }
        ibuffer[i] = idx;
      }
      MANTA::Triangle triangle;
      triangle.c[0] = ibuffer[0];
      triangle.c[1] = ibuffer[1];
      triangle.c[2] = ibuffer[2];
      mMeshTriangles->push_back(triangle);
      cntTris++;
    }
    else {
      // whatever, ignore
    }
    // kill rest of line
    getline(ifs, id);
  }
  ifs.close();
  return true;
}

bool MANTA::updateMeshFromUni(string filename)
{
  if (with_debug)
    cout << "MANTA::updateMeshFromUni()" << endl;

  gzFile gzf;
  float fbuffer[4];
  int ibuffer[4];

  gzf = (gzFile)BLI_gzopen(filename.c_str(), "rb1");  // do some compression
  if (!gzf) {
    cerr << "Fluid Error -- updateMeshFromUni(): Unable to open file: " << filename << endl;
    return false;
  }

  int readBytes = 0;
  char file_magic[5] = {0, 0, 0, 0, 0};
  readBytes = gzread(gzf, file_magic, 4);
  if (!readBytes) {
    cerr << "Fluid Error -- updateMeshFromUni(): Unable to read header in file: " << filename
         << endl;
    gzclose(gzf);
    return false;
  }

  vector<pVel> *velocityPointer = mMeshVelocities;

  // mdata uni header
  const int STR_LEN_PDATA = 256;
  int elementType, bytesPerElement, numParticles;
  char info[STR_LEN_PDATA];      // mantaflow build information
  unsigned long long timestamp;  // creation time

  // read mesh header
  gzread(gzf, &ibuffer, sizeof(int) * 4);  // num particles, dimX, dimY, dimZ
  gzread(gzf, &elementType, sizeof(int));
  gzread(gzf, &bytesPerElement, sizeof(int));
  gzread(gzf, &info, sizeof(info));
  gzread(gzf, &timestamp, sizeof(unsigned long long));

  if (with_debug)
    cout << "Fluid: Read " << ibuffer[0] << " vertices in file: " << filename << endl;

  // Sanity checks
  const int meshSize = sizeof(float) * 3 + sizeof(int);
  if (!(bytesPerElement == meshSize) && (elementType == 0)) {
    cerr << "Fluid Error -- updateMeshFromUni(): Invalid header in file: " << filename << endl;
    gzclose(gzf);
    return false;
  }
  if (!ibuffer[0]) {  // Any vertices present?
    cerr << "Fluid Error -- updateMeshFromUni(): No vertices present in file: " << filename
         << endl;
    gzclose(gzf);
    return false;
  }

  // Reading mesh
  if (!strcmp(file_magic, "MB01")) {
    // TODO (sebbas): Future update could add uni mesh support
  }
  // Reading mesh data file v1 with vec3
  else if (!strcmp(file_magic, "MD01")) {
    numParticles = ibuffer[0];

    velocityPointer->resize(numParticles);
    MANTA::pVel *bufferPVel;
    for (vector<pVel>::iterator it = velocityPointer->begin(); it != velocityPointer->end();
         ++it) {
      gzread(gzf, fbuffer, sizeof(float) * 3);
      bufferPVel = (MANTA::pVel *)fbuffer;
      it->pos[0] = bufferPVel->pos[0];
      it->pos[1] = bufferPVel->pos[1];
      it->pos[2] = bufferPVel->pos[2];
    }
  }
  return (gzclose(gzf) == Z_OK);
}

bool MANTA::updateParticlesFromFile(string filename, bool isSecondarySys, bool isVelData)
{
  if (with_debug)
    cout << "MANTA::updateParticlesFromFile()" << endl;

  string fname(filename);
  string::size_type idx;

  idx = fname.rfind('.');
  if (idx != string::npos) {
    string extension = fname.substr(idx + 1);

    if (extension.compare("uni") == 0)
      return updateParticlesFromUni(filename, isSecondarySys, isVelData);
    else
      cerr << "Fluid Error -- updateParticlesFromFile(): Invalid file extension in file: "
           << filename << endl;
    return false;
  }
  else {
    cerr << "Fluid Error -- updateParticlesFromFile(): Unable to open file: " << filename << endl;
    return false;
  }
}

bool MANTA::updateParticlesFromUni(string filename, bool isSecondarySys, bool isVelData)
{
  if (with_debug)
    cout << "MANTA::updateParticlesFromUni()" << endl;

  gzFile gzf;
  int ibuffer[4];

  gzf = (gzFile)BLI_gzopen(filename.c_str(), "rb1");  // do some compression
  if (!gzf) {
    cerr << "Fluid Error -- updateParticlesFromUni(): Unable to open file: " << filename << endl;
    return false;
  }

  int readBytes = 0;
  char file_magic[5] = {0, 0, 0, 0, 0};
  readBytes = gzread(gzf, file_magic, 4);
  if (!readBytes) {
    cerr << "Fluid Error -- updateParticlesFromUni(): Unable to read header in file: " << filename
         << endl;
    gzclose(gzf);
    return false;
  }

  if (!strcmp(file_magic, "PB01")) {
    cerr << "Fluid Error -- updateParticlesFromUni(): Particle uni file format v01 not "
            "supported anymore."
         << endl;
    gzclose(gzf);
    return false;
  }

  // Pointer to FLIP system or to secondary particle system
  vector<pData> *dataPointer = nullptr;
  vector<pVel> *velocityPointer = nullptr;
  vector<float> *lifePointer = nullptr;

  if (isSecondarySys) {
    dataPointer = mSndParticleData;
    velocityPointer = mSndParticleVelocity;
    lifePointer = mSndParticleLife;
  }
  else {
    dataPointer = mFlipParticleData;
    velocityPointer = mFlipParticleVelocity;
  }

  // pdata uni header
  const int STR_LEN_PDATA = 256;
  int elementType, bytesPerElement, numParticles;
  char info[STR_LEN_PDATA];      // mantaflow build information
  unsigned long long timestamp;  // creation time

  // read particle header
  gzread(gzf, &ibuffer, sizeof(int) * 4);  // num particles, dimX, dimY, dimZ
  gzread(gzf, &elementType, sizeof(int));
  gzread(gzf, &bytesPerElement, sizeof(int));
  gzread(gzf, &info, sizeof(info));
  gzread(gzf, &timestamp, sizeof(unsigned long long));

  if (with_debug)
    cout << "Fluid: Read " << ibuffer[0] << " particles in file: " << filename << endl;

  // Sanity checks
  const int partSysSize = sizeof(float) * 3 + sizeof(int);
  if (!(bytesPerElement == partSysSize) && (elementType == 0)) {
    cerr << "Fluid Error -- updateParticlesFromUni(): Invalid header in file: " << filename
         << endl;
    gzclose(gzf);
    return false;
  }
  if (!ibuffer[0]) {  // Any particles present?
    if (with_debug)
      cout << "Fluid: No particles present in file: " << filename << endl;
    gzclose(gzf);
    return true;  // return true since having no particles in a cache file is valid
  }

  numParticles = ibuffer[0];

  const int numChunks = (int)(ceil((float)numParticles / PARTICLE_CHUNK));
  int todoParticles, readLen;
  int readStart, readEnd;

  // Reading base particle system file v2
  if (!strcmp(file_magic, "PB02")) {
    MANTA::pData *bufferPData;
    todoParticles = numParticles;
    bufferPData = (MANTA::pData *)MEM_malloc_arrayN(
        PARTICLE_CHUNK, sizeof(MANTA::pData), "fluid_particle_data");

    dataPointer->resize(numParticles);

    for (int i = 0; i < numChunks && todoParticles > 0; ++i) {
      readLen = PARTICLE_CHUNK;
      if (todoParticles < PARTICLE_CHUNK) {
        readLen = todoParticles;
      }

      readBytes = gzread(gzf, bufferPData, readLen * sizeof(pData));
      if (!readBytes) {
        cerr << "Fluid Error -- updateParticlesFromUni(): Unable to read particle data in file: "
             << filename << endl;
        MEM_freeN(bufferPData);
        gzclose(gzf);
        return false;
      }

      readStart = (numParticles - todoParticles);
      CLAMP(readStart, 0, numParticles);
      readEnd = readStart + readLen;
      CLAMP(readEnd, 0, numParticles);

      int k = 0;
      for (vector<MANTA::pData>::size_type j = readStart; j < readEnd; j++, k++) {
        dataPointer->at(j).pos[0] = bufferPData[k].pos[0];
        dataPointer->at(j).pos[1] = bufferPData[k].pos[1];
        dataPointer->at(j).pos[2] = bufferPData[k].pos[2];
        dataPointer->at(j).flag = bufferPData[k].flag;
      }
      todoParticles -= readLen;
    }
    MEM_freeN(bufferPData);
  }
  // Reading particle data file v1 with velocities
  else if (!strcmp(file_magic, "PD01") && isVelData) {
    MANTA::pVel *bufferPVel;
    todoParticles = numParticles;
    bufferPVel = (MANTA::pVel *)MEM_malloc_arrayN(
        PARTICLE_CHUNK, sizeof(MANTA::pVel), "fluid_particle_velocity");

    velocityPointer->resize(numParticles);

    for (int i = 0; i < numChunks && todoParticles > 0; ++i) {
      readLen = PARTICLE_CHUNK;
      if (todoParticles < PARTICLE_CHUNK) {
        readLen = todoParticles;
      }

      readBytes = gzread(gzf, bufferPVel, readLen * sizeof(pVel));
      if (!readBytes) {
        cerr << "Fluid Error -- updateParticlesFromUni(): Unable to read particle velocities "
                "in file: "
             << filename << endl;
        MEM_freeN(bufferPVel);
        gzclose(gzf);
        return false;
      }

      readStart = (numParticles - todoParticles);
      CLAMP(readStart, 0, numParticles);
      readEnd = readStart + readLen;
      CLAMP(readEnd, 0, numParticles);

      int k = 0;
      for (vector<MANTA::pVel>::size_type j = readStart; j < readEnd; j++, k++) {
        velocityPointer->at(j).pos[0] = bufferPVel[k].pos[0];
        velocityPointer->at(j).pos[1] = bufferPVel[k].pos[1];
        velocityPointer->at(j).pos[2] = bufferPVel[k].pos[2];
      }
      todoParticles -= readLen;
    }
    MEM_freeN(bufferPVel);
  }
  // Reading particle data file v1 with lifetime
  else if (!strcmp(file_magic, "PD01")) {
    float *bufferPLife;
    todoParticles = numParticles;
    bufferPLife = (float *)MEM_malloc_arrayN(PARTICLE_CHUNK, sizeof(float), "fluid_particle_life");

    lifePointer->resize(numParticles);

    for (int i = 0; i < numChunks && todoParticles > 0; ++i) {
      readLen = PARTICLE_CHUNK;
      if (todoParticles < PARTICLE_CHUNK) {
        readLen = todoParticles;
      }

      readBytes = gzread(gzf, bufferPLife, readLen * sizeof(float));
      if (!readBytes) {
        cerr << "Fluid Error -- updateParticlesFromUni(): Unable to read particle life in file: "
             << filename << endl;
        MEM_freeN(bufferPLife);
        gzclose(gzf);
        return false;
      }

      readStart = (numParticles - todoParticles);
      CLAMP(readStart, 0, numParticles);
      readEnd = readStart + readLen;
      CLAMP(readEnd, 0, numParticles);

      int k = 0;
      for (vector<float>::size_type j = readStart; j < readEnd; j++, k++) {
        lifePointer->at(j) = bufferPLife[k];
      }
      todoParticles -= readLen;
    }
    MEM_freeN(bufferPLife);
  }
  return (gzclose(gzf) == Z_OK);
}

bool MANTA::updateGridsFromFile(string filename, vector<GridItem> grids)
{
  if (with_debug)
    cout << "MANTA::updateGridsFromFile()" << endl;

  if (grids.empty()) {
    cerr << "Fluid Error -- updateGridsFromFile(): Cannot read into uninitialized grid vector."
         << endl;
    return false;
  }

  string fname(filename);
  string::size_type idx;

  idx = fname.rfind('.');
  if (idx != string::npos) {
    string extension = fname.substr(idx);

    if (extension.compare(FLUID_DOMAIN_EXTENSION_UNI) == 0) {
      return updateGridsFromUni(filename, grids);
    }
#if OPENVDB == 1
    else if (extension.compare(FLUID_DOMAIN_EXTENSION_OPENVDB) == 0) {
      return updateGridsFromVDB(filename, grids);
    }
#endif
    else if (extension.compare(FLUID_DOMAIN_EXTENSION_RAW) == 0) {
      return updateGridsFromRaw(filename, grids);
    }
    else {
      cerr << "Fluid Error -- updateGridsFromFile(): Invalid file extension in file: " << filename
           << endl;
    }
    return false;
  }
  else {
    cerr << "Fluid Error -- updateGridsFromFile(): Unable to open file: " << filename << endl;
    return false;
  }
}

bool MANTA::updateGridsFromUni(string filename, vector<GridItem> grids)
{
  if (with_debug)
    cout << "MANTA::updateGridsFromUni()" << endl;

  gzFile gzf;
  int expectedBytes = 0, readBytes = 0;
  int ibuffer[4];

  gzf = (gzFile)BLI_gzopen(filename.c_str(), "rb1");
  if (!gzf) {
    cerr << "Fluid Error -- updateGridsFromUni(): Unable to open file: " << filename << endl;
    return false;
  }

  char file_magic[5] = {0, 0, 0, 0, 0};
  readBytes = gzread(gzf, file_magic, 4);
  if (!readBytes) {
    cerr << "Fluid Error -- updateGridsFromUni(): Invalid header in file: " << filename << endl;
    gzclose(gzf);
    return false;
  }
  if (!strcmp(file_magic, "DDF2") || !strcmp(file_magic, "MNT1") || !strcmp(file_magic, "MNT2")) {
    cerr << "Fluid Error -- updateGridsFromUni(): Unsupported header in file: " << filename
         << endl;
    gzclose(gzf);
    return false;
  }

  if (!strcmp(file_magic, "MNT3")) {

    // grid uni header
    const int STR_LEN_GRID = 252;
    int elementType, bytesPerElement;  // data type info
    char info[STR_LEN_GRID];           // mantaflow build information
    int dimT;                          // optionally store forth dimension for 4d grids
    unsigned long long timestamp;      // creation time

    // read grid header
    gzread(gzf, &ibuffer, sizeof(int) * 4);  // dimX, dimY, dimZ, gridType
    gzread(gzf, &elementType, sizeof(int));
    gzread(gzf, &bytesPerElement, sizeof(int));
    gzread(gzf, &info, sizeof(info));
    gzread(gzf, &dimT, sizeof(int));
    gzread(gzf, &timestamp, sizeof(unsigned long long));

    if (with_debug)
      cout << "Fluid: Read " << ibuffer[3] << " grid type in file: " << filename << endl;

    for (vector<GridItem>::iterator gIter = grids.begin(); gIter != grids.end(); ++gIter) {
      GridItem gridItem = *gIter;
      void **pointerList = gridItem.pointer;
      int type = gridItem.type;
      int *res = gridItem.res;
      assert(pointerList[0]);
      assert(res[0] == res[0] && res[1] == res[1] && res[2] == res[2]);
      UNUSED_VARS(res);

      switch (type) {
        case FLUID_DOMAIN_GRID_VEC3F: {
          assert(pointerList[1] && pointerList[2]);
          float **fpointers = (float **)pointerList;
          expectedBytes = sizeof(float) * 3 * ibuffer[0] * ibuffer[1] * ibuffer[2];
          readBytes = 0;
          for (int i = 0; i < ibuffer[0] * ibuffer[1] * ibuffer[2]; ++i) {
            for (int j = 0; j < 3; ++j) {
              readBytes += gzread(gzf, fpointers[j], sizeof(float));
              ++fpointers[j];
            }
          }
          break;
        }
        case FLUID_DOMAIN_GRID_FLOAT: {
          float **fpointers = (float **)pointerList;
          expectedBytes = sizeof(float) * ibuffer[0] * ibuffer[1] * ibuffer[2];
          readBytes = gzread(
              gzf, fpointers[0], sizeof(float) * ibuffer[0] * ibuffer[1] * ibuffer[2]);
          break;
        }
        default: {
          cerr << "Fluid Error -- Unknown grid type" << endl;
        }
      }

      if (!readBytes) {
        cerr << "Fluid Error -- updateGridFromRaw(): Unable to read raw file: " << filename
             << endl;
        gzclose(gzf);
        return false;
      }
      assert(expectedBytes == readBytes);
      UNUSED_VARS(expectedBytes);

      if (with_debug)
        cout << "Fluid: Read successfully: " << filename << endl;
    }
  }
  else {
    cerr << "Fluid Error -- updateGridsFromUni(): Unknown header in file: " << filename << endl;
    gzclose(gzf);
    return false;
  }

  return (gzclose(gzf) == Z_OK);
}

#if OPENVDB == 1
bool MANTA::updateGridsFromVDB(string filename, vector<GridItem> grids)
{
  if (with_debug)
    cout << "MANTA::updateGridsFromVDB()" << endl;

  openvdb::initialize();
  openvdb::io::File file(filename);
  try {
    file.open();
  }
  catch (const openvdb::IoError &) {
    cerr << "Fluid Error -- updateGridsFromVDB(): IOError, invalid OpenVDB file: " << filename
         << endl;
    return false;
  }
  if (grids.empty()) {
    cerr << "Fluid Error -- updateGridsFromVDB(): No grids found in grid vector" << endl;
    return false;
  }

  unordered_map<string, openvdb::FloatGrid::Accessor> floatAccessors;
  unordered_map<string, openvdb::Vec3SGrid::Accessor> vec3fAccessors;
  openvdb::GridBase::Ptr baseGrid;

  /* Get accessors to all grids in this OpenVDB file.*/
  for (vector<GridItem>::iterator gIter = grids.begin(); gIter != grids.end(); ++gIter) {
    GridItem gridItem = *gIter;
    string itemName = gridItem.name;
    int itemType = gridItem.type;

    for (openvdb::io::File::NameIterator nameIter = file.beginName(); nameIter != file.endName();
         ++nameIter) {
      string vdbName = nameIter.gridName();
      bool nameMatch = !itemName.compare(vdbName);

      /* Support for <= 2.83: If file has only one grid in it, use that grid. */
      openvdb::io::File::NameIterator peekNext = nameIter;
      bool onlyGrid = (++peekNext == file.endName());
      if (onlyGrid) {
        vdbName = itemName;
      }

      if (nameMatch || onlyGrid) {
        baseGrid = file.readGrid(nameIter.gridName());

        switch (itemType) {
          case FLUID_DOMAIN_GRID_VEC3F: {
            openvdb::Vec3SGrid::Ptr gridVDB = openvdb::gridPtrCast<openvdb::Vec3SGrid>(baseGrid);
            openvdb::Vec3SGrid::Accessor vdbAccessor = gridVDB->getAccessor();
            vec3fAccessors.emplace(vdbName, vdbAccessor);
            break;
          }
          case FLUID_DOMAIN_GRID_FLOAT: {
            openvdb::FloatGrid::Ptr gridVDB = openvdb::gridPtrCast<openvdb::FloatGrid>(baseGrid);
            openvdb::FloatGrid::Accessor vdbAccessor = gridVDB->getAccessor();
            floatAccessors.emplace(vdbName, vdbAccessor);
            break;
          }
          default: {
            cerr << "Fluid Error -- Unknown grid type" << endl;
          }
        }
      }
      else {
        cerr << "Fluid Error -- Could not read grid from file" << endl;
        return false;
      }
    }
  }
  file.close();

  size_t index = 0;

  /* Use res of first grid for grid loop. All grids must be same size anyways. */
  vector<GridItem>::iterator gIter = grids.begin();
  int *res = (*gIter).res;

  for (int z = 0; z < res[2]; ++z) {
    for (int y = 0; y < res[1]; ++y) {
      for (int x = 0; x < res[0]; ++x, ++index) {
        openvdb::Coord xyz(x, y, z);

        for (vector<GridItem>::iterator gIter = grids.begin(); gIter != grids.end(); ++gIter) {
          GridItem gridItem = *gIter;
          void **pointerList = gridItem.pointer;
          int type = gridItem.type;
          int *res = gridItem.res;
          assert(pointerList[0]);
          assert(res[0] == res[0] && res[1] == res[1] && res[2] == res[2]);
          UNUSED_VARS(res);

          switch (type) {
            case FLUID_DOMAIN_GRID_VEC3F: {
              unordered_map<string, openvdb::Vec3SGrid::Accessor>::iterator it;
              it = vec3fAccessors.find(gridItem.name);
              if (it == vec3fAccessors.end()) {
                cerr << "Fluid Error -- '" << gridItem.name << "' not in vdb grid map" << endl;
                return false;
              }
              openvdb::Vec3f v = it->second.getValue(xyz);

              assert(pointerList[1] && pointerList[2]);
              float **fpointers = (float **)pointerList;
              for (int j = 0; j < 3; ++j) {
                (fpointers[j])[index] = (float)v[j];
              }
              break;
            }
            case FLUID_DOMAIN_GRID_FLOAT: {
              unordered_map<string, openvdb::FloatGrid::Accessor>::iterator it;
              it = floatAccessors.find(gridItem.name);
              if (it == floatAccessors.end()) {
                cerr << "Fluid Error -- '" << gridItem.name << "' not in vdb grid map" << endl;
                return false;
              }
              float v = it->second.getValue(xyz);
              float **fpointers = (float **)pointerList;
              (fpointers[0])[index] = v;
              break;
            }
            default: {
              cerr << "Fluid Error -- Unknown grid type" << endl;
            }
          }
        }
      }
    }
  }
  if (with_debug)
    cout << "Fluid: Read successfully: " << filename << endl;

  return true;
}
#endif

bool MANTA::updateGridsFromRaw(string filename, vector<GridItem> grids)
{
  if (with_debug)
    cout << "MANTA::updateGridsFromRaw()" << endl;

  gzFile gzf;
  int expectedBytes, readBytes;

  gzf = (gzFile)BLI_gzopen(filename.c_str(), "rb");
  if (!gzf) {
    cout << "MANTA::updateGridsFromRaw(): unable to open file" << endl;
    return false;
  }

  for (vector<GridItem>::iterator gIter = grids.begin(); gIter != grids.end(); ++gIter) {
    GridItem gridItem = *gIter;
    void **pointerList = gridItem.pointer;
    int type = gridItem.type;
    int *res = gridItem.res;
    assert(pointerList[0]);
    assert(res[0] == res[0] && res[1] == res[1] && res[2] == res[2]);
    UNUSED_VARS(res);

    switch (type) {
      case FLUID_DOMAIN_GRID_VEC3F: {
        assert(pointerList[1] && pointerList[2]);
        float **fpointers = (float **)pointerList;
        expectedBytes = sizeof(float) * 3 * res[0] * res[1] * res[2];
        readBytes = 0;
        for (int i = 0; i < res[0] * res[1] * res[2]; ++i) {
          for (int j = 0; j < 3; ++j) {
            readBytes += gzread(gzf, fpointers[j], sizeof(float));
            ++fpointers[j];
          }
        }
        break;
      }
      case FLUID_DOMAIN_GRID_FLOAT: {
        float **fpointers = (float **)pointerList;
        expectedBytes = sizeof(float) * res[0] * res[1] * res[2];
        readBytes = gzread(gzf, fpointers[0], expectedBytes);
        break;
      }
      default: {
        cerr << "Fluid Error -- Unknown grid type" << endl;
      }
    }

    if (!readBytes) {
      cerr << "Fluid Error -- updateGridsFromRaw(): Unable to read raw file: " << filename << endl;
      gzclose(gzf);
      return false;
    }
    assert(expectedBytes == readBytes);

    if (with_debug)
      cout << "Fluid: Read successfully: " << filename << endl;
  }

  if (with_debug)
    cout << "Fluid: Read successfully: " << filename << endl;

  return (gzclose(gzf) == Z_OK);
}

void MANTA::updatePointers()
{
  if (with_debug)
    cout << "MANTA::updatePointers()" << endl;

  string func = "getDataPointer";
  string funcNodes = "getNodesDataPointer";
  string funcTris = "getTrisDataPointer";

  string id = to_string(mCurrentID);
  string solver = "s" + id;
  string parts = "pp" + id;
  string snd = "sp" + id;
  string mesh = "sm" + id;
  string mesh2 = "mesh" + id;
  string noise = "sn" + id;
  string solver_ext = "_" + solver;
  string parts_ext = "_" + parts;
  string snd_ext = "_" + snd;
  string mesh_ext = "_" + mesh;
  string mesh_ext2 = "_" + mesh2;
  string noise_ext = "_" + noise;

  mFlags = (int *)pyObjectToPointer(callPythonFunction("flags" + solver_ext, func));
  mPhiIn = (float *)pyObjectToPointer(callPythonFunction("phiIn" + solver_ext, func));
  mPhiStaticIn = (float *)pyObjectToPointer(callPythonFunction("phiSIn" + solver_ext, func));
  mVelocityX = (float *)pyObjectToPointer(callPythonFunction("x_vel" + solver_ext, func));
  mVelocityY = (float *)pyObjectToPointer(callPythonFunction("y_vel" + solver_ext, func));
  mVelocityZ = (float *)pyObjectToPointer(callPythonFunction("z_vel" + solver_ext, func));
  mForceX = (float *)pyObjectToPointer(callPythonFunction("x_force" + solver_ext, func));
  mForceY = (float *)pyObjectToPointer(callPythonFunction("y_force" + solver_ext, func));
  mForceZ = (float *)pyObjectToPointer(callPythonFunction("z_force" + solver_ext, func));

  if (mUsingOutflow) {
    mPhiOutIn = (float *)pyObjectToPointer(callPythonFunction("phiOutIn" + solver_ext, func));
    mPhiOutStaticIn = (float *)pyObjectToPointer(
        callPythonFunction("phiOutSIn" + solver_ext, func));
  }
  if (mUsingObstacle) {
    mPhiObsIn = (float *)pyObjectToPointer(callPythonFunction("phiObsIn" + solver_ext, func));
    mPhiObsStaticIn = (float *)pyObjectToPointer(
        callPythonFunction("phiObsSIn" + solver_ext, func));
    mObVelocityX = (float *)pyObjectToPointer(callPythonFunction("x_obvel" + solver_ext, func));
    mObVelocityY = (float *)pyObjectToPointer(callPythonFunction("y_obvel" + solver_ext, func));
    mObVelocityZ = (float *)pyObjectToPointer(callPythonFunction("z_obvel" + solver_ext, func));
    mNumObstacle = (float *)pyObjectToPointer(callPythonFunction("numObs" + solver_ext, func));
  }
  if (mUsingGuiding) {
    mPhiGuideIn = (float *)pyObjectToPointer(callPythonFunction("phiGuideIn" + solver_ext, func));
    mGuideVelocityX = (float *)pyObjectToPointer(
        callPythonFunction("x_guidevel" + solver_ext, func));
    mGuideVelocityY = (float *)pyObjectToPointer(
        callPythonFunction("y_guidevel" + solver_ext, func));
    mGuideVelocityZ = (float *)pyObjectToPointer(
        callPythonFunction("z_guidevel" + solver_ext, func));
    mNumGuide = (float *)pyObjectToPointer(callPythonFunction("numGuides" + solver_ext, func));
  }
  if (mUsingInvel) {
    mInVelocityX = (float *)pyObjectToPointer(callPythonFunction("x_invel" + solver_ext, func));
    mInVelocityY = (float *)pyObjectToPointer(callPythonFunction("y_invel" + solver_ext, func));
    mInVelocityZ = (float *)pyObjectToPointer(callPythonFunction("z_invel" + solver_ext, func));
  }
  if (mUsingSmoke) {
    mDensity = (float *)pyObjectToPointer(callPythonFunction("density" + solver_ext, func));
    mDensityIn = (float *)pyObjectToPointer(callPythonFunction("densityIn" + solver_ext, func));
    mShadow = (float *)pyObjectToPointer(callPythonFunction("shadow" + solver_ext, func));
    mEmissionIn = (float *)pyObjectToPointer(callPythonFunction("emissionIn" + solver_ext, func));
  }
  if (mUsingSmoke && mUsingHeat) {
    mHeat = (float *)pyObjectToPointer(callPythonFunction("heat" + solver_ext, func));
    mHeatIn = (float *)pyObjectToPointer(callPythonFunction("heatIn" + solver_ext, func));
  }
  if (mUsingSmoke && mUsingFire) {
    mFlame = (float *)pyObjectToPointer(callPythonFunction("flame" + solver_ext, func));
    mFuel = (float *)pyObjectToPointer(callPythonFunction("fuel" + solver_ext, func));
    mReact = (float *)pyObjectToPointer(callPythonFunction("react" + solver_ext, func));
    mFuelIn = (float *)pyObjectToPointer(callPythonFunction("fuelIn" + solver_ext, func));
    mReactIn = (float *)pyObjectToPointer(callPythonFunction("reactIn" + solver_ext, func));
  }
  if (mUsingSmoke && mUsingColors) {
    mColorR = (float *)pyObjectToPointer(callPythonFunction("color_r" + solver_ext, func));
    mColorG = (float *)pyObjectToPointer(callPythonFunction("color_g" + solver_ext, func));
    mColorB = (float *)pyObjectToPointer(callPythonFunction("color_b" + solver_ext, func));
    mColorRIn = (float *)pyObjectToPointer(callPythonFunction("color_r_in" + solver_ext, func));
    mColorGIn = (float *)pyObjectToPointer(callPythonFunction("color_g_in" + solver_ext, func));
    mColorBIn = (float *)pyObjectToPointer(callPythonFunction("color_b_in" + solver_ext, func));
  }
  if (mUsingSmoke && mUsingNoise) {
    mDensityHigh = (float *)pyObjectToPointer(callPythonFunction("density" + noise_ext, func));
    mTextureU = (float *)pyObjectToPointer(callPythonFunction("texture_u" + solver_ext, func));
    mTextureV = (float *)pyObjectToPointer(callPythonFunction("texture_v" + solver_ext, func));
    mTextureW = (float *)pyObjectToPointer(callPythonFunction("texture_w" + solver_ext, func));
    mTextureU2 = (float *)pyObjectToPointer(callPythonFunction("texture_u2" + solver_ext, func));
    mTextureV2 = (float *)pyObjectToPointer(callPythonFunction("texture_v2" + solver_ext, func));
    mTextureW2 = (float *)pyObjectToPointer(callPythonFunction("texture_w2" + solver_ext, func));
  }
  if (mUsingSmoke && mUsingNoise && mUsingFire) {
    mFlameHigh = (float *)pyObjectToPointer(callPythonFunction("flame" + noise_ext, func));
    mFuelHigh = (float *)pyObjectToPointer(callPythonFunction("fuel" + noise_ext, func));
    mReactHigh = (float *)pyObjectToPointer(callPythonFunction("react" + noise_ext, func));
  }
  if (mUsingSmoke && mUsingNoise && mUsingColors) {
    mColorRHigh = (float *)pyObjectToPointer(callPythonFunction("color_r" + noise_ext, func));
    mColorGHigh = (float *)pyObjectToPointer(callPythonFunction("color_g" + noise_ext, func));
    mColorBHigh = (float *)pyObjectToPointer(callPythonFunction("color_b" + noise_ext, func));
  }
  if (mUsingLiquid) {
    mPhi = (float *)pyObjectToPointer(callPythonFunction("phi" + solver_ext, func));
    mFlipParticleData = (vector<pData> *)pyObjectToPointer(
        callPythonFunction("pp" + solver_ext, func));
    mFlipParticleVelocity = (vector<pVel> *)pyObjectToPointer(
        callPythonFunction("pVel" + parts_ext, func));
  }
  if (mUsingLiquid && mUsingMesh) {
    mMeshNodes = (vector<Node> *)pyObjectToPointer(
        callPythonFunction("mesh" + mesh_ext, funcNodes));
    mMeshTriangles = (vector<Triangle> *)pyObjectToPointer(
        callPythonFunction("mesh" + mesh_ext, funcTris));
  }
  if (mUsingLiquid && mUsingMVel) {
    mMeshVelocities = (vector<pVel> *)pyObjectToPointer(
        callPythonFunction("mVel" + mesh_ext2, func));
  }
  if (mUsingLiquid && (mUsingDrops | mUsingBubbles | mUsingFloats | mUsingTracers)) {
    mSndParticleData = (vector<pData> *)pyObjectToPointer(
        callPythonFunction("ppSnd" + snd_ext, func));
    mSndParticleVelocity = (vector<pVel> *)pyObjectToPointer(
        callPythonFunction("pVelSnd" + parts_ext, func));
    mSndParticleLife = (vector<float> *)pyObjectToPointer(
        callPythonFunction("pLifeSnd" + parts_ext, func));
  }

  mFlipFromFile = false;
  mMeshFromFile = false;
  mParticlesFromFile = false;
  mSmokeFromFile = false;
  mNoiseFromFile = false;
}

bool MANTA::hasConfig(FluidModifierData *mmd, int framenr)
{
  string extension = FLUID_DOMAIN_EXTENSION_UNI;
  return BLI_exists(
      getFile(mmd, FLUID_DOMAIN_DIR_CONFIG, FLUID_FILENAME_CONFIG, extension, framenr).c_str());
}

bool MANTA::hasData(FluidModifierData *mmd, int framenr)
{
  string filename = (mUsingSmoke) ? FLUID_FILENAME_DENSITY : FLUID_FILENAME_PP;
  string extension = getCacheFileEnding(mmd->domain->cache_data_format);
  return BLI_exists(getFile(mmd, FLUID_DOMAIN_DIR_DATA, filename, extension, framenr).c_str());
}

bool MANTA::hasNoise(FluidModifierData *mmd, int framenr)
{
  string extension = getCacheFileEnding(mmd->domain->cache_noise_format);
  return BLI_exists(
      getFile(mmd, FLUID_DOMAIN_DIR_NOISE, FLUID_FILENAME_DENSITYNOISE, extension, framenr)
          .c_str());
}

bool MANTA::hasMesh(FluidModifierData *mmd, int framenr)
{
  string extension = getCacheFileEnding(mmd->domain->cache_mesh_format);
  return BLI_exists(
      getFile(mmd, FLUID_DOMAIN_DIR_MESH, FLUID_FILENAME_MESH, extension, framenr).c_str());
}

bool MANTA::hasParticles(FluidModifierData *mmd, int framenr)
{
  string extension = getCacheFileEnding(mmd->domain->cache_particle_format);
  return BLI_exists(
      getFile(mmd, FLUID_DOMAIN_DIR_PARTICLES, FLUID_FILENAME_PPSND, extension, framenr).c_str());
}

bool MANTA::hasGuiding(FluidModifierData *mmd, int framenr, bool sourceDomain)
{
  string subdirectory = (sourceDomain) ? FLUID_DOMAIN_DIR_DATA : FLUID_DOMAIN_DIR_GUIDE;
  string filename = (sourceDomain) ? FLUID_FILENAME_VELOCITY : FLUID_FILENAME_GUIDEVEL;
  string extension = getCacheFileEnding(mmd->domain->cache_data_format);
  return BLI_exists(getFile(mmd, subdirectory, filename, extension, framenr).c_str());
}

string MANTA::getDirectory(FluidModifierData *mmd, string subdirectory)
{
  char directory[FILE_MAX];
  BLI_path_join(
      directory, sizeof(directory), mmd->domain->cache_directory, subdirectory.c_str(), nullptr);
  BLI_path_make_safe(directory);
  return directory;
}

string MANTA::getFile(
    FluidModifierData *mmd, string subdirectory, string fname, string extension, int framenr)
{
  char targetFile[FILE_MAX];
  string path = getDirectory(mmd, subdirectory);
  string filename = fname + extension;
  BLI_join_dirfile(targetFile, sizeof(targetFile), path.c_str(), filename.c_str());
  BLI_path_frame(targetFile, framenr, 0);
  return targetFile;
}
