# SPDX-FileCopyrightText: 2011 Blender Authors
#
# SPDX-License-Identifier: BSD-3-Clause

# - Find Spacenav library
# Find the native Spacenav includes and library
# This module defines
#  SPACENAV_INCLUDE_DIRS, where to find spnav.h, Set when
#                        SPACENAV_INCLUDE_DIR is found.
#  SPACENAV_LIBRARIES, libraries to link against to use Spacenav.
#  SPACENAV_ROOT_DIR, The base directory to search for Spacenav.
#                    This can also be an environment variable.
#  SPACENAV_FOUND, If false, do not try to use Spacenav.
#
# also defined, but not for general use are
#  SPACENAV_LIBRARY, where to find the Spacenav library.

# If `SPACENAV_ROOT_DIR` was defined in the environment, use it.
if(DEFINED SPACENAV_ROOT_DIR)
  # Pass.
elseif(DEFINED ENV{SPACENAV_ROOT_DIR})
  set(SPACENAV_ROOT_DIR $ENV{SPACENAV_ROOT_DIR})
else()
  set(SPACENAV_ROOT_DIR "")
endif()

set(_spacenav_SEARCH_DIRS
  ${SPACENAV_ROOT_DIR}
)

find_path(SPACENAV_INCLUDE_DIR
  NAMES
    spnav.h
  HINTS
    ${_spacenav_SEARCH_DIRS}
  PATH_SUFFIXES
    include
)

find_library(SPACENAV_LIBRARY
  NAMES
    spnav
  HINTS
    ${_spacenav_SEARCH_DIRS}
  PATH_SUFFIXES
    lib64 lib
  )

# handle the QUIETLY and REQUIRED arguments and set SPACENAV_FOUND to TRUE if
# all listed variables are TRUE
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Spacenav DEFAULT_MSG
    SPACENAV_LIBRARY SPACENAV_INCLUDE_DIR)

if(SPACENAV_FOUND)
  set(SPACENAV_LIBRARIES ${SPACENAV_LIBRARY})
  set(SPACENAV_INCLUDE_DIRS ${SPACENAV_INCLUDE_DIR})
endif()

mark_as_advanced(
  SPACENAV_INCLUDE_DIR
  SPACENAV_LIBRARY
)
