# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# The Original Code is Copyright (C) 2016, Blender Foundation
# All rights reserved.
# ***** END GPL LICENSE BLOCK *****

# Libraries configuration for Apple.

if("${CMAKE_OSX_ARCHITECTURES}" STREQUAL "arm64")
  set(MACOSX_DEPLOYMENT_TARGET 11.00)
else()
  set(MACOSX_DEPLOYMENT_TARGET 10.13)
endif()

macro(find_package_wrapper)
# do nothing, just satisfy the macro
endmacro()

function(print_found_status
  lib_name
  lib_path
  )

  if(FIRST_RUN)
    if(lib_path)
      message(STATUS "Found ${lib_name}: ${lib_path}")
    else()
      message(WARNING "Could NOT find ${lib_name}")
    endif()
  endif()
endfunction()

# ------------------------------------------------------------------------
# Find system provided libraries.

# Find system ZLIB, not the pre-compiled one supplied with OpenCollada.
set(ZLIB_ROOT /usr)
find_package(ZLIB REQUIRED)
find_package(BZip2 REQUIRED)
list(APPEND ZLIB_LIBRARIES ${BZIP2_LIBRARIES})

if(WITH_OPENAL)
  find_package(OpenAL)
  if(NOT OPENAL_FOUND)
    set(WITH_OPENAL OFF)
  endif()
endif()

if(NOT DEFINED LIBDIR)
  set(LIBDIR ${CMAKE_SOURCE_DIR}/../lib/darwin)
  # Prefer lib directory paths
  file(GLOB LIB_SUBDIRS ${LIBDIR}/*)
  set(CMAKE_PREFIX_PATH ${LIB_SUBDIRS})
else()
  message(STATUS "Using pre-compiled LIBDIR: ${LIBDIR}")
endif()
if(NOT EXISTS "${LIBDIR}/")
  message(FATAL_ERROR "Mac OSX requires pre-compiled libs at: '${LIBDIR}'")
endif()

# -------------------------------------------------------------------------
# Find precompiled libraries, and avoid system or user-installed ones.

if(EXISTS ${LIBDIR})
  without_system_libs_begin()
endif()

if(WITH_ALEMBIC)
  find_package(Alembic)
endif()

if(WITH_USD)
  find_package(USD)
  if(NOT USD_FOUND)
    set(WITH_USD OFF)
  endif()
endif()

if(WITH_OPENSUBDIV)
  find_package(OpenSubdiv)
endif()

if(WITH_JACK)
  find_library(JACK_FRAMEWORK
    NAMES jackmp
  )
  if(NOT JACK_FRAMEWORK)
    set(WITH_JACK OFF)
  else()
    set(JACK_INCLUDE_DIRS ${JACK_FRAMEWORK}/headers)
  endif()
endif()

if(WITH_CODEC_SNDFILE)
  find_package(SndFile)
  find_library(_sndfile_FLAC_LIBRARY NAMES flac HINTS ${LIBDIR}/sndfile/lib)
  find_library(_sndfile_OGG_LIBRARY NAMES ogg HINTS ${LIBDIR}/ffmpeg/lib)
  find_library(_sndfile_VORBIS_LIBRARY NAMES vorbis HINTS ${LIBDIR}/ffmpeg/lib)
  find_library(_sndfile_VORBISENC_LIBRARY NAMES vorbisenc HINTS ${LIBDIR}/ffmpeg/lib)
  list(APPEND LIBSNDFILE_LIBRARIES
    ${_sndfile_FLAC_LIBRARY}
    ${_sndfile_OGG_LIBRARY}
    ${_sndfile_VORBIS_LIBRARY}
    ${_sndfile_VORBISENC_LIBRARY}
  )

  print_found_status("SndFile libraries" "${LIBSNDFILE_LIBRARIES}")
  unset(_sndfile_FLAC_LIBRARY)
  unset(_sndfile_OGG_LIBRARY)
  unset(_sndfile_VORBIS_LIBRARY)
  unset(_sndfile_VORBISENC_LIBRARY)
endif()

if(WITH_PYTHON)
  # we use precompiled libraries for py 3.7 and up by default
  set(PYTHON_VERSION 3.7)
  if(NOT WITH_PYTHON_MODULE AND NOT WITH_PYTHON_FRAMEWORK)
    # normally cached but not since we include them with blender
    set(PYTHON_INCLUDE_DIR "${LIBDIR}/python/include/python${PYTHON_VERSION}m")
    set(PYTHON_EXECUTABLE "${LIBDIR}/python/bin/python${PYTHON_VERSION}m")
    set(PYTHON_LIBRARY ${LIBDIR}/python/lib/libpython${PYTHON_VERSION}m.a)
    set(PYTHON_LIBPATH "${LIBDIR}/python/lib/python${PYTHON_VERSION}")
    # set(PYTHON_LINKFLAGS "-u _PyMac_Error")  # won't  build with this enabled
  else()
    # module must be compiled against Python framework
    set(_py_framework "/Library/Frameworks/Python.framework/Versions/${PYTHON_VERSION}")

    set(PYTHON_INCLUDE_DIR "${_py_framework}/include/python${PYTHON_VERSION}m")
    set(PYTHON_EXECUTABLE "${_py_framework}/bin/python${PYTHON_VERSION}m")
    set(PYTHON_LIBPATH "${_py_framework}/lib/python${PYTHON_VERSION}/config-${PYTHON_VERSION}m")
    # set(PYTHON_LIBRARY python${PYTHON_VERSION})
    # set(PYTHON_LINKFLAGS "-u _PyMac_Error -framework Python")  # won't  build with this enabled

    unset(_py_framework)
  endif()

  # uncached vars
  set(PYTHON_INCLUDE_DIRS "${PYTHON_INCLUDE_DIR}")
  set(PYTHON_LIBRARIES  "${PYTHON_LIBRARY}")

  # needed for Audaspace, numpy is installed into python site-packages
  set(PYTHON_NUMPY_INCLUDE_DIRS "${PYTHON_LIBPATH}/site-packages/numpy/core/include")

  if(NOT EXISTS "${PYTHON_EXECUTABLE}")
    message(FATAL_ERROR "Python executable missing: ${PYTHON_EXECUTABLE}")
  endif()
endif()

if(WITH_FFTW3)
  find_package(Fftw3)
endif()

find_package(Freetype REQUIRED)

if(WITH_IMAGE_OPENEXR)
  find_package(OpenEXR)
endif()

if(WITH_CODEC_FFMPEG)
  set(FFMPEG_FIND_COMPONENTS
    avcodec avdevice avformat avutil
    mp3lame ogg opus swresample swscale
    theora theoradec theoraenc vorbis vorbisenc
    vorbisfile vpx x264 xvidcore)
  find_package(FFmpeg)
endif()

if(WITH_IMAGE_OPENJPEG OR WITH_CODEC_FFMPEG)
  # use openjpeg from libdir that is linked into ffmpeg
  find_package(OpenJPEG)
endif()

find_library(SYSTEMSTUBS_LIBRARY
  NAMES
  SystemStubs
  PATHS
)
mark_as_advanced(SYSTEMSTUBS_LIBRARY)
if(SYSTEMSTUBS_LIBRARY)
  list(APPEND PLATFORM_LINKLIBS SystemStubs)
endif()

set(PLATFORM_CFLAGS "${PLATFORM_CFLAGS} -pipe -funsigned-char")
set(PLATFORM_LINKFLAGS
  "-fexceptions -framework CoreServices -framework Foundation -framework IOKit -framework AppKit -framework Cocoa -framework Carbon -framework AudioUnit -framework AudioToolbox -framework CoreAudio -framework Metal -framework QuartzCore"
)

list(APPEND PLATFORM_LINKLIBS c++)

if(WITH_JACK)
  set(PLATFORM_LINKFLAGS "${PLATFORM_LINKFLAGS} -F/Library/Frameworks -weak_framework jackmp")
endif()

if(WITH_PYTHON_MODULE OR WITH_PYTHON_FRAMEWORK)
  # force cmake to link right framework
  set(PLATFORM_LINKFLAGS "${PLATFORM_LINKFLAGS} /Library/Frameworks/Python.framework/Versions/${PYTHON_VERSION}/Python")
endif()

if(WITH_OPENCOLLADA)
  find_package(OpenCOLLADA)
  find_library(PCRE_LIBRARIES NAMES pcre HINTS ${LIBDIR}/opencollada/lib)
  find_library(XML2_LIBRARIES NAMES xml2 HINTS ${LIBDIR}/opencollada/lib)
  print_found_status("PCRE" "${PCRE_LIBRARIES}")
  print_found_status("XML2" "${XML2_LIBRARIES}")
endif()

if(WITH_SDL)
  find_package(SDL2)
  set(SDL_INCLUDE_DIR ${SDL2_INCLUDE_DIRS})
  set(SDL_LIBRARY ${SDL2_LIBRARIES})
  set(PLATFORM_LINKFLAGS "${PLATFORM_LINKFLAGS} -framework ForceFeedback")
endif()

set(PNG_ROOT ${LIBDIR}/png)
find_package(PNG REQUIRED)

set(JPEG_ROOT ${LIBDIR}/jpeg)
find_package(JPEG REQUIRED)

if(WITH_IMAGE_TIFF)
  set(TIFF_ROOT ${LIBDIR}/tiff)
  find_package(TIFF)
  if(NOT TIFF_FOUND)
    message(WARNING "TIFF not found, disabling WITH_IMAGE_TIFF")
    set(WITH_IMAGE_TIFF OFF)
  endif()
endif()

if(WITH_BOOST)
  set(Boost_NO_BOOST_CMAKE ON)
  set(BOOST_ROOT ${LIBDIR}/boost)
  set(Boost_NO_SYSTEM_PATHS ON)
  set(_boost_FIND_COMPONENTS date_time filesystem regex system thread wave)
  if(WITH_INTERNATIONAL)
    list(APPEND _boost_FIND_COMPONENTS locale)
  endif()
  if(WITH_CYCLES_NETWORK)
    list(APPEND _boost_FIND_COMPONENTS serialization)
  endif()
  if(WITH_OPENVDB)
    list(APPEND _boost_FIND_COMPONENTS iostreams)
  endif()
  find_package(Boost COMPONENTS ${_boost_FIND_COMPONENTS})

  set(BOOST_LIBRARIES ${Boost_LIBRARIES})
  set(BOOST_INCLUDE_DIR ${Boost_INCLUDE_DIRS})
  set(BOOST_DEFINITIONS)

  mark_as_advanced(Boost_LIBRARIES)
  mark_as_advanced(Boost_INCLUDE_DIRS)
  unset(_boost_FIND_COMPONENTS)
endif()

if(WITH_INTERNATIONAL OR WITH_CODEC_FFMPEG)
  set(PLATFORM_LINKFLAGS "${PLATFORM_LINKFLAGS} -liconv") # boost_locale and ffmpeg needs it !
endif()

if(WITH_OPENIMAGEIO)
  find_package(OpenImageIO)
  list(APPEND OPENIMAGEIO_LIBRARIES
    ${PNG_LIBRARIES}
    ${JPEG_LIBRARIES}
    ${TIFF_LIBRARY}
    ${OPENEXR_LIBRARIES}
    ${OPENJPEG_LIBRARIES}
    ${ZLIB_LIBRARIES}
  )
  set(OPENIMAGEIO_DEFINITIONS "-DOIIO_STATIC_BUILD")
  set(OPENIMAGEIO_IDIFF "${LIBDIR}/openimageio/bin/idiff")
endif()

if(WITH_OPENCOLORIO)
  find_package(OpenColorIO)
endif()

if(WITH_OPENVDB)
  find_package(OpenVDB)
  find_library(BLOSC_LIBRARIES NAMES blosc HINTS ${LIBDIR}/openvdb/lib)
  print_found_status("Blosc" "${BLOSC_LIBRARIES}")
  list(APPEND OPENVDB_LIBRARIES ${BLOSC_LIBRARIES})
  set(OPENVDB_DEFINITIONS)
endif()

if(WITH_NANOVDB)
  set(NANOVDB ${LIBDIR}/nanovdb)
  set(NANOVDB_INCLUDE_DIR ${NANOVDB}/include)
endif()

if(WITH_LLVM)
  find_package(LLVM)
  if(NOT LLVM_FOUND)
    message(FATAL_ERROR "LLVM not found.")
  endif()
endif()

if(WITH_CYCLES_OSL)
  set(CYCLES_OSL ${LIBDIR}/osl)

  find_library(OSL_LIB_EXEC NAMES oslexec PATHS ${CYCLES_OSL}/lib)
  find_library(OSL_LIB_COMP NAMES oslcomp PATHS ${CYCLES_OSL}/lib)
  find_library(OSL_LIB_QUERY NAMES oslquery PATHS ${CYCLES_OSL}/lib)
  # WARNING! depends on correct order of OSL libs linking
  list(APPEND OSL_LIBRARIES ${OSL_LIB_COMP} -force_load ${OSL_LIB_EXEC} ${OSL_LIB_QUERY})
  find_path(OSL_INCLUDE_DIR OSL/oslclosure.h PATHS ${CYCLES_OSL}/include)
  find_program(OSL_COMPILER NAMES oslc PATHS ${CYCLES_OSL}/bin)
  find_path(OSL_SHADER_DIR NAMES stdosl.h PATHS ${CYCLES_OSL}/shaders)

  if(OSL_INCLUDE_DIR AND OSL_LIBRARIES AND OSL_COMPILER AND OSL_SHADER_DIR)
    set(OSL_FOUND TRUE)
  else()
    message(STATUS "OSL not found")
    set(WITH_CYCLES_OSL OFF)
  endif()
endif()

if("${CMAKE_OSX_ARCHITECTURES}" STREQUAL "arm64")
  set(WITH_CYCLES_EMBREE OFF)
  set(WITH_OPENIMAGEDENOISE OFF)
  set(WITH_CPU_SSE OFF)
endif()

if(WITH_CYCLES_EMBREE)
  find_package(Embree 3.8.0 REQUIRED)
  # Increase stack size for Embree, only works for executables.
  if(NOT WITH_PYTHON_MODULE)
    set(PLATFORM_LINKFLAGS "${PLATFORM_LINKFLAGS} -Xlinker -stack_size -Xlinker 0x100000")
  endif()

  # Embree static library linking can mix up SSE and AVX symbols, causing
  # crashes on macOS systems with older CPUs that don't have AVX. Using
  # force load avoids that. The Embree shared library does not suffer from
  # this problem, precisely because linking a shared library uses force load.
  set(_embree_libraries_force_load)
  foreach(_embree_library ${EMBREE_LIBRARIES})
    list(APPEND _embree_libraries_force_load "-Wl,-force_load,${_embree_library}")
  endforeach()
  set(EMBREE_LIBRARIES ${_embree_libraries_force_load})
endif()

if(WITH_OPENIMAGEDENOISE)
  find_package(OpenImageDenoise)

  if(NOT OPENIMAGEDENOISE_FOUND)
    set(WITH_OPENIMAGEDENOISE OFF)
    message(STATUS "OpenImageDenoise not found")
  endif()
endif()

if(WITH_TBB)
  find_package(TBB)
endif()

if(WITH_POTRACE)
  find_package(Potrace)
  if(NOT POTRACE_FOUND)
    message(WARNING "potrace not found, disabling WITH_POTRACE")
    set(WITH_POTRACE OFF)
  endif()
endif()

# CMake FindOpenMP doesn't know about AppleClang before 3.12, so provide custom flags.
if(WITH_OPENMP)
  if(CMAKE_C_COMPILER_ID MATCHES "Clang" AND CMAKE_C_COMPILER_VERSION VERSION_GREATER_EQUAL "7.0")
    # Use OpenMP from our precompiled libraries.
    message(STATUS "Using ${LIBDIR}/openmp for OpenMP")
    set(OPENMP_CUSTOM ON)
    set(OPENMP_FOUND ON)
    set(OpenMP_C_FLAGS "-Xclang -fopenmp -I'${LIBDIR}/openmp/include'")
    set(OpenMP_CXX_FLAGS "-Xclang -fopenmp -I'${LIBDIR}/openmp/include'")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -L'${LIBDIR}/openmp/lib' -lomp")

    # Copy libomp.dylib to allow executables like datatoc and tests to work.
    # `@executable_path/../Resources/lib/` is a default dylib search path.
    # For single config generator datatoc, tests etc.
    execute_process(
      COMMAND mkdir -p ${CMAKE_BINARY_DIR}/Resources/lib
      COMMAND cp -p ${LIBDIR}/openmp/lib/libomp.dylib ${CMAKE_BINARY_DIR}/Resources/lib/libomp.dylib
    )
    # For multi-config generator datatoc, etc.
    execute_process(
      COMMAND mkdir -p ${CMAKE_BINARY_DIR}/bin/Resources/lib
      COMMAND cp -p ${LIBDIR}/openmp/lib/libomp.dylib ${CMAKE_BINARY_DIR}/bin/Resources/lib/libomp.dylib
    )
    # For multi-config generator tests.
    execute_process(
      COMMAND mkdir -p ${CMAKE_BINARY_DIR}/bin/tests/Resources/lib
      COMMAND cp -p ${LIBDIR}/openmp/lib/libomp.dylib ${CMAKE_BINARY_DIR}/bin/tests/Resources/lib/libomp.dylib
    )
  endif()
endif()

if(WITH_XR_OPENXR)
  find_package(XR_OpenXR_SDK)
  if(NOT XR_OPENXR_SDK_FOUND)
    message(WARNING "OpenXR-SDK was not found, disabling WITH_XR_OPENXR")
    set(WITH_XR_OPENXR OFF)
  endif()
endif()

if(WITH_GMP)
  find_package(GMP)
  if(NOT GMP_FOUND)
    message(WARNING "GMP not found, disabling WITH_GMP")
    set(WITH_GMP OFF)
  endif()
endif()

if(EXISTS ${LIBDIR})
  without_system_libs_end()
endif()

# ---------------------------------------------------------------------
# Set compiler and linker flags.

set(EXETYPE MACOSX_BUNDLE)

set(CMAKE_C_FLAGS_DEBUG "-fno-strict-aliasing -g")
set(CMAKE_CXX_FLAGS_DEBUG "-fno-strict-aliasing -g")
if(CMAKE_OSX_ARCHITECTURES MATCHES "x86_64" OR CMAKE_OSX_ARCHITECTURES MATCHES "i386")
  set(CMAKE_CXX_FLAGS_RELEASE "-O2 -mdynamic-no-pic -msse -msse2 -msse3 -mssse3")
  set(CMAKE_C_FLAGS_RELEASE "-O2 -mdynamic-no-pic  -msse -msse2 -msse3 -mssse3")
  if(NOT CMAKE_C_COMPILER_ID MATCHES "Clang")
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -ftree-vectorize  -fvariable-expansion-in-unroller")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -ftree-vectorize  -fvariable-expansion-in-unroller")
  endif()
else()
  set(CMAKE_C_FLAGS_RELEASE "-O2 -mdynamic-no-pic -fno-strict-aliasing")
  set(CMAKE_CXX_FLAGS_RELEASE "-O2 -mdynamic-no-pic -fno-strict-aliasing")
endif()

if(${XCODE_VERSION} VERSION_EQUAL 5 OR ${XCODE_VERSION} VERSION_GREATER 5)
  # Xcode 5 is always using CLANG, which has too low template depth of 128 for libmv
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -ftemplate-depth=1024")
endif()

# Avoid conflicts with Luxrender, and other plug-ins that may use the same
# libraries as Blender with a different version or build options.
set(PLATFORM_LINKFLAGS
  "${PLATFORM_LINKFLAGS} -Xlinker -unexported_symbols_list -Xlinker '${CMAKE_SOURCE_DIR}/source/creator/osx_locals.map'"
)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
set(PLATFORM_LINKFLAGS "${PLATFORM_LINKFLAGS} -stdlib=libc++")

# Suppress ranlib "has no symbols" warnings (workaround for T48250)
set(CMAKE_C_ARCHIVE_CREATE   "<CMAKE_AR> Scr <TARGET> <LINK_FLAGS> <OBJECTS>")
set(CMAKE_CXX_ARCHIVE_CREATE "<CMAKE_AR> Scr <TARGET> <LINK_FLAGS> <OBJECTS>")
set(CMAKE_C_ARCHIVE_FINISH   "<CMAKE_RANLIB> -no_warning_for_no_symbols -c <TARGET>")
set(CMAKE_CXX_ARCHIVE_FINISH "<CMAKE_RANLIB> -no_warning_for_no_symbols -c <TARGET>")
