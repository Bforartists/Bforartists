# SPDX-FileCopyrightText: 2019-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(OIDN_EXTRA_ARGS
  -DOIDN_APPS=OFF
  -DTBB_ROOT=${LIBDIR}/tbb
  -DISPC_EXECUTABLE=${LIBDIR}/ispc/bin/ispc
  -DOIDN_FILTER_RTLIGHTMAP=OFF
  -DPython_EXECUTABLE=${PYTHON_BINARY}
)
if(NOT APPLE)
  set(OIDN_EXTRA_ARGS
    ${OIDN_EXTRA_ARGS}
    -DOIDN_DEVICE_SYCL=ON
    -DOIDN_DEVICE_SYCL_AOT=OFF
    -DLEVEL_ZERO_ROOT=${LIBDIR}/level-zero/lib
  )
endif()

if(WIN32)
  set(OIDN_EXTRA_ARGS
    ${OIDN_EXTRA_ARGS}
    -DTBB_DEBUG_LIBRARY=${LIBDIR}/tbb/lib/tbb.lib
    -DTBB_DEBUG_LIBRARY_MALLOC=${LIBDIR}/tbb/lib/tbbmalloc.lib
    -DCMAKE_CXX_COMPILER=${LIBDIR}/dpcpp/bin/clang++.exe
    -DCMAKE_C_COMPILER=${LIBDIR}/dpcpp/bin/clang.exe
    -DCMAKE_DEBUG_POSTFIX=_d
  )
  set(OIDN_CMAKE_FLAGS ${DEFAULT_CLANG_CMAKE_FLAGS}
    -DCMAKE_CXX_COMPILER=${LIBDIR}/dpcpp/bin/clang++.exe
    -DCMAKE_C_COMPILER=${LIBDIR}/dpcpp/bin/clang.exe
    -DCMAKE_SHARED_LINKER_FLAGS=-L"${LIBDIR}/dpcpp/lib"
    -DCMAKE_EXE_LINKER_FLAGS=-L"${LIBDIR}/dpcpp/lib"
  )
else()
  if(NOT APPLE)
    set(OIDN_EXTRA_ARGS
      ${OIDN_EXTRA_ARGS}
      -DCMAKE_CXX_COMPILER=${LIBDIR}/dpcpp/bin/clang++
      -DCMAKE_C_COMPILER=${LIBDIR}/dpcpp/bin/clang
      -DCMAKE_FIND_ROOT_PATH=${LIBDIR}/ocloc
    )
  endif()
  set(OIDN_CMAKE_FLAGS ${DEFAULT_CMAKE_FLAGS})
endif()

ExternalProject_Add(external_openimagedenoise
  URL file://${PACKAGE_DIR}/${OIDN_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${OIDN_HASH_TYPE}=${OIDN_HASH}
  PREFIX ${BUILD_DIR}/openimagedenoise
  CMAKE_GENERATOR ${PLATFORM_ALT_GENERATOR}
  CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${LIBDIR}/openimagedenoise ${OIDN_CMAKE_FLAGS} ${OIDN_EXTRA_ARGS}
  PATCH_COMMAND ${PATCH_CMD} --verbose -p 1 -N -d ${BUILD_DIR}/openimagedenoise/src/external_openimagedenoise < ${PATCH_DIR}/oidn.diff
  INSTALL_DIR ${LIBDIR}/openimagedenoise
)

add_dependencies(
  external_openimagedenoise
  external_tbb
  external_ispc
  external_python
)

if(BUILD_MODE STREQUAL Release AND WIN32)
    ExternalProject_Add_Step(external_openimagedenoise after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${LIBDIR}/openimagedenoise/bin ${HARVEST_TARGET}/openimagedenoise/bin
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${LIBDIR}/openimagedenoise/lib ${HARVEST_TARGET}/openimagedenoise/lib
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${LIBDIR}/openimagedenoise/include ${HARVEST_TARGET}/openimagedenoise/include
      DEPENDEES install
    )
endif()
