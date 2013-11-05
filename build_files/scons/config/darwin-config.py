#
# Note : if you want to alter this file
# copy it as a whole in the upper folder
# as user-config.py
# dont create a new file with only some
# vars changed.

import commands

# IMPORTANT NOTE : OFFICIAL BUILDS SHOULD BE DONE WITH SDKs
USE_SDK=True

#############################################################################
###################     Cocoa & architecture settings      ##################
#############################################################################
WITH_GHOST_COCOA=True
MACOSX_ARCHITECTURE = 'x86_64' # valid archs: ppc, i386, ppc64, x86_64


cmd = 'uname -p'
MAC_PROC=commands.getoutput(cmd)
cmd = 'uname -r'
cmd_res=commands.getoutput(cmd)

if cmd_res[:1]=='7':
    MAC_CUR_VER='10.3'
elif cmd_res[:1]=='8':
    MAC_CUR_VER='10.4'
elif cmd_res[:1]=='9':
    MAC_CUR_VER='10.5'
elif cmd_res[:2]=='10':
    MAC_CUR_VER='10.6'
elif cmd_res[:2]=='11':
    MAC_CUR_VER='10.7'
elif cmd_res[:2]=='12':
    MAC_CUR_VER='10.8'
elif cmd_res[:2]=='13':
    MAC_CUR_VER='10.9'
cmd = 'xcodebuild -version'
cmd_xcode=commands.getoutput(cmd)
XCODE_CUR_VER=cmd_xcode[6:][:3] # truncate output to major.minor version
cmd = 'xcodebuild -showsdks'
cmd_sdk=commands.getoutput(cmd)
MACOSX_SDK_CHECK=cmd_sdk
cmd = 'xcode-select --print-path'
XCODE_SELECT_PATH=commands.getoutput(cmd)
if XCODE_SELECT_PATH.endswith("/Contents/Developer"):
	XCODE_BUNDLE=XCODE_SELECT_PATH[:-19]
else:
	XCODE_BUNDLE=XCODE_SELECT_PATH

if MACOSX_ARCHITECTURE == 'x86_64' or MACOSX_ARCHITECTURE == 'ppc64':
    USE_QTKIT=True # Carbon quicktime is not available for 64bit


# Default target OSX settings per architecture
# Can be customized

if MACOSX_ARCHITECTURE == 'ppc' and MAC_CUR_VER == '10.4':
# all releases are now made for 10.5 !
#   MAC_MIN_VERS = '10.3'
#   MACOSX_SDK='/Developer/SDKs/MacOSX10.3.9.sdk'
#   LCGDIR = '#../lib/darwin-6.1-powerpc'
#   CC = 'gcc-3.3'
#   CXX = 'g++-3.3'
    MAC_MIN_VERS = '10.4'
    MACOSX_DEPLOYMENT_TARGET = '10.4'
    MACOSX_SDK='/Developer/SDKs/MacOSX10.4u.sdk'
    LCGDIR = '#../lib/darwin-8.0.0-powerpc'
    CC = 'gcc-4.0'
    CXX = 'g++-4.0'
elif MACOSX_ARCHITECTURE == 'i386' and MAC_CUR_VER == '10.4':
    MAC_MIN_VERS = '10.4'
    MACOSX_DEPLOYMENT_TARGET = '10.4'
    MACOSX_SDK='/Developer/SDKs/MacOSX10.4u.sdk'
    LCGDIR = '#../lib/darwin-8.x.i386'
    CC = 'gcc-4.0'
    CXX = 'g++-4.0'
else :
    if 'Mac OS X 10.5' in MACOSX_SDK_CHECK:
        # OSX 10.5/6 with Xcode 3.x
        MAC_MIN_VERS = '10.5'
        MACOSX_DEPLOYMENT_TARGET = '10.5'
        MACOSX_SDK='/Developer/SDKs/MacOSX10.5.sdk'
        LCGDIR = '#../lib/darwin-9.x.universal'
        CC = 'gcc-4.2'
        CXX = 'g++-4.2'
    elif 'Mac OS X 10.6' in MACOSX_SDK_CHECK:
        # OSX 10.6/7 with Xcode 4.x
        MAC_MIN_VERS = '10.6'
        MACOSX_DEPLOYMENT_TARGET = '10.6'
        MACOSX_SDK='/Developer/SDKs/MacOSX10.6.sdk'
        LCGDIR = '#../lib/darwin-9.x.universal'
        CC = 'gcc-4.2'
        CXX = 'g++-4.2'
    else:
        # OSX 10.8 with Xcode 4.4 and higher (no 10.6sdk! )
        MAC_MIN_VERS = '10.6'
        MACOSX_DEPLOYMENT_TARGET = '10.6'
        MACOSX_SDK='/Developer/SDKs/MacOSX10.8.sdk'
        LCGDIR = '#../lib/darwin-9.x.universal'
        CC = 'gcc'
        CXX = 'g++'

LIBDIR = '${LCGDIR}'

if XCODE_CUR_VER >= '4.3':  ## since version 4.3, XCode and developer dir are bundled ##
	MACOSX_SDK = XCODE_BUNDLE + '/Contents/Developer/Platforms/MacOSX.platform' + MACOSX_SDK

#############################################################################
###################          Dependency settings           ##################
#############################################################################

#Defaults openMP to true if compiler handles it ( only gcc 4.6.1 and newer )
# if your compiler does not have accurate suffix you may have to enable it by hand !
if CC[:-2].endswith('4.6') or CC[:-2].endswith('4.8'):
    WITH_BF_OPENMP = True  # multithreading for fluids, cloth, sculpt and smoke
else:
    WITH_BF_OPENMP = False

# enable ffmpeg  support
WITH_BF_FFMPEG = True
BF_FFMPEG = LIBDIR + '/ffmpeg'
BF_FFMPEG_INC = "${BF_FFMPEG}/include"
BF_FFMPEG_LIBPATH='${BF_FFMPEG}/lib'
BF_FFMPEG_LIB = 'avcodec avdevice avformat avutil mp3lame swscale x264 xvidcore theora theoradec theoraenc vorbis vorbisenc vorbisfile ogg bz2'
#bz2 is a standard osx dynlib

BF_PYTHON_VERSION = '3.3'
WITH_OSX_STATICPYTHON = True

if WITH_OSX_STATICPYTHON:
    # python 3.3 uses precompiled libraries in bf svn /lib by default

    BF_PYTHON = LIBDIR + '/python'
    BF_PYTHON_INC = '${BF_PYTHON}/include/python${BF_PYTHON_VERSION}m'
    # BF_PYTHON_BINARY = '${BF_PYTHON}/bin/python${BF_PYTHON_VERSION}'
    BF_PYTHON_LIB = 'python${BF_PYTHON_VERSION}m'
    BF_PYTHON_LIBPATH = '${BF_PYTHON}/lib/python${BF_PYTHON_VERSION}'
    # BF_PYTHON_LINKFLAGS = ['-u', '_PyMac_Error', '-framework', 'System']
else:
    # python 3.2 uses Python-framework additionally installed in /Library/Frameworks

    BF_PYTHON = '/Library/Frameworks/Python.framework/Versions/'
    BF_PYTHON_INC = '${BF_PYTHON}${BF_PYTHON_VERSION}/include/python${BF_PYTHON_VERSION}m'
    BF_PYTHON_BINARY = '${BF_PYTHON}${BF_PYTHON_VERSION}/bin/python${BF_PYTHON_VERSION}'
    #BF_PYTHON_LIB = ''
    BF_PYTHON_LIBPATH = '${BF_PYTHON}${BF_PYTHON_VERSION}/lib/python${BF_PYTHON_VERSION}/config-${BF_PYTHON_VERSION}m'

WITH_BF_OPENAL = True
#different lib must be used  following version of gcc
# for gcc 3.3
#BF_OPENAL = LIBDIR + '/openal'
# for gcc 3.4 and ulterior
if MAC_PROC == 'powerpc':
    BF_OPENAL = '#../lib/darwin-8.0.0-powerpc/openal'
else :
    BF_OPENAL = LIBDIR + '/openal'

WITH_BF_STATICOPENAL = False
BF_OPENAL_INC = '${BF_OPENAL}/include' # only headers from libdir needed for proper use of framework !!!!
#BF_OPENAL_LIB = 'openal'
#BF_OPENAL_LIBPATH = '${BF_OPENAL}/lib'
# Warning, this static lib configuration is untested! users of this OS please confirm.
#BF_OPENAL_LIB_STATIC = '${BF_OPENAL}/lib/libopenal.a'

# Warning, this static lib configuration is untested! users of this OS please confirm.
BF_CXX = '/usr'
WITH_BF_STATICCXX = False
BF_CXX_LIB_STATIC = '${BF_CXX}/lib/libstdc++.a'

# we use simply jack framework
WITH_BF_JACK = True
BF_JACK = '/Library/Frameworks/Jackmp.framework'
BF_JACK_INC = '${BF_JACK}/headers'
#BF_JACK_LIB = 'jack' # not used due framework
BF_JACK_LIBPATH = '${BF_JACK}'

WITH_BF_SNDFILE = True
BF_SNDFILE = LIBDIR + '/sndfile'
BF_SNDFILE_INC = '${BF_SNDFILE}/include'
BF_SNDFILE_LIB = 'sndfile FLAC ogg vorbis vorbisenc'
BF_SNDFILE_LIBPATH = '${BF_SNDFILE}/lib ${BF_FFMPEG}/lib' #ogg libs are stored in ffmpeg dir

WITH_BF_SDL = True
BF_SDL = LIBDIR + '/sdl' #$(shell sdl-config --prefix)
BF_SDL_INC = '${BF_SDL}/include' #$(shell $(BF_SDL)/bin/sdl-config --cflags)
BF_SDL_LIB = 'SDL' #BF_SDL #$(shell $(BF_SDL)/bin/sdl-config --libs) -lSDL_mixer
BF_SDL_LIBPATH = '${BF_SDL}/lib'

WITH_BF_OPENEXR = True
WITH_BF_STATICOPENEXR = False
BF_OPENEXR = '${LCGDIR}/openexr'
BF_OPENEXR_INC = '${BF_OPENEXR}/include ${BF_OPENEXR}/include/OpenEXR'
BF_OPENEXR_LIB = ' Iex Half IlmImf Imath IlmThread'
BF_OPENEXR_LIBPATH = '${BF_OPENEXR}/lib'
# Warning, this static lib configuration is untested! users of this OS please confirm.
BF_OPENEXR_LIB_STATIC = '${BF_OPENEXR}/lib/libHalf.a ${BF_OPENEXR}/lib/libIlmImf.a ${BF_OPENEXR}/lib/libIex.a ${BF_OPENEXR}/lib/libImath.a ${BF_OPENEXR}/lib/libIlmThread.a'

WITH_BF_DDS = True

#Color Management System
WITH_BF_LCMS = False
BF_LCMS = LIBDIR + '/lcms'
BF_LCMS_INC = '${BF_LCMS}/include'
BF_LCMS_LIB = 'lcms'
BF_LCMS_LIBPATH = '${BF_LCMS}/lib'

WITH_BF_JPEG = True
BF_JPEG = LIBDIR + '/jpeg'
BF_JPEG_INC = '${BF_JPEG}/include'
BF_JPEG_LIB = 'jpeg'
BF_JPEG_LIBPATH = '${BF_JPEG}/lib'

WITH_BF_PNG = True
BF_PNG = LIBDIR + '/png'
BF_PNG_INC = '${BF_PNG}/include'
BF_PNG_LIB = 'png'
BF_PNG_LIBPATH = '${BF_PNG}/lib'

WITH_BF_TIFF = True
BF_TIFF = LIBDIR + '/tiff'
BF_TIFF_INC = '${BF_TIFF}/include'
BF_TIFF_LIB = 'tiff'
BF_TIFF_LIBPATH = '${BF_TIFF}/lib'

WITH_BF_ZLIB = True
BF_ZLIB = '/usr'
BF_ZLIB_INC = '${BF_ZLIB}/include'
BF_ZLIB_LIB = 'z'

WITH_BF_INTERNATIONAL = True

WITH_BF_GAMEENGINE = True
WITH_BF_PLAYER = True
WITH_BF_OCEANSIM = True

WITH_BF_BULLET = True
BF_BULLET = '#extern/bullet2/src'
BF_BULLET_INC = '${BF_BULLET}'
BF_BULLET_LIB = 'extern_bullet'

WITH_BF_FFTW3 = True
BF_FFTW3 = LIBDIR + '/fftw3'
BF_FFTW3_INC = '${BF_FFTW3}/include'
BF_FFTW3_LIB = 'libfftw3'
BF_FFTW3_LIBPATH = '${BF_FFTW3}/lib'

BF_FREETYPE = LIBDIR + '/freetype'
BF_FREETYPE_INC = '${BF_FREETYPE}/include ${BF_FREETYPE}/include/freetype2'
BF_FREETYPE_LIB = 'freetype'
BF_FREETYPE_LIBPATH = '${BF_FREETYPE}/lib'

WITH_BF_QUICKTIME = True

WITH_BF_ICONV = True
BF_ICONV = '/usr'
BF_ICONV_INC = '${BF_ICONV}/include'
BF_ICONV_LIB = 'iconv'
#BF_ICONV_LIBPATH = '${BF_ICONV}/lib'

# Mesa Libs should go here if your using them as well....
WITH_BF_STATICOPENGL = True
BF_OPENGL_LIB = 'GL GLU'
BF_OPENGL_LIBPATH = '/System/Library/Frameworks/OpenGL.framework/Libraries'
BF_OPENGL_LINKFLAGS = ['-framework', 'OpenGL']

#OpenCollada flags
WITH_BF_COLLADA = True
BF_COLLADA = '#source/blender/collada'
BF_COLLADA_INC = '${BF_COLLADA}'
BF_COLLADA_LIB = 'bf_collada'
BF_OPENCOLLADA = LIBDIR + '/opencollada'
BF_OPENCOLLADA_INC = '${BF_OPENCOLLADA}/include'
BF_OPENCOLLADA_LIB = 'OpenCOLLADASaxFrameworkLoader OpenCOLLADAFramework OpenCOLLADABaseUtils OpenCOLLADAStreamWriter MathMLSolver GeneratedSaxParser UTF xml2 buffer ftoa'
BF_OPENCOLLADA_LIBPATH = LIBDIR + '/opencollada'
BF_PCRE = LIBDIR + '/opencollada'
BF_PCRE_LIB = 'pcre'
BF_PCRE_LIBPATH = '${BF_PCRE}/lib'
#BF_EXPAT = '/usr'
#BF_EXPAT_LIB = 'expat'
#BF_EXPAT_LIBPATH = '/usr/lib'

# Cycles
WITH_BF_CYCLES = True

#OSL

WITH_BF_CYCLES_OSL = True
BF_OSL = LIBDIR + '/osl'
BF_OSL_INC = '${BF_OSL}/include'
# note oslexec would passed via program linkflags, which is needed to
# make llvm happy with osl_allocate_closure_component
#BF_OSL_LIB = 'oslcomp oslquery'
BF_OSL_LIBPATH = '${BF_OSL}/lib'
BF_OSL_COMPILER = '${BF_OSL}/bin/oslc'

WITH_BF_LLVM = True
BF_LLVM = LIBDIR + '/llvm'
BF_LLVM_LIB = 'LLVMBitReader LLVMJIT LLVMipo LLVMVectorize LLVMBitWriter LLVMX86CodeGen LLVMX86Desc LLVMX86Info LLVMX86AsmPrinter ' + \
    'LLVMX86Utils LLVMSelectionDAG LLVMCodeGen LLVMScalarOpts LLVMInstCombine LLVMTransformUtils LLVMipa LLVMAnalysis LLVMExecutionEngine ' + \
    'LLVMTarget LLVMMC LLVMCore LLVMSupport'
BF_LLVM_LIBPATH = '${BF_LLVM}/lib'

WITH_BF_OIIO = True
BF_OIIO = LIBDIR + '/openimageio'
BF_OIIO_INC = '${BF_OIIO}/include'
BF_OIIO_LIB = 'OpenImageIO'
BF_OIIO_LIBPATH = '${BF_OIIO}/lib'

WITH_BF_OCIO = True
BF_OCIO = LIBDIR + '/opencolorio'
BF_OCIO_INC = '${BF_OCIO}/include'
BF_OCIO_LIB = 'OpenColorIO tinyxml yaml-cpp'
BF_OCIO_LIBPATH = '${BF_OCIO}/lib'

WITH_BF_BOOST = True
BF_BOOST = LIBDIR + '/boost'
BF_BOOST_INC = '${BF_BOOST}/include'
BF_BOOST_LIB = 'boost_date_time-mt boost_filesystem-mt boost_regex-mt boost_system-mt boost_thread-mt boost_wave-mt'
BF_BOOST_LIB_INTERNATIONAL = 'boost_locale-mt'
BF_BOOST_LIBPATH = '${BF_BOOST}/lib'

WITH_BF_CYCLES_CUDA_BINARIES = False
BF_CYCLES_CUDA_NVCC = '/usr/local/cuda/bin/nvcc'
BF_CYCLES_CUDA_BINARIES_ARCH = ['sm_20', 'sm_21', 'sm_30', 'sm_35']

#Freestyle
WITH_BF_FREESTYLE = True

#Ray trace optimization
if MACOSX_ARCHITECTURE == 'x86_64' or MACOSX_ARCHITECTURE == 'i386':
    WITH_BF_RAYOPTIMIZATION = True
else:
    WITH_BF_RAYOPTIMIZATION = False
if MACOSX_ARCHITECTURE == 'i386':
    BF_RAYOPTIMIZATION_SSE_FLAGS = ['-msse']
elif MACOSX_ARCHITECTURE == 'x86_64':
    BF_RAYOPTIMIZATION_SSE_FLAGS = ['-msse','-msse2']

# SpaceNavigator and related 3D mice, driver must be 3DxWare 10 Beta 4 (Mac OS X) or later !
WITH_BF_3DMOUSE = True

#############################################################################
###################  various compile settings and flags    ##################
#############################################################################

BF_QUIET = '1' # suppress verbose output

if MACOSX_ARCHITECTURE == 'x86_64' or MACOSX_ARCHITECTURE == 'ppc64':
    ARCH_FLAGS = ['-m64']
else:
    ARCH_FLAGS = ['-m32']

CFLAGS = []
CXXFLAGS = []
CCFLAGS = ['-pipe','-funsigned-char']


CPPFLAGS = list(ARCH_FLAGS)

if WITH_GHOST_COCOA:
    PLATFORM_LINKFLAGS = ['-fexceptions','-framework','CoreServices','-framework','Foundation','-framework','IOKit','-framework','AppKit','-framework','Cocoa','-framework','Carbon','-framework','AudioUnit','-framework','AudioToolbox','-framework','CoreAudio','-framework','OpenAL']+ARCH_FLAGS
else:
    PLATFORM_LINKFLAGS = ['-fexceptions','-framework','CoreServices','-framework','Foundation','-framework','IOKit','-framework','AppKit','-framework','Carbon','-framework','AGL','-framework','AudioUnit','-framework','AudioToolbox','-framework','CoreAudio','-framework','OpenAL']+ARCH_FLAGS

if WITH_BF_QUICKTIME:
    if USE_QTKIT:
        PLATFORM_LINKFLAGS = PLATFORM_LINKFLAGS+['-framework','QTKit']
    else:
        PLATFORM_LINKFLAGS = PLATFORM_LINKFLAGS+['-framework','QuickTime']

if not WITH_OSX_STATICPYTHON:
    PLATFORM_LINKFLAGS = PLATFORM_LINKFLAGS+['-framework','Python']


#note to build succesfully on 10.3.9 SDK you need to patch  10.3.9 by adding the SystemStubs.a lib from 10.4
#for > 10.7.sdk, SystemStubs needs to be excluded (lib doesn't exist anymore)
if MACOSX_SDK.endswith("10.7.sdk") or MACOSX_SDK.endswith("10.8.sdk") or MACOSX_SDK.endswith("10.9.sdk"):
    LLIBS = ['stdc++']
else:
    LLIBS = ['stdc++', 'SystemStubs']

# some flags shuffling for different OS versions
if MAC_MIN_VERS == '10.3':
    CCFLAGS = ['-fuse-cxa-atexit'] + CCFLAGS
    PLATFORM_LINKFLAGS = ['-fuse-cxa-atexit'] + PLATFORM_LINKFLAGS
    LLIBS.append('crt3.o')

if USE_SDK:
    SDK_FLAGS=['-isysroot', MACOSX_SDK,'-mmacosx-version-min='+MAC_MIN_VERS,'-arch',MACOSX_ARCHITECTURE]
    PLATFORM_LINKFLAGS = ['-mmacosx-version-min='+MAC_MIN_VERS,'-Wl','-isysroot',MACOSX_SDK,'-arch',MACOSX_ARCHITECTURE]+PLATFORM_LINKFLAGS
    CCFLAGS=SDK_FLAGS+CCFLAGS
    CXXFLAGS=SDK_FLAGS+CXXFLAGS

#Intel Macs are CoreDuo and Up
if MACOSX_ARCHITECTURE == 'i386' or MACOSX_ARCHITECTURE == 'x86_64':
    REL_CFLAGS = []
    REL_CXXFLAGS = []
    REL_CCFLAGS = ['-DNDEBUG', '-O2','-ftree-vectorize','-msse','-msse2','-msse3','-mfpmath=sse']
else:
    CCFLAGS += ['-fno-strict-aliasing']
    REL_CFLAGS = []
    REL_CXXFLAGS = []
    REL_CCFLAGS = ['-DNDEBUG', '-O2']

# Intel 64bit Macs are Core2Duo and up
if MACOSX_ARCHITECTURE == 'x86_64':
    REL_CCFLAGS += ['-march=core2','-mssse3','-with-tune=core2','-enable-threads']

CC_WARN = ['-Wall']
C_WARN = ['-Wno-char-subscripts', '-Wpointer-arith', '-Wcast-align', '-Wdeclaration-after-statement', '-Wno-unknown-pragmas', '-Wstrict-prototypes']
CXX_WARN = ['-Wno-invalid-offsetof', '-Wno-sign-compare']

##FIX_STUBS_WARNINGS = -Wno-unused

##LOPTS = --dynamic
##DYNLDFLAGS = -shared $(LDFLAGS)

BF_PROFILE_CCFLAGS = ['-pg', '-g ']
BF_PROFILE_LINKFLAGS = ['-pg']
BF_PROFILE = False

BF_DEBUG = False
BF_DEBUG_CCFLAGS = ['-g', '-D_DEBUG']

#############################################################################
###################           Output directories           ##################
#############################################################################

BF_BUILDDIR='../build/darwin'
BF_INSTALLDIR='../install/darwin'
