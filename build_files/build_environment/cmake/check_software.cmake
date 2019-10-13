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

if(UNIX)
  if(APPLE)
    set(_libtoolize_name glibtoolize)
  else()
    set(_libtoolize_name libtoolize)
  endif()

  set(_required_software
    autoconf
    automake
    ${_libtoolize_name}
    nasm
    yasm
    tclsh
  )

  foreach(_software ${_required_software})
    find_program(_software_find NAMES ${_software})
    if(NOT _software_find)
      set(_software_missing "${_software_missing}${_software} ")
    endif()
    unset(_software_find CACHE)
  endforeach()

  if(_software_missing)
    message(
      "\n"
      "Missing software for building Blender dependencies:\n"
      "  ${_software_missing}\n"
      "\n"
      "On Debian and Ubuntu:\n"
      "  apt install autoconf automake libtool yasm nasm tcl\n"
      "\n"
      "On macOS (with homebrew):\n"
      "  brew install cmake autoconf automake libtool yasm nasm\n"
      "\n"
      "Other platforms:\n"
      "  Install equivalent packages.\n")
    message(FATAL_ERROR "Install missing software before continuing")
  endif()
endif()
