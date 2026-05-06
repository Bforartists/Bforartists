# SPDX-FileCopyrightText: 2002-2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set(TRACY_EXTRA_ARGS
  -DCMAKE_DEBUG_POSTFIX=_d
  -DTRACY_ENABLE=ON
)

ExternalProject_Add(external_tracy
  URL file://${PACKAGE_DIR}/${TRACY_FILE}
  DOWNLOAD_DIR ${DOWNLOAD_DIR}
  URL_HASH ${TRACY_HASH_TYPE}=${TRACY_HASH}
  PREFIX ${BUILD_DIR}/tracy

  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${LIBDIR}/tracy
    ${DEFAULT_CMAKE_FLAGS}
    ${TRACY_EXTRA_ARGS}

  INSTALL_DIR ${LIBDIR}/tracy
)

if(WIN32)
  if(BUILD_MODE STREQUAL Release)
    ExternalProject_Add_Step(external_tracy after_install
      COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${LIBDIR}/tracy
        ${HARVEST_TARGET}/tracy

      DEPENDEES install
    )
  endif()
  if(BUILD_MODE STREQUAL Debug)
    ExternalProject_Add_Step(external_tracy after_install
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/tracy/lib/Debug/TracyClient_d.lib
        ${HARVEST_TARGET}/tracy//lib/Debug/TracyClient_d.lib
      COMMAND ${CMAKE_COMMAND} -E copy
        ${LIBDIR}/tracy/lib/cmake/Tracy/TracyTargets-debug.cmake
        ${HARVEST_TARGET}/tracy/lib/cmake/Tracy/TracyTargets-debug.cmake

      DEPENDEES install
    )
  endif()
else()
  harvest(external_tracy tracy/include tracy/include "*")
  harvest(external_tracy tracy/lib tracy/lib "*.a")
  harvest(external_tracy tracy/lib/cmake/Tracy tracy/lib/cmake/Tracy "*.cmake")
endif()
