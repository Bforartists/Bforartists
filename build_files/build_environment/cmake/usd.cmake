# SPDX-FileCopyrightText: 2019-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

if(WIN32)
  # OIIO and OSL are statically linked for us, but USD doesn't know
  set(USD_CXX_FLAGS "${CMAKE_CXX_FLAGS} /DOIIO_STATIC_DEFINE /DOSL_STATIC_DEFINE")
  if(BUILD_MODE STREQUAL Debug)
    # USD does not look for debug libs, nor does it link them
    # when building static, so this is just to keep find_package happy
    # if we ever link dynamically on windows util will need to be linked as well.
    set(USD_OIIO_CMAKE_DEFINES "-DOIIO_LIBRARIES=${LIBDIR}/openimageio/lib/OpenImageIO_d${LIBEXT}^^${LIBDIR}/openimageio/lib/OpenImageIO_util_d${LIBEXT}")
  endif()
  set(USD_PLATFORM_FLAGS
    ${USD_OIIO_CMAKE_DEFINES}
    -DCMAKE_CXX_FLAGS=${USD_CXX_FLAGS}
    -D_PXR_CXX_DEFINITIONS=/DBOOST_ALL_NO_LIB
    -DCMAKE_SHARED_LINKER_FLAGS_INIT=/LIBPATH:${LIBDIR}/tbb/lib
    -DPython_FIND_REGISTRY=NEVER
    -DPython3_EXECUTABLE=${PYTHON_BINARY}
  )
  if(BUILD_MODE STREQUAL Debug)
    list(APPEND USD_PLATFORM_FLAGS -DPXR_USE_DEBUG_PYTHON=ON)
    list(APPEND USD_PLATFORM_FLAGS -DOPENVDB_LIBRARY=${LIBDIR}/openvdb/lib/openvdb_d.lib)
  endif()
elseif(UNIX)
  # Workaround USD not linking correctly with static Python library, where it would embed
  # part of the interpret in the USD library. Allow undefined Python symbols and replace
  # Python library with TBB so it doesn't complain about missing library.
  set(USD_PLATFORM_FLAGS
    # NOTE(@ideasman42): Setting the root is needed, without this an older version of Python
    # is detected from the system. Referencing the root-directory may remove the need
    # to explicitly set the `PYTHON_INCLUDE_DIR` & `PYTHON_LIBRARY`.
    # Keep them as it's known these are the libraries to use and it avoids any ambiguity.
    -DPython3_ROOT_DIR=${LIBDIR}/python/

    -DPYTHON_INCLUDE_DIR=${LIBDIR}/python/include/python${PYTHON_SHORT_VERSION}/
    -DPYTHON_LIBRARY=${LIBDIR}/tbb/lib/${LIBPREFIX}${TBB_LIBRARY}${SHAREDLIBEXT}
  )

  if(APPLE)
    set(USD_SHARED_LINKER_FLAGS "-Xlinker -undefined -Xlinker dynamic_lookup")
    list(APPEND USD_PLATFORM_FLAGS
      -DCMAKE_SHARED_LINKER_FLAGS=${USD_SHARED_LINKER_FLAGS}
    )
  endif()
endif()

set(USD_EXTRA_ARGS
  ${DEFAULT_BOOST_FLAGS}
  ${USD_PLATFORM_FLAGS}
  -DOPENSUBDIV_ROOT_DIR=${LIBDIR}/opensubdiv
  -DOpenImageIO_ROOT=${LIBDIR}/openimageio
  -DMaterialX_ROOT=${LIBDIR}/materialx
  -DOPENEXR_LIBRARIES=${LIBDIR}/imath/lib/${LIBPREFIX}Imath${OPENEXR_VERSION_POSTFIX}${SHAREDLIBEXT}
  -DOPENEXR_INCLUDE_DIR=${LIBDIR}/imath/include
  -DImath_DIR=${LIBDIR}/imath
  -DOPENVDB_LOCATION=${LIBDIR}/openvdb
  -DPXR_ENABLE_PYTHON_SUPPORT=ON
  -DPXR_USE_PYTHON_3=ON
  -DPXR_BUILD_IMAGING=ON
  -DPXR_BUILD_TESTS=OFF
  -DPXR_BUILD_EXAMPLES=OFF
  -DPXR_BUILD_TUTORIALS=OFF
  -DPXR_BUILD_USDVIEW=OFF
  -DPXR_ENABLE_HDF5_SUPPORT=OFF
  -DPXR_ENABLE_MATERIALX_SUPPORT=ON
  -DPXR_ENABLE_OPENVDB_SUPPORT=ON
  -DPYTHON_EXECUTABLE=${PYTHON_BINARY}
  -DPython3_EXECUTABLE=${PYTHON_BINARY}
  -DPXR_BUILD_MONOLITHIC=ON
  # OSL is an optional dependency of the Imaging module. However, since that
  # module was included for its support for converting primitive shapes (sphere,
  # cube, etc.) to geometry, it's not necessary. Disabling it will make it
  # simpler to build Blender; currently only Cycles uses OSL.
  -DPXR_ENABLE_OSL_SUPPORT=OFF
  # Enable OpenGL for Hydra support. Note that this indirectly also adds an X11
  # dependency on Linux. This would be good to eliminate for headless and Wayland
  # only builds, however is not worse than what Blender already links to for
  # official releases currently.
  -DPXR_ENABLE_GL_SUPPORT=ON
  # OIIO is used for loading image textures in Hydra Storm / Embree renderers.
  -DPXR_BUILD_OPENIMAGEIO_PLUGIN=ON
  # USD 22.03 does not support OCIO 2.x
  # Tracking ticket https://github.com/PixarAnimationStudios/USD/issues/1386
  -DPXR_BUILD_OPENCOLORIO_PLUGIN=OFF
  -DPXR_ENABLE_PTEX_SUPPORT=OFF
  -DPXR_BUILD_USD_TOOLS=OFF
  -DCMAKE_DEBUG_POSTFIX=_d
  -DBUILD_SHARED_LIBS=ON
  -DTBB_INCLUDE_DIRS=${LIBDIR}/tbb/include
  -DTBB_LIBRARIES=${LIBDIR}/tbb/lib/${LIBPREFIX}${TBB_LIBRARY}${SHAREDLIBEXT}
  -DTbb_TBB_LIBRARY=${LIBDIR}/tbb/lib/${LIBPREFIX}${TBB_LIBRARY}${SHAREDLIBEXT}
  -DTBB_tbb_LIBRARY_RELEASE=${LIBDIR}/tbb/lib/${LIBPREFIX}${TBB_LIBRARY}${SHAREDLIBEXT}
)

# Ray: I'm not sure if the other platforms relied on this or not but this is no longer
# needed for windows. If mac/lin confirm, this can be removed.
if(NOT WIN32)
  list(APPEND USD_EXTRA_ARGS
    # USD wants the tbb debug lib set even when you are doing a release build
    # Otherwise it will error out during the cmake configure phase.
    -DTBB_LIBRARIES_DEBUG=${LIBDIR}/tbb/lib/${LIBPREFIX}${TBB_LIBRARY}${SHAREDLIBEXT}
  )
endif()

ExternalProject_Add(external_usd
  URL file://${PACKAGE_DIR}/${USD_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${USD_HASH_TYPE}=${USD_HASH}
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}
  PREFIX ${BUILD_DIR}/usd
  LIST_SEPARATOR ^^
  # usd_pull_1965.diff  https://github.com/PixarAnimationStudios/USD/pull/1965
  # usd_hydra.diff -    https://github.com/bnagirniak/RPRHydraRenderBlenderAddon/blob/master/usd.diff
  # usd_hydra.diff also included the blender changes and usd_pull_1965 and has been edited to remove those sections.
  PATCH_COMMAND ${PATCH_CMD} -p 1 -d ${BUILD_DIR}/usd/src/external_usd < ${PATCH_DIR}/usd.diff &&
                ${PATCH_CMD} -p 1 -d ${BUILD_DIR}/usd/src/external_usd < ${PATCH_DIR}/usd_pull_1965.diff &&
                ${PATCH_CMD} -p 1 -d ${BUILD_DIR}/usd/src/external_usd < ${PATCH_DIR}/usd_hydra.diff &&
                ${PATCH_CMD} -p 1 -d ${BUILD_DIR}/usd/src/external_usd < ${PATCH_DIR}/usd_core_profile.diff
  CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${LIBDIR}/usd -Wno-dev ${DEFAULT_CMAKE_FLAGS} ${USD_EXTRA_ARGS}
  INSTALL_DIR ${LIBDIR}/usd
)

add_dependencies(
  external_usd
  external_tbb
  external_boost
  external_opensubdiv
  external_python
  external_openimageio
  external_materialx
  openvdb
)

# Since USD 21.11 the libraries are prefixed with "usd_", i.e. "libusd_m.a" became "libusd_usd_m.a".
# See https://github.com/PixarAnimationStudios/USD/blob/release/CHANGELOG.md#2111---2021-11-01
if(NOT WIN32)
  if(USD_VERSION VERSION_LESS 21.11)
    set(PXR_LIB_PREFIX "")
  else()
    set(PXR_LIB_PREFIX "usd_")
  endif()
endif()

if(WIN32)
  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_usd after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${LIBDIR}/usd ${HARVEST_TARGET}/usd
      DEPENDEES install
    )
  endif()
  if(BUILD_MODE STREQUAL Debug)
    ExternalProject_Add_Step(external_usd after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${LIBDIR}/usd/lib/python ${HARVEST_TARGET}/usd/lib/debug/python
      COMMAND ${CMAKE_COMMAND} -E copy ${LIBDIR}/usd/lib/usd_ms_d.dll ${HARVEST_TARGET}/usd/lib/usd_ms_d.dll
      COMMAND ${CMAKE_COMMAND} -E copy ${LIBDIR}/usd/lib/usd_ms_d.lib ${HARVEST_TARGET}/usd/lib/usd_ms_d.lib
      DEPENDEES install
    )
  endif()
endif()
