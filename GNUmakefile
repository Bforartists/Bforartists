# -*- mode: gnumakefile; tab-width: 8; indent-tabs-mode: t; -*-
# vim: tabstop=8
# $Id$
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# This Makefile does an out-of-source CMake build in ../build/`OS`_`CPU`
# eg:
#   ../build/Linux_i386
# This is for users who like to configure & build blender with a single command.


# System Vars
OS:=$(shell uname -s)
OS_NCASE:=$(shell uname -s | tr '[A-Z]' '[a-z]')
# CPU:=$(shell uname -m)  # UNUSED


# Source and Build DIR's
BLENDER_DIR:=$(shell pwd -P)
BUILD_DIR:=$(shell dirname $(BLENDER_DIR))/build/$(OS_NCASE)
BUILD_TYPE:=Release
BUILD_CMAKE_ARGS:=""


# -----------------------------------------------------------------------------
# additional targets for the build configuration

# support 'make debug'
ifneq "$(findstring debug, $(MAKECMDGOALS))" ""
	BUILD_DIR:=$(BUILD_DIR)_debug
	BUILD_TYPE:=Debug
endif
ifneq "$(findstring lite, $(MAKECMDGOALS))" ""
	BUILD_DIR:=$(BUILD_DIR)_lite
	BUILD_CMAKE_ARGS:=$(BUILD_CMAKE_ARGS) -C$(BLENDER_DIR)/build_files/cmake/config/blender_lite.cmake
endif
ifneq "$(findstring headless, $(MAKECMDGOALS))" ""
	BUILD_DIR:=$(BUILD_DIR)_bpy
	BUILD_CMAKE_ARGS:=$(BUILD_CMAKE_ARGS) -C$(BLENDER_DIR)/build_files/cmake/config/blender_headless.cmake
endif
ifneq "$(findstring bpy, $(MAKECMDGOALS))" ""
	BUILD_DIR:=$(BUILD_DIR)_bpy
	BUILD_CMAKE_ARGS:=$(BUILD_CMAKE_ARGS) -C$(BLENDER_DIR)/build_files/cmake/config/bpy_module.cmake
endif


# -----------------------------------------------------------------------------
# Get the number of cores for threaded build
NPROCS:=1
ifeq ($(OS), Linux)
	NPROCS:=$(shell grep -c ^processor /proc/cpuinfo)
endif
ifeq ($(OS), Darwin)
	NPROCS:=$(shell sysctl -a | grep "hw.ncpu " | cut -d" " -f3)
endif
ifeq ($(OS), FreeBSD)
	NPROCS:=$(shell sysctl -a | grep "hw.ncpu " | cut -d" " -f3 )
endif
ifeq ($(OS), NetBSD)
	NPROCS:=$(shell sysctl -a | grep "hw.ncpu " | cut -d" " -f3 )
endif

# -----------------------------------------------------------------------------
# Build Blender
all:
	@echo
	@echo Configuring Blender ...

	if test ! -f $(BUILD_DIR)/CMakeCache.txt ; then \
		cmake $(BUILD_CMAKE_ARGS) -H$(BLENDER_DIR) -B$(BUILD_DIR) -DCMAKE_BUILD_TYPE:STRING=$(BUILD_TYPE); \
	fi

	@echo
	@echo Building Blender ...
	$(MAKE) -C $(BUILD_DIR) -s -j $(NPROCS) install
	@echo
	@echo edit build configuration with: "$(BUILD_DIR)/CMakeCache.txt" run make again to rebuild.
	@echo blender installed, run from: "$(BUILD_DIR)/bin/blender"
	@echo

debug: all
lite: all
headless: all
bpy: all

# -----------------------------------------------------------------------------
# Helo for build targets
help:
	@echo ""
	@echo "Convenience targets provided for building blender, (multiple at once can be used)"
	@echo "  * debug     - build a debug binary"
	@echo "  * lite      - disable non essential features for a smaller binary and faster build"
	@echo "  * headless  - build without an interface (renderfarm or server automation)"
	@echo "  * bpy       - build as a python module which can be loaded from python directly"
	@echo ""
	@echo "Project Files for IDE's"
	@echo "  * project_qtcreator - QtCreator Project Files"
	@echo "  * project_netbeans  - NetBeans Project Files"
	@echo "  * project_eclipse   - Eclipse CDT4 Project Files"
	@echo ""
	@echo "Package Targets"
	@echo "  * package_debian  - build a debian package"
	@echo "  * package_pacman  - build an arch linux pacmanpackage"
	@echo "  * package_archive - build an archive package"
	@echo ""
	@echo "Testing Targets (not assosiated with building blender)"
	@echo "  * test            - run ctest, currently tests import/export, operator execution and that python modules load"
	@echo "  * test_cmake      - runs our own cmake file checker which detects errors in the cmake file list definitions"
	@echo "  * test_pep8       - checks all python script are pep8 which are tagged to use the stricter formatting"
	@echo "  * test_deprecated - checks for deprecation tags in our code which may need to be removed"
	@echo ""
	@echo "Static Source Code Checking (not assosiated with building blender)"
	@echo "  * check_cppcheck  - run blender source through cppcheck (C & C++)"
	@echo "  * check_splint    - run blenders source through splint (C only)"
	@echo "  * check_sparse    - run blenders source through sparse (C only)"
	@echo ""

# -----------------------------------------------------------------------------
# Packages
#
package_debian:
	cd build_files/package_spec ; DEB_BUILD_OPTIONS="parallel=$(NPROCS)" sh ./build_debian.sh

package_pacman:
	cd build_files/package_spec/pacman ; MAKEFLAGS="-j$(NPROCS)" makepkg --asroot

package_archive:
	make -C $(BUILD_DIR) -s package_archive
	@echo archive in "$(BUILD_DIR)/release"


# -----------------------------------------------------------------------------
# Tests
#
test:
	cd $(BUILD_DIR) ; ctest . --output-on-failure

# run pep8 check check on scripts we distribute.
test_pep8:
	python3 source/tests/pep8.py > test_pep8.log 2>&1
	@echo "written: test_pep8.log"

# run some checks on our cmakefiles.
test_cmake:
	python3 build_files/cmake/cmake_consistency_check.py > test_cmake_consistency.log 2>&1
	@echo "written: test_cmake_consistency.log"

# run deprecation tests, see if we have anything to remove.
test_deprecated:
	python3 source/tests/check_deprecated.py


# -----------------------------------------------------------------------------
# Project Files
#

project_qtcreator:
	python3 build_files/cmake/cmake_qtcreator_project.py $(BUILD_DIR)

project_netbeans:
	python3 build_files/cmake/cmake_netbeans_project.py $(BUILD_DIR)

project_eclipse:
	cmake -G"Eclipse CDT4 - Unix Makefiles" -H$(BLENDER_DIR) -B$(BUILD_DIR)


# -----------------------------------------------------------------------------
# Static Checking
#

check_cppcheck:
	cd $(BUILD_DIR) ; python3 $(BLENDER_DIR)/build_files/cmake/cmake_static_check_cppcheck.py

check_splint:
	cd $(BUILD_DIR) ; python3 $(BLENDER_DIR)/build_files/cmake/cmake_static_check_splint.py

check_sparse:
	cd $(BUILD_DIR) ; python3 $(BLENDER_DIR)/build_files/cmake/cmake_static_check_sparse.py


clean:
	$(MAKE) -C $(BUILD_DIR) clean

.PHONY: all
