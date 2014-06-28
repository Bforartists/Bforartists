
###########################################################################
# GLUT

if(WITH_CYCLES_STANDALONE AND WITH_CYCLES_STANDALONE_GUI)
	set(GLUT_ROOT_PATH ${CYCLES_GLUT})

	find_package(GLUT)
	message(STATUS "GLUT_FOUND=${GLUT_FOUND}")

	include_directories(
		SYSTEM
		${GLUT_INCLUDE_DIR}
	)
endif()

if(WITH_SYSTEM_GLEW)
	set(CYCLES_GLEW_LIBRARY ${GLEW_LIBRARY})
else()
	set(CYCLES_GLEW_LIBRARY extern_glew)
endif()

###########################################################################
# CUDA

if(WITH_CYCLES_CUDA_BINARIES)
	find_package(CUDA) # Try to auto locate CUDA toolkit
	if(CUDA_FOUND)
		message(STATUS "CUDA nvcc = ${CUDA_NVCC_EXECUTABLE}")
	else()
		message(STATUS "CUDA compiler not found, disabling WITH_CYCLES_CUDA_BINARIES")
		set(WITH_CYCLES_CUDA_BINARIES OFF)
	endif()
endif()

