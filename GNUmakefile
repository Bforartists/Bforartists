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
CPU:=$(shell uname -m)


# Source and Build DIR's
BLENDER_DIR:=$(shell pwd -P)
BUILD_DIR:=$(shell dirname $(BLENDER_DIR))/build/$(OS)_$(CPU)


# Get the number of cores for threaded build
NPROCS:=1
ifeq ($(OS), Linux)
	NPROCS:=$(shell grep -c ^processor /proc/cpuinfo)
endif
ifeq ($(OS), Darwin)
	NPROCS:=$(shell system_profiler | awk '/Number Of CPUs/{print $4}{next;}')
endif
ifeq ($(OS), FreeBSD)
	NPROCS:=$(shell sysctl -a | grep "hw.ncpu " | cut -d" " -f3 )
endif
ifeq ($(OS), NetBSD)
	NPROCS:=$(shell sysctl -a | grep "hw.ncpu " | cut -d" " -f3 )
endif


# Build Blender
all:
	@echo 
	@echo Configuring Blender ...

	if test ! -f $(BUILD_DIR)/CMakeCache.txt ; then \
		mkdir -p $(BUILD_DIR) ; \
		cd $(BUILD_DIR) ; \
		cmake $(BLENDER_DIR) -DCMAKE_BUILD_TYPE:STRING=Release ; \
	fi

	@echo 
	@echo Building Blender ...
	cd $(BUILD_DIR) ; make -s -j $(NPROCS)
	@echo 
	@echo run blender from "$(BUILD_DIR)/bin/blender"
	@echo 

.PHONY: all
