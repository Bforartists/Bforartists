#
# $Id$
#
# ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version. The Blender
# Foundation also sells licenses for use in proprietary software under
# the Blender License.  See http://www.blender.org/BL/ for information
# about this.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
# All rights reserved.
#
# The Original Code is: all of this file.
#
# Contributor(s): none yet.
#
# ***** END GPL/BL DUAL LICENSE BLOCK *****
#
# set some defaults when these are not overruled (?=) by environment variables
#

sinclude ../user-def.mk

ifndef CONFIG_GUESS
  ifeq (debug, $(findstring debug, $(MAKECMDGOALS)))
    ifeq (all, $(findstring all, $(MAKECMDGOALS)))
all debug::
      ERRTXT = "ERROR: all and debug targets cannot be used together anymore"
      ERRTXT += "Use something like ..make all && make debug.. instead"
      $(error $(ERRTXT))
    endif
  endif

  # First generic defaults for all platforms which should be constant.
  # Note: ?= lets these defaults be overruled by environment variables,
    export NAN_NO_KETSJI=true
    export NAN_JUST_BLENDERDYNAMIC=true
    export NAN_NO_OPENAL=true
    export SRCHOME ?= $(NANBLENDERHOME)/source
    export CONFIG_GUESS := $(shell ${SRCHOME}/tools/guess/guessconfig)
    export OS := $(shell echo ${CONFIG_GUESS} | sed -e 's/-.*//')
    export OS_VERSION := $(shell echo ${CONFIG_GUESS} | sed -e 's/^[^-]*-//' -e 's/-[^-]*//')
    export CPU := $(shell echo ${CONFIG_GUESS} | sed -e 's/^[^-]*-[^-]*-//')
    export MAKE_START := $(shell date "+%H:%M:%S %d-%b-%Y")
    export NAN_LIBDIR ?= $(NANBLENDERHOME)/../lib
    export NAN_OBJDIR ?= $(NANBLENDERHOME)/obj
    # Library Config_Guess DIRectory
    export LCGDIR = $(NAN_LIBDIR)/$(CONFIG_GUESS)
    # Object Config_Guess DIRectory
    export OCGDIR = $(NAN_OBJDIR)/$(CONFIG_GUESS)
    export NAN_MOTO ?= $(LCGDIR)/moto
ifeq ($(FREE_WINDOWS), true)
    export NAN_SOLID ?= $(LCGDIR)/gcc/solid
    export NAN_QHULL ?= $(LCGDIR)/gcc/qhull
else
    export NAN_SOLID ?= $(LCGDIR)/solid
    export NAN_QHULL ?= $(LCGDIR)/qhull
endif
    export NAN_BULLET ?= $(LCGDIR)/bullet
    export NAN_SUMO ?= $(SRCHOME)/gameengine/Physics/Sumo
    export NAN_FUZZICS ?= $(SRCHOME)/gameengine/Physics/Sumo/Fuzzics
    export NAN_BLENKEY ?= $(LCGDIR)/blenkey
    export NAN_DECIMATION ?= $(LCGDIR)/decimation
    export NAN_GUARDEDALLOC ?= $(LCGDIR)/guardedalloc
    export NAN_IKSOLVER ?= $(LCGDIR)/iksolver
    export NAN_BSP ?= $(LCGDIR)/bsp
	export NAN_BOOLOP ?= $(LCGDIR)/boolop
    export NAN_SOUNDSYSTEM ?= $(LCGDIR)/SoundSystem
    export NAN_STRING ?= $(LCGDIR)/string
    export NAN_MEMUTIL ?= $(LCGDIR)/memutil
    export NAN_CONTAINER ?= $(LCGDIR)/container
    export NAN_ACTION ?= $(LCGDIR)/action
    export NAN_IMG ?= $(LCGDIR)/img
    export NAN_GHOST ?= $(LCGDIR)/ghost
    export NAN_TEST_VERBOSITY ?= 1
    export NAN_BMFONT ?= $(LCGDIR)/bmfont
    export NAN_OPENNL ?= $(LCGDIR)/opennl
    export NAN_ELBEEM ?= $(LCGDIR)/elbeem
    export NAN_SUPERLU ?= $(LCGDIR)/superlu
    ifeq ($(FREE_WINDOWS), true)
      export NAN_FTGL ?= $(LCGDIR)/gcc/ftgl
    else
      export NAN_FTGL ?= $(LCGDIR)/ftgl
    endif

    export WITH_OPENEXR ?= true
    ifeq ($(OS),windows)
      ifeq ($(FREE_WINDOWS), true)
        export NAN_OPENEXR ?= $(LCGDIR)/gcc/openexr
        export NAN_OPENEXR_LIBS ?= $(NAN_OPENEXR)/lib/libIlmImf.a $(NAN_OPENEXR)/lib/libHalf.a $(NAN_OPENEXR)/lib/libIex.a
        export NAN_OPENEXR_INC ?= -I$(NAN_OPENEXR)/include -I$(NAN_OPENEXR)/include/OpenEXR
      else
        export NAN_OPENEXR ?= $(LCGDIR)/openexr
        export NAN_OPENEXR_LIBS ?= $(NAN_OPENEXR)/lib/IlmImf.lib $(NAN_OPENEXR)/lib/Half.lib $(NAN_OPENEXR)/lib/Iex.lib
        export NAN_OPENEXR_INC ?= -I$(NAN_OPENEXR)/include -I$(NAN_OPENEXR)/include/IlmImf -I$(NAN_OPENEXR)/include/Imath -I$(NAN_OPENEXR)/include/Iex
      endif
    else
      export NAN_OPENEXR ?= /usr/local
      export NAN_OPENEXR_INC ?= -I$(NAN_OPENEXR)/include -I$(NAN_OPENEXR)/include/OpenEXR
      export NAN_OPENEXR_LIBS ?= $(NAN_OPENEXR)/lib/libIlmImf.a $(NAN_OPENEXR)/lib/libHalf.a $(NAN_OPENEXR)/lib/libIex.a
    endif
  # Platform Dependent settings go below:

  ifeq ($(OS),beos)

    export ID = $(USER)
    export HOST = $(HOSTNAME)
    export NAN_PYTHON ?= $(LCGDIR)/python
    export NAN_PYTHON_VERSION ?= 2.3
    export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    export NAN_OPENAL ?= $(LCGDIR)/openal
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= $(LCGDIR)/jpeg
    export NAN_PNG ?= $(LCGDIR)/png
    export NAN_TIFF ?= $(LCGDIR)/tiff
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= $(LCGDIR)/zlib
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_FREETYPE ?= $(LCGDIR)/freetype
    export NAN_GETTEXT ?= $(LCGDIR)/gettext
    export NAN_SDL ?= $(shell sdl-config --prefix)
    export NAN_SDLLIBS ?= $(shell sdl-config --libs) 
    export NAN_SDLCFLAGS ?= $(shell sdl-config --cflags)

    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # l10n
    #export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    #export WITH_FREETYPE2 ?= true

  else
  ifeq ($(OS),darwin)

    export ID = $(shell whoami)
    export HOST = $(shell hostname -s)

    export PY_FRAMEWORK	= 1    

    ifdef PY_FRAMEWORK
       export NAN_PYTHON ?= /System/Library/Frameworks/Python.framework/Versions/2.3
       export NAN_PYTHON_VERSION ?= 2.3
       export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    else 
       export NAN_PYTHON ?= /sw
       export NAN_PYTHON_VERSION ?= 2.3
       export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    endif

    export NAN_OPENAL ?= $(LCGDIR)/openal
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= $(LCGDIR)/jpeg
    export NAN_PNG ?= $(LCGDIR)/png
    export NAN_TIFF ?= $(LCGDIR)/tiff
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= $(LCGDIR)/zlib
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_FREETYPE ?= $(LCGDIR)/freetype
    export NAN_GETTEXT ?= $(LCGDIR)/gettext
    export NAN_SDL ?= $(LCGDIR)/sdl
    export NAN_SDLCFLAGS ?= -I$(NAN_SDL)/include
    export NAN_SDLLIBS ?= $(NAN_SDL)/lib/libSDL.a -framework Cocoa -framework IOKit

    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # enable quicktime by default on OS X
    export WITH_QUICKTIME ?= true

    # enable l10n
    export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    export WITH_FREETYPE2 ?= true

  else
  ifeq ($(OS),freebsd)

    export ID = $(shell whoami)
    export HOST = $(shell hostname -s)
    export NAN_PYTHON ?= /usr/local
    export NAN_PYTHON_VERSION ?= 2.3
    export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    export NAN_OPENAL ?= /usr/local
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= /usr/local
    export NAN_PNG ?= /usr/local
    export NAN_TIFF ?= /usr/local
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= /usr
    export NAN_NSPR ?= /usr/local
    export NAN_FREETYPE ?= $(LCGDIR)/freetype
    export NAN_GETTEXT ?= $(LCGDIR)/gettext
    export NAN_SDL ?= $(shell sdl11-config --prefix)
    export NAN_SDLLIBS ?= $(shell sdl11-config --libs)
    export NAN_SDLCFLAGS ?= $(shell sdl11-config --cflags)

    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # enable l10n
    # export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    # export WITH_FREETYPE2 ?= true

  else
  ifeq ($(OS),irix)

    export ID = $(shell whoami)
    export HOST = $(shell /usr/bsd/hostname -s)
    #export NAN_NO_KETSJI=true
    export NAN_JUST_BLENDERDYNAMIC=true
    export NAN_PYTHON ?= $(LCGDIR)/python
    export NAN_PYTHON_VERSION ?= 2.3
    export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    export NAN_OPENAL ?= $(LCGDIR)/openal
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= $(LCGDIR)/jpeg
    export NAN_PNG ?= $(LCGDIR)/png
    export NAN_TIFF ?= /usr/freeware
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= /usr/freeware
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_FREETYPE ?= /usr/freeware
    export NAN_GETTEXT ?= /usr/freeware
    export NAN_SDL ?= $(LCGDIR)/sdl
    export NAN_SDLLIBS ?= -L$(NAN_SDL)/lib -lSDL
    export NAN_SDLCFLAGS ?= -I$(NAN_SDL)/include/SDL
 
    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # enable l10n
    export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    export WITH_FREETYPE2 ?= true

  else
  ifeq ($(OS),linux)

    export ID = $(shell whoami)
    export HOST = $(shell hostname -s)
    export NAN_PYTHON ?= /usr
      ifeq ($(CPU),ia64)
    export NAN_PYTHON_VERSION ?= 2.2
      else
    export NAN_PYTHON_VERSION ?= 2.3
      endif
    export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    export NAN_OPENAL ?= /usr
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= /usr
    export NAN_PNG ?= /usr
    export NAN_TIFF ?= /usr
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr
    export NAN_ZLIB ?= /usr
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_FREETYPE ?= /usr
    export NAN_GETTEXT ?= /usr
    export NAN_SDL ?= $(shell sdl-config --prefix)
    export NAN_SDLLIBS ?= $(shell sdl-config --libs)
    export NAN_SDLCFLAGS ?= $(shell sdl-config --cflags)

    # Uncomment the following line to use Mozilla inplace of netscape
    export CPPFLAGS += -DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= /usr/include/mozilla
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # l10n
    export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    export WITH_FREETYPE2 ?= true


  else
  ifeq ($(OS),openbsd)

    export ID = $(shell whoami)
    export HOST = $(shell hostname -s)
    export NAN_PYTHON ?= $(LCGDIR)/python
    export NAN_PYTHON_VERSION ?= 2.3
    export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    export NAN_OPENAL ?= $(LCGDIR)/openal
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= $(LCGDIR)/jpeg
    export NAN_PNG ?= $(LCGDIR)/png
    export NAN_TIFF ?= $(LCGDIR)/tiff
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= $(LCGDIR)/zlib
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_FREETYPE ?= $(LCGDIR)/freetype
    export NAN_GETTEXT ?= $(LCGDIR)/gettext
    export NAN_SDL ?= $(shell sdl-config --prefix)
    export NAN_SDLLIBS ?= $(shell sdl-config --libs)
    export NAN_SDLCFLAGS ?= $(shell sdl-config --cflags)

    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # l10n
    #export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    #export WITH_FREETYPE2 ?= true

  else
  ifeq ($(OS),solaris)

    export ID = $(shell /usr/ucb/whoami)
    export HOST = $(shell hostname)
    export NAN_PYTHON ?= /usr/local
    export NAN_PYTHON_VERSION ?= 2.3
    export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
    export NAN_OPENAL ?= /usr/local
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= /usr/local
    export NAN_PNG ?= /usr/local
    export NAN_TIFF ?= /usr
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?=
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= /usr
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_FREETYPE ?= $(LCGDIR)/freetype
    export NAN_GETTEXT ?= $(LCGDIR)/gettext
    export NAN_SDL ?= $(shell sdl-config --prefix)
    export NAN_SDLLIBS ?= $(shell sdl-config --libs)
    export NAN_SDLCFLAGS ?= $(shell sdl-config --cflags)

    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # l10n
    #export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    #export WITH_FREETYPE2 ?= true

  else
  ifeq ($(OS),windows)

    export ID = $(LOGNAME)
    export NAN_NO_KETSJI=false
    export NAN_PYTHON ?= $(LCGDIR)/python
    export NAN_ICONV ?= $(LCGDIR)/iconv
    export NAN_PYTHON_VERSION ?= 2.4
    ifeq ($(FREE_WINDOWS), true)
      export NAN_PYTHON_BINARY ?= $(NAN_PYTHON)/bin/python$(NAN_PYTHON_VERSION)
      export NAN_FREETYPE ?= $(LCGDIR)/gcc/freetype
      export NAN_ODE ?= $(LCGDIR)/gcc/ode
      ifeq ($(NAN_SDL),)
	  export NAN_SDL ?= $(LCGDIR)/gcc/sdl
	  export NAN_SDLCFLAGS ?= -I$(NAN_SDL)/include
      endif
    else
      export NAN_PYTHON_BINARY ?= python
      export NAN_FREETYPE ?= $(LCGDIR)/freetype
      export NAN_ODE ?= $(LCGDIR)/ode
      ifeq ($(NAN_SDL),)
	  export NAN_SDL ?= $(LCGDIR)/sdl
	  export NAN_SDLCFLAGS ?= -I$(NAN_SDL)/include
      endif
    endif
    export NAN_OPENAL ?= $(LCGDIR)/openal
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= $(LCGDIR)/jpeg
    export NAN_PNG ?= $(LCGDIR)/png
    export NAN_TIFF ?= $(LCGDIR)/tiff
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= $(LCGDIR)/zlib
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_GETTEXT ?= $(LCGDIR)/gettext

    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.
	export NAN_PYTHON_BINARY ?= python
    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # l10n
    export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    export WITH_FREETYPE2 ?= true
    
    # enable quicktime support
    # export WITH_QUICKTIME ?= true

  else # Platform not listed above

    export NAN_PYTHON ?= $(LCGDIR)/python
    export NAN_PYTHON_VERSION ?= 2.3
    export NAN_PYTHON_BINARY ?= python
    export NAN_OPENAL ?= $(LCGDIR)/openal
    export NAN_FMOD ?= $(LCGDIR)/fmod
    export NAN_JPEG ?= $(LCGDIR)/jpeg
    export NAN_PNG ?= $(LCGDIR)/png
    export NAN_TIFF ?= $(LCGDIR)/tiff
    export NAN_SDL ?= $(LCGDIR)/sdl
    export NAN_ODE ?= $(LCGDIR)/ode
    export NAN_TERRAPLAY ?= $(LCGDIR)/terraplay
    export NAN_MESA ?= /usr/src/Mesa-3.1
    export NAN_ZLIB ?= $(LCGDIR)/zlib
    export NAN_NSPR ?= $(LCGDIR)/nspr
    export NAN_FREETYPE ?= $(LCGDIR)/freetype
    export NAN_GETTEXT ?= $(LCGDIR)/gettext
    export NAN_SDL ?= $(shell sdl-config --prefix)
    export NAN_SDLLIBS ?= $(shell sdl-config --libs)
    export NAN_SDLCFLAGS ?= $(shell sdl-config --cflags)

    # Uncomment the following line to use Mozilla inplace of netscape
    # CPPFLAGS +=-DMOZ_NOT_NET
    # Location of MOZILLA/Netscape header files...
    export NAN_MOZILLA_INC ?= $(LCGDIR)/mozilla/include
    export NAN_MOZILLA_LIB ?= $(LCGDIR)/mozilla/lib/
    # Will fall back to look in NAN_MOZILLA_INC/nspr and NAN_MOZILLA_LIB
    # if this is not set.

    export NAN_BUILDINFO ?= true
    # Be paranoid regarding library creation (do not update archives)
    export NAN_PARANOID ?= true

    # l10n
    #export INTERNATIONAL ?= true

    # enable freetype2 support for text objects
    #export WITH_FREETYPE2 ?= true
  endif

endif
endif
endif
endif
endif
endif
endif
endif

# Don't want to build the gameengine?
ifeq ($(NAN_NO_KETSJI), true)
   export NAN_JUST_BLENDERDYNAMIC=true
   export NAN_NO_OPENAL=true
endif
