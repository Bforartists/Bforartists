# SPDX-License-Identifier: BSD-3-Clause
# Copyright 2023 Blender Foundation.

# - Find Vulkan libraries
# Find the Vulkan includes and libraries
# This module defines
#  VULKAN_INCLUDE_DIRS, where to find Vulkan headers, Set when
#                       VULKAN_INCLUDE_DIR is found.
#  VULKAN_LIBRARIES, libraries to link against to use Vulkan.
#  VULKAN_ROOT_DIR, The base directory to search for Vulkan.
#                    This can also be an environment variable.
#  VULKAN_FOUND, If false, do not try to use Vulkan.
#

# If VULKAN_ROOT_DIR was defined in the environment, use it.
IF(NOT VULKAN_ROOT_DIR AND NOT $ENV{VULKAN_ROOT_DIR} STREQUAL "")
  SET(VULKAN_ROOT_DIR $ENV{VULKAN_ROOT_DIR})
ENDIF()

SET(_vulkan_SEARCH_DIRS
  ${VULKAN_ROOT_DIR}
)

# FIXME: These finder modules typically don't use LIBDIR,
# this should be set by `./build_files/cmake/platform/` instead.
IF(DEFINED LIBDIR)
  SET(_vulkan_SEARCH_DIRS ${_vulkan_SEARCH_DIRS} ${LIBDIR}/vulkan)
ENDIF()

FIND_PATH(VULKAN_INCLUDE_DIR
  NAMES
    vulkan/vulkan.h
  HINTS
    ${_vulkan_SEARCH_DIRS}
  PATH_SUFFIXES
    include
)

FIND_LIBRARY(VULKAN_LIBRARY
  NAMES
    vulkan
  HINTS
    ${_vulkan_SEARCH_DIRS}
  PATH_SUFFIXES
    lib
)

# handle the QUIETLY and REQUIRED arguments and set VULKAN_FOUND to TRUE if
# all listed variables are TRUE
INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(Vulkan DEFAULT_MSG VULKAN_LIBRARY VULKAN_INCLUDE_DIR)

IF(VULKAN_FOUND)
  SET(VULKAN_LIBRARIES ${VULKAN_LIBRARY})
  SET(VULKAN_INCLUDE_DIRS ${VULKAN_INCLUDE_DIR})
ENDIF()

MARK_AS_ADVANCED(
  VULKAN_INCLUDE_DIR
  VULKAN_LIBRARY
)

UNSET(_vulkan_SEARCH_DIRS)
