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

set(CLANG_EXTRA_ARGS
	-DCLANG_PATH_TO_LLVM_SOURCE=${BUILD_DIR}/ll/src/ll
	-DCLANG_PATH_TO_LLVM_BUILD=${LIBDIR}/llvm
	-DLLVM_USE_CRT_RELEASE=MT
	-DLLVM_USE_CRT_DEBUG=MTd
)
ExternalProject_Add(external_clang
	URL ${CLANG_URI}
	DOWNLOAD_DIR ${DOWNLOAD_DIR}
	URL_HASH MD5=${CLANG_HASH}
	PATCH_COMMAND ${PATCH_CMD} -p 2 -N -R -d ${BUILD_DIR}/clang/src/external_clang < ${PATCH_DIR}/clang.diff
	PREFIX ${BUILD_DIR}/clang
	CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${LIBDIR}/llvm ${DEFAULT_CMAKE_FLAGS} ${CLANG_EXTRA_ARGS}
	INSTALL_DIR ${LIBDIR}/llvm
)

add_dependencies(external_clang ll)
