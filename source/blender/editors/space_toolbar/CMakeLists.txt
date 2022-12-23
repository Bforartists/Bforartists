# SPDX-License-Identifier: GPL-2.0-or-later
#
# Contributor(s): ?? Grabbed from the UI tutorial here: https://wiki.blender.org/index.php/Dev:Source/UI/Tutorials/AddAnEditor


set(INC
	../include
	../../blenkernel
	../../blenlib
	../../blenloader
	../../gpu
	../../makesdna
	../../makesrna
	../../windowmanager
	../../../../intern/guardedalloc

  # dna_type_offsets.h
  ${CMAKE_CURRENT_BINARY_DIR}/../../makesdna/intern
)
 
set(INC_SYS
	${GLEW_INCLUDE_PATH}
)
 
set(SRC
	space_toolbar.c
)
 
blender_add_lib(bf_editor_space_toolbar "${SRC}" "${INC}" "${INC_SYS}" "${LIB}")

# dna_type_offsets.h dna_type_offsets.h
add_dependencies(bf_editor_space_toolbar bf_dna)
