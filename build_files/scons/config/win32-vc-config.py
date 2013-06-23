import subprocess

CL_OUT = subprocess.Popen(["cl.exe"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
CL_STDOUT, CL_STDERR = CL_OUT.communicate()

if CL_STDERR.find("Version 15.00.") == -1:
    VC_VERSION = '11.0'
    LCGDIR = '#../lib/windows_vc11'
    
else:
    VC_VERSION = '9.0'
    LCGDIR = '#../lib/windows'

LIBDIR = '${LCGDIR}'

WITH_BF_FFMPEG = True
BF_FFMPEG = LIBDIR +'/ffmpeg'
BF_FFMPEG_INC = '${BF_FFMPEG}/include ${BF_FFMPEG}/include/msvc'
BF_FFMPEG_LIBPATH='${BF_FFMPEG}/lib'
if VC_VERSION == '11.0':
    BF_FFMPEG_LIB = 'avformat-54.lib avcodec-54.lib avdevice-54.lib avutil-52.lib avfilter-3.lib swscale-2.lib swresample-0.lib'
    BF_FFMPEG_DLL = '${BF_FFMPEG_LIBPATH}/avformat-54.dll ${BF_FFMPEG_LIBPATH}/avcodec-54.dll ${BF_FFMPEG_LIBPATH}/avdevice-54.dll ${BF_FFMPEG_LIBPATH}/avutil-52.dll ${BF_FFMPEG_LIBPATH}/avfilter-3.dll ${BF_FFMPEG_LIBPATH}/swscale-2.dll ${BF_FFMPEG_LIBPATH}/swresample-0.dll'
else:
    BF_FFMPEG_LIB = 'avformat-53.lib avcodec-53.lib avdevice-53.lib avutil-51.lib swscale-2.lib'
    BF_FFMPEG_DLL = '${BF_FFMPEG_LIBPATH}/avformat-53.dll ${BF_FFMPEG_LIBPATH}/avcodec-53.dll ${BF_FFMPEG_LIBPATH}/avdevice-53.dll ${BF_FFMPEG_LIBPATH}/avutil-51.dll ${BF_FFMPEG_LIBPATH}/swscale-2.dll'

BF_PYTHON = LIBDIR + '/python'
BF_PYTHON_VERSION = '3.3'
BF_PYTHON_INC = '${BF_PYTHON}/include/python${BF_PYTHON_VERSION}'
BF_PYTHON_BINARY = 'python'
BF_PYTHON_LIB = 'python33'
BF_PYTHON_DLL = '${BF_PYTHON_LIB}'
BF_PYTHON_LIBPATH = '${BF_PYTHON}/lib'

WITH_BF_OPENAL = True
BF_OPENAL = LIBDIR + '/openal'
BF_OPENAL_INC = '${BF_OPENAL}/include '
if VC_VERSION == '11.0':
    BF_OPENAL_LIB = 'OpenAL32'
else:
    BF_OPENAL_LIB = 'wrap_oal'
BF_OPENAL_LIBPATH = '${BF_OPENAL}/lib'

WITH_BF_ICONV = True
BF_ICONV = LIBDIR + '/iconv'
BF_ICONV_INC = '${BF_ICONV}/include'
BF_ICONV_LIB = 'iconv'
BF_ICONV_LIBPATH = '${BF_ICONV}/lib'

WITH_BF_JACK = False
BF_JACK = LIBDIR + '/jack'
BF_JACK_INC = '${BF_JACK}/include ${BF_FFMPEG}/include/msvc'
BF_JACK_LIB = 'libjack'
BF_JACK_LIBPATH = '${BF_JACK}/lib'

WITH_BF_SNDFILE = True
BF_SNDFILE = LIBDIR + '/sndfile'
BF_SNDFILE_INC = '${BF_SNDFILE}/include'
BF_SNDFILE_LIB = 'libsndfile-1'
BF_SNDFILE_LIBPATH = '${BF_SNDFILE}/lib'

WITH_BF_SDL = True
BF_SDL = LIBDIR + '/sdl'
BF_SDL_INC = '${BF_SDL}/include'
if VC_VERSION == '11.0':
    BF_SDL_LIB = 'SDL.lib dxguid.lib'
else:
    BF_SDL_LIB = 'SDL.lib'
BF_SDL_LIBPATH = '${BF_SDL}/lib'

BF_PTHREADS = LIBDIR + '/pthreads'
BF_PTHREADS_INC = '${BF_PTHREADS}/include'
BF_PTHREADS_LIB = 'pthreadVC2'
BF_PTHREADS_LIBPATH = '${BF_PTHREADS}/lib'

WITH_BF_OPENEXR = True
WITH_BF_STATICOPENEXR = False
BF_OPENEXR = LIBDIR + '/openexr'
BF_OPENEXR_INC = '${BF_OPENEXR}/include ${BF_OPENEXR}/include/OpenEXR '
BF_OPENEXR_LIB = ' Iex Half IlmImf Imath IlmThread '
BF_OPENEXR_LIBPATH = '${BF_OPENEXR}/lib'
BF_OPENEXR_LIB_STATIC = '${BF_OPENEXR}/lib/libHalf.a ${BF_OPENEXR}/lib/libIlmImf.a ${BF_OPENEXR}/lib/libIex.a ${BF_OPENEXR}/lib/libImath.a ${BF_OPENEXR}/lib/libIlmThread.a'

WITH_BF_DDS = True

WITH_BF_JPEG = True
BF_JPEG = LIBDIR + '/jpeg'
BF_JPEG_INC = '${BF_JPEG}/include'
BF_JPEG_LIB = 'libjpeg'
BF_JPEG_LIBPATH = '${BF_JPEG}/lib'

WITH_BF_PNG = True
BF_PNG = LIBDIR + '/png'
BF_PNG_INC = '${BF_PNG}/include'
BF_PNG_LIB = 'libpng'
BF_PNG_LIBPATH = '${BF_PNG}/lib'

WITH_BF_TIFF = True
BF_TIFF = LIBDIR + '/tiff'
BF_TIFF_INC = '${BF_TIFF}/include'
BF_TIFF_LIB = 'libtiff'
BF_TIFF_LIBPATH = '${BF_TIFF}/lib'

WITH_BF_ZLIB = True
BF_ZLIB = LIBDIR + '/zlib'
BF_ZLIB_INC = '${BF_ZLIB}/include'
BF_ZLIB_LIB = 'libz_st'
BF_ZLIB_LIBPATH = '${BF_ZLIB}/lib'

WITH_BF_INTERNATIONAL = True

WITH_BF_GAMEENGINE = True
WITH_BF_PLAYER = True
WITH_BF_OCEANSIM = True

WITH_BF_BULLET = True
BF_BULLET = '#extern/bullet2/src'
BF_BULLET_INC = '${BF_BULLET}'
BF_BULLET_LIB = 'extern_bullet'

WITH_BF_ELTOPO = False
BF_LAPACK = LIBDIR + '/lapack'
BF_LAPACK_LIB = 'libf2c clapack_nowrap BLAS_nowrap'
BF_LAPACK_LIBPATH = '${BF_LAPACK}/lib'

BF_WINTAB = LIBDIR + '/wintab'
BF_WINTAB_INC = '${BF_WINTAB}/INCLUDE'

WITH_BF_BINRELOC = False

BF_WITH_FREETYPE = True
BF_FREETYPE = LIBDIR + '/freetype'
BF_FREETYPE_INC = '${BF_FREETYPE}/include ${BF_FREETYPE}/include/freetype2'
BF_FREETYPE_LIB = 'freetype2ST'
BF_FREETYPE_LIBPATH = '${BF_FREETYPE}/lib'

WITH_BF_QUICKTIME = False
BF_QUICKTIME = LIBDIR + '/QTDevWin'
BF_QUICKTIME_INC = '${BF_QUICKTIME}/CIncludes'
BF_QUICKTIME_LIB = 'qtmlClient'
BF_QUICKTIME_LIBPATH = '${BF_QUICKTIME}/Libraries'

WITH_BF_OPENJPEG = True 
BF_OPENJPEG = '#extern/libopenjpeg'
BF_OPENJPEG_LIB = ''
BF_OPENJPEG_INC = '${BF_OPENJPEG}'
BF_OPENJPEG_LIBPATH='${BF_OPENJPEG}/lib'

WITH_BF_FFTW3 = True
BF_FFTW3 = LIBDIR + '/fftw3'
BF_FFTW3_INC = '${BF_FFTW3}/include'
BF_FFTW3_LIB = 'libfftw'
BF_FFTW3_LIBPATH = '${BF_FFTW3}/lib'

WITH_BF_REDCODE = False  
BF_REDCODE_INC = '#extern'

WITH_BF_COLLADA = True
BF_COLLADA = '#source/blender/collada'
BF_COLLADA_INC = '${BF_COLLADA}'
BF_COLLADA_LIB = 'bf_collada'

BF_OPENCOLLADA = LIBDIR + '/opencollada'
BF_OPENCOLLADA_INC = '${BF_OPENCOLLADA}/include/opencollada'
BF_OPENCOLLADA_LIB = 'OpenCOLLADAStreamWriter OpenCOLLADASaxFrameworkLoader OpenCOLLADAFramework OpenCOLLADABaseUtils GeneratedSaxParser MathMLSolver xml pcre buffer ftoa UTF'
BF_OPENCOLLADA_LIBPATH = '${BF_OPENCOLLADA}/lib/opencollada'

WITH_BF_3DMOUSE = True

WITH_BF_OPENMP = True

#Cycles
WITH_BF_CYCLES = True 

WITH_BF_CYCLES_OSL = True
WITH_BF_STATICOSL = True
BF_OSL = '${LIBDIR}/osl'
BF_OSL_INC = '${BF_OSL}/include'
BF_OSL_LIBPATH = '${BF_OSL}/lib'
BF_OSL_LIB_STATIC = '${BF_OSL_LIBPATH}/oslcomp.lib ${BF_OSL_LIBPATH}/oslexec.lib ${BF_OSL_LIBPATH}/oslquery.lib '
BF_OSL_COMPILER = '${BF_OSL}/bin/oslc'

WITH_BF_LLVM = True
BF_LLVM = LIBDIR + '/llvm'
BF_LLVM_LIB = 'LLVMBitReader LLVMJIT LLVMipo LLVMVectorize LLVMBitWriter LLVMX86CodeGen LLVMX86Desc LLVMX86Info LLVMX86AsmPrinter ' + \
    'LLVMX86Utils LLVMSelectionDAG LLVMCodeGen LLVMScalarOpts LLVMInstCombine LLVMTransformUtils LLVMipa LLVMAnalysis LLVMExecutionEngine ' + \
    'LLVMTarget LLVMMC LLVMCore LLVMObject LLVMRuntimeDyld LLVMSupport'
BF_LLVM_LIBPATH = '${BF_LLVM}/lib'

WITH_BF_OIIO = True
BF_OIIO = '${LIBDIR}/openimageio'
BF_OIIO_INC = '${BF_OIIO}/include'
BF_OIIO_LIBPATH = '${BF_OIIO}/lib'
BF_OIIO_LIB_STATIC = '${BF_OIIO_LIBPATH}/OpenImageIO.lib'
WITH_BF_STATICOIIO = True

WITH_BF_OCIO = True
BF_OCIO = '${LIBDIR}/opencolorio'
BF_OCIO_INC = '${BF_OCIO}/include'
BF_OCIO_LIBPATH = '${BF_OCIO}/lib'
BF_OCIO_LIB_STATIC = '${BF_OCIO_LIBPATH}/OpenColorIO.lib'
WITH_BF_STATICOCIO = True

WITH_BF_BOOST = True
BF_BOOST = '${LIBDIR}/boost'
BF_BOOST_INC = '${BF_BOOST}/include'
if VC_VERSION == '11.0':
    BF_BOOST_LIB = 'libboost_date_time-vc110-mt-s-1_53 libboost_filesystem-vc110-mt-s-1_53 libboost_regex-vc110-mt-s-1_53 libboost_system-vc110-mt-s-1_53 libboost_thread-vc110-mt-s-1_53 libboost_wave-vc110-mt-s-1_53'
    BF_BOOST_LIB_INTERNATIONAL = ' libboost_locale-vc110-mt-s-1_53'
else:
    BF_BOOST_LIB = 'libboost_date_time-vc90-mt-s-1_49 libboost_filesystem-vc90-mt-s-1_49 libboost_regex-vc90-mt-s-1_49 libboost_system-vc90-mt-s-1_49 libboost_thread-vc90-mt-s-1_49 libboost_wave-vc90-mt-s-1_49'
    BF_BOOST_LIB_INTERNATIONAL = 'libboost_locale-vc90-mt-s-1_49'
BF_BOOST_LIBPATH = '${BF_BOOST}/lib'

#CUDA
WITH_BF_CYCLES_CUDA_BINARIES = False
#BF_CYCLES_CUDA_NVCC = "" # Path to the nvidia compiler

# Workaround for ptxas.exe crash on VS2012 and cuda 5.5
if VC_VERSION == '11.0':
	BF_CYCLES_CUDA_BINARIES_ARCH = ['sm_20', 'sm_21', 'sm_30']
else:
	BF_CYCLES_CUDA_BINARIES_ARCH = ['sm_20', 'sm_21', 'sm_30', 'sm_35']

#Ray trace optimization
WITH_BF_RAYOPTIMIZATION = True
BF_RAYOPTIMIZATION_SSE_FLAGS = ['/arch:SSE']

#Freestyle
WITH_BF_FREESTYLE = True

WITH_BF_STATICOPENGL = False
BF_OPENGL_INC = '${BF_OPENGL}/include'
BF_OPENGL_LIBINC = '${BF_OPENGL}/lib'
BF_OPENGL_LIB = 'opengl32 glu32'
BF_OPENGL_LIB_STATIC = [ '${BF_OPENGL}/lib/libGL.a', '${BF_OPENGL}/lib/libGLU.a',
                         '${BF_OPENGL}/lib/libXmu.a', '${BF_OPENGL}/lib/libXext.a',
                         '${BF_OPENGL}/lib/libX11.a', '${BF_OPENGL}/lib/libXi.a' ]
                         
CC = 'cl.exe'
CXX = 'cl.exe'

CCFLAGS = ['/nologo', '/J', '/W1', '/Gd', '/wd4018', '/wd4244', '/wd4305', '/wd4800', '/wd4065', '/wd4267', '/we4013']
CXXFLAGS = ['/EHsc']
BGE_CXXFLAGS = ['/O2', '/Ob2', '/EHsc', '/GR', '/fp:fast', '/arch:SSE']

BF_DEBUG_CCFLAGS = ['/Zi', '/Ob0', '/Od', '/FR${TARGET}.sbr']

CPPFLAGS = ['-DWIN32','-D_CONSOLE', '-D_LIB', '-D_CRT_SECURE_NO_DEPRECATE', '-DOPJ_STATIC']
REL_CFLAGS = []
REL_CXXFLAGS = []
REL_CCFLAGS = ['-O2', '/Ob2', '-DNDEBUG']

C_WARN = []
CC_WARN = []
CXX_WARN = []

LLIBS = ['ws2_32', 'vfw32', 'winmm', 'kernel32', 'user32', 'gdi32', 'comdlg32', 'advapi32', 'shfolder', 'shell32', 'ole32', 'oleaut32', 'uuid', 'psapi']

PLATFORM_LINKFLAGS = ['/SUBSYSTEM:CONSOLE','/MACHINE:IX86','/STACK:2097152','/INCREMENTAL:NO', '/LARGEADDRESSAWARE', '/NODEFAULTLIB:msvcrt.lib', '/NODEFAULTLIB:msvcmrt.lib', '/NODEFAULTLIB:msvcurt.lib', '/NODEFAULTLIB:msvcrtd.lib']

# # Todo
# BF_PROFILE_CCFLAGS = ['-pg', '-g ']
# BF_PROFILE_LINKFLAGS = ['-pg']
# BF_PROFILE = False

BF_BSC=False

if VC_VERSION == '11.0':
    BF_BUILDDIR = '..\\build\\win32-vc11'
    BF_INSTALLDIR='..\\install\\win32-vc11'
else:
    BF_BUILDDIR = '..\\build\\win32-vc'
    BF_INSTALLDIR='..\\install\\win32-vc'
