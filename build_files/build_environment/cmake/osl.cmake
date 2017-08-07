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

if(WIN32)
	set(OSL_CMAKE_CXX_STANDARD_LIBRARIES "kernel32${LIBEXT} user32${LIBEXT} gdi32${LIBEXT} winspool${LIBEXT} shell32${LIBEXT} ole32${LIBEXT} oleaut32${LIBEXT} uuid${LIBEXT} comdlg32${LIBEXT} advapi32${LIBEXT} psapi${LIBEXT}")
	set(OSL_FLEX_BISON -DFLEX_EXECUTABLE=${LIBDIR}/flexbison/win_flex.exe -DFLEX_EXTRA_OPTIONS="--wincompat" -DBISON_EXECUTABLE=${LIBDIR}/flexbison/win_bison.exe)
	set(OSL_OPENIMAGEIO_LIBRARY "${LIBDIR}/openimageio/lib/${LIBPREFIX}OpenImageIO${LIBEXT};${LIBDIR}/openimageio/lib/${LIBPREFIX}OpenImageIO_Util${LIBEXT};${LIBDIR}/png/lib/libpng16${LIBEXT};${LIBDIR}/jpg/lib/${LIBPREFIX}jpeg${LIBEXT};${LIBDIR}/tiff/lib/${LIBPREFIX}tiff${LIBEXT};${LIBDIR}/openexr/lib/${LIBPREFIX}IlmImf-2_2${LIBEXT}")
	if("${CMAKE_SIZEOF_VOID_P}" EQUAL "4")
		set(OSL_SIMD_FLAGS -DOIIO_SIMD=0)
	else()
		set(OSL_SIMD_FLAGS -DOIIO_SIMD=sse2)
	endif()
else()
	set(OSL_CMAKE_CXX_STANDARD_LIBRARIES)
	set(OSL_FLEX_BISON)
	set(OSL_OPENIMAGEIO_LIBRARY "${LIBDIR}/openimageio/lib/${LIBPREFIX}OpenImageIO${LIBEXT};${LIBDIR}/openimageio/lib/${LIBPREFIX}OpenImageIO_Util${LIBEXT};${LIBDIR}/png/lib/${LIBPREFIX}png16${LIBEXT};${LIBDIR}/jpg/lib/${LIBPREFIX}jpeg${LIBEXT};${LIBDIR}/tiff/lib/${LIBPREFIX}tiff${LIBEXT};${LIBDIR}/openexr/lib/${LIBPREFIX}IlmImf-2_2${LIBEXT}")
endif()

set(OSL_ILMBASE_CUSTOM_LIBRARIES "${LIBDIR}/ilmbase/lib/Imath-2_2.lib^^${LIBDIR}/ilmbase/lib/Half.lib^^${LIBDIR}/ilmbase/lib/IlmThread-2_2.lib^^${LIBDIR}/ilmbase/lib/Iex-2_2.lib")
set(OSL_LLVM_LIBRARY "${LIBDIR}/llvm/lib/LLVMAnalysis${LIBEXT};${LIBDIR}/llvm/lib/LLVMAsmParser${LIBEXT};${LIBDIR}/llvm/lib/LLVMAsmPrinter${LIBEXT};${LIBDIR}/llvm/lib/LLVMBitReader${LIBEXT};${LIBDIR}/llvm/lib/LLVMBitWriter${LIBEXT};${LIBDIR}/llvm/lib/LLVMCodeGen${LIBEXT};${LIBDIR}/llvm/lib/LLVMCore${LIBEXT};${LIBDIR}/llvm/lib/LLVMDebugInfo${LIBEXT};${LIBDIR}/llvm/lib/LLVMExecutionEngine${LIBEXT};${LIBDIR}/llvm/lib/LLVMInstCombine${LIBEXT};${LIBDIR}/llvm/lib/LLVMInstrumentation${LIBEXT};${LIBDIR}/llvm/lib/LLVMInterpreter${LIBEXT};${LIBDIR}/llvm/lib/LLVMJIT${LIBEXT};${LIBDIR}/llvm/lib/LLVMLinker${LIBEXT};${LIBDIR}/llvm/lib/LLVMMC${LIBEXT};${LIBDIR}/llvm/lib/LLVMMCDisassembler${LIBEXT};${LIBDIR}/llvm/lib/LLVMMCJIT${LIBEXT};${LIBDIR}/llvm/lib/LLVMMCParser${LIBEXT};${LIBDIR}/llvm/lib/LLVMObject${LIBEXT};${LIBDIR}/llvm/lib/LLVMRuntimeDyld${LIBEXT};${LIBDIR}/llvm/lib/LLVMScalarOpts${LIBEXT};${LIBDIR}/llvm/lib/LLVMSelectionDAG${LIBEXT};${LIBDIR}/llvm/lib/LLVMSupport${LIBEXT};${LIBDIR}/llvm/lib/LLVMTableGen${LIBEXT};${LIBDIR}/llvm/lib/LLVMTarget${LIBEXT};${LIBDIR}/llvm/lib/LLVMTransformUtils${LIBEXT};${LIBDIR}/llvm/lib/LLVMVectorize${LIBEXT};${LIBDIR}/llvm/lib/LLVMX86AsmParser${LIBEXT};${LIBDIR}/llvm/lib/LLVMX86AsmPrinter${LIBEXT};${LIBDIR}/llvm/lib/LLVMX86CodeGen${LIBEXT};${LIBDIR}/llvm/lib/LLVMX86Desc${LIBEXT};${LIBDIR}/llvm/lib/LLVMX86Disassembler${LIBEXT};${LIBDIR}/llvm/lib/LLVMX86Info${LIBEXT};${LIBDIR}/llvm/lib/LLVMX86Utils${LIBEXT};${LIBDIR}/llvm/lib/LLVMipa${LIBEXT};${LIBDIR}/llvm/lib/LLVMipo${LIBEXT}")

set(OSL_EXTRA_ARGS
	-DBoost_COMPILER:STRING=${BOOST_COMPILER_STRING}
	-DBoost_USE_MULTITHREADED=ON
	-DBoost_USE_STATIC_LIBS=ON
	-DBoost_USE_STATIC_RUNTIME=ON
	-DBOOST_ROOT=${LIBDIR}/boost
	-DBOOST_LIBRARYDIR=${LIBDIR}/boost/lib/
	-DBoost_NO_SYSTEM_PATHS=ON
	-DLLVM_DIRECTORY=${LIBDIR}/llvm
	-DLLVM_INCLUDES=${LIBDIR}/llvm/include
	-DLLVM_LIB_DIR=${LIBDIR}/llvm/lib
	-DLLVM_VERSION=3.4
	-DLLVM_LIBRARY=${OSL_LLVM_LIBRARY}
	-DOPENEXR_HOME=${LIBDIR}/openexr/
	-DILMBASE_HOME=${LIBDIR}/ilmbase/
	-DILMBASE_INCLUDE_DIR=${LIBDIR}/ilmbase/include/
	-DOPENEXR_IMATH_LIBRARY=${LIBDIR}/ilmbase/lib/${LIBPREFIX}Imath-2_2${LIBEXT}
	-DOPENEXR_ILMTHREAD_LIBRARY=${LIBDIR}/ilmbase/lib/${LIBPREFIX}IlmThread-2_2${LIBEXT}
	-DOPENEXR_IEX_LIBRARY=${LIBDIR}/ilmbase/lib/${LIBPREFIX}Iex-2_2${LIBEXT}
	-DOPENEXR_INCLUDE_DIR=${LIBDIR}/openexr/include/
	-DOPENEXR_ILMIMF_LIBRARY=${LIBDIR}/openexr/lib/${LIBPREFIX}IlmImf-2_2${LIBEXT}
	-DOSL_BUILD_TESTS=OFF
	-DZLIB_LIBRARY=${LIBDIR}/zlib/lib/${ZLIB_LIBRARY}
	-DZLIB_INCLUDE_DIR=${LIBDIR}/zlib/include/
	-DOPENIMAGEIOHOME=${LIBDIR}/openimageio/
	-DOPENIMAGEIO_LIBRARY=${OSL_OPENIMAGEIO_LIBRARY}
	-DOPENIMAGEIO_INCLUDES=${LIBDIR}/openimageio/include
	${OSL_FLEX_BISON}
	-DCMAKE_CXX_STANDARD_LIBRARIES=${OSL_CMAKE_CXX_STANDARD_LIBRARIES}
	-DBUILDSTATIC=ON
	-DLINKSTATIC=ON
	-DOSL_BUILD_PLUGINS=Off
	-DSTOP_ON_WARNING=OFF
	-DOSL_BUILD_CPP11=ON
	-DUSE_LLVM_BITCODE=OFF
	${OSL_SIMD_FLAGS}
)

ExternalProject_Add(external_osl
	URL ${OSL_URI}
	DOWNLOAD_DIR ${DOWNLOAD_DIR}
	LIST_SEPARATOR ^^
	URL_HASH MD5=${OSL_HASH}
	PREFIX ${BUILD_DIR}/osl
	PATCH_COMMAND ${PATCH_CMD} -p 3 -d ${BUILD_DIR}/osl/src/external_osl < ${PATCH_DIR}/osl.diff &&
				${PATCH_CMD} -p 0 -d ${BUILD_DIR}/osl/src/external_osl < ${PATCH_DIR}/osl_simd_oiio.diff
	CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${LIBDIR}/osl -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} ${DEFAULT_CMAKE_FLAGS} ${OSL_EXTRA_ARGS}
	INSTALL_DIR ${LIBDIR}/osl
)

add_dependencies(external_osl external_boost ll external_clang external_ilmbase external_openexr external_zlib external_flexbison external_openimageio)
