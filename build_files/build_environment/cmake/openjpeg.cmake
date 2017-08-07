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
# ***** END GPL LICENSE BLOCK *****

# Note the encoder/decoder may use png/tiff/lcms system libraries, but the
# library itself does not depend on them, so should give no problems.

set(OPENJPEG_EXTRA_ARGS -DBUILD_SHARED_LIBS=OFF)

if(WIN32)
	set(OPENJPEG_EXTRA_ARGS -G "MSYS Makefiles")
else()
	set(OPENJPEG_EXTRA_ARGS ${DEFAULT_CMAKE_FLAGS})
endif()

ExternalProject_Add(external_openjpeg
	URL ${OPENJPEG_URI}
	DOWNLOAD_DIR ${DOWNLOAD_DIR}
	URL_HASH SHA256=${OPENJPEG_HASH}
	PREFIX ${BUILD_DIR}/openjpeg
	CONFIGURE_COMMAND ${CONFIGURE_ENV} && cd ${BUILD_DIR}/openjpeg/src/external_openjpeg-build && ${CMAKE_COMMAND} ${OPENJPEG_EXTRA_ARGS} -DCMAKE_INSTALL_PREFIX=${LIBDIR}/openjpeg -DBUILD_SHARED_LIBS=Off -DBUILD_THIRDPARTY=OFF ${BUILD_DIR}/openjpeg/src/external_openjpeg
	BUILD_COMMAND ${CONFIGURE_ENV} && cd ${BUILD_DIR}/openjpeg/src/external_openjpeg-build/ && make -j${MAKE_THREADS}
	INSTALL_COMMAND ${CONFIGURE_ENV} && cd ${BUILD_DIR}/openjpeg/src/external_openjpeg-build/ && make install
	INSTALL_DIR ${LIBDIR}/openjpeg
)

if(MSVC)
	set_target_properties(external_openjpeg PROPERTIES FOLDER Mingw)
endif(MSVC)
