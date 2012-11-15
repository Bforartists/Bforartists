BF_BUILDDIR = '../blender-build/linux-glibc27-i686'
BF_INSTALLDIR = '../blender-install/linux-glibc27-i686'
BF_NUMJOBS = 2

# Python configuration
BF_PYTHON_VERSION = '3.3'
BF_PYTHON_ABI_FLAGS = 'm'
BF_PYTHON = '/opt/python3'

WITH_BF_STATICPYTHON = True

# OpenCollada configuration
WITH_BF_COLLADA = True
BF_OPENCOLLADA = '/opt/opencollada'
BF_OPENCOLLADA_INC = '${BF_OPENCOLLADA}/include'
BF_OPENCOLLADA_LIB = 'OpenCOLLADAStreamWriter OpenCOLLADASaxFrameworkLoader OpenCOLLADAFramework OpenCOLLADABaseUtils GeneratedSaxParser UTF MathMLSolver buffer ftoa libxml2-static libexpat-static libpcre-static'
BF_OPENCOLLADA_LIBPATH = '${BF_OPENCOLLADA}/lib /home/sources/staticlibs/lib32'
BF_PCRE_LIB = ''
BF_EXPAT_LIB = ''

# FFMPEG configuration
WITH_BF_FFMPEG = True
WITH_BF_STATICFFMPEG = True

BF_FFMPEG = '/home/sources/staticlibs/ffmpeg'
BF_FFMPEG_LIBPATH = '${BF_FFMPEG}/lib32'
BF_FFMPEG_LIB_STATIC = '${BF_FFMPEG_LIBPATH}/libavformat.a ${BF_FFMPEG_LIBPATH}/libswscale.a ' + \
    '${BF_FFMPEG_LIBPATH}/libavcodec.a ${BF_FFMPEG_LIBPATH}/libavdevice.a ${BF_FFMPEG_LIBPATH}/libavutil.a ' + \
    '${BF_FFMPEG_LIBPATH}/libxvidcore.a ${BF_FFMPEG_LIBPATH}/libx264.a ${BF_FFMPEG_LIBPATH}/libmp3lame.a ' + \
    '${BF_FFMPEG_LIBPATH}/libvpx.a ${BF_FFMPEG_LIBPATH}/libvorbis.a ${BF_FFMPEG_LIBPATH}/libogg.a ' + \
    '${BF_FFMPEG_LIBPATH}/libvorbisenc.a ${BF_FFMPEG_LIBPATH}/libtheora.a ' + \
    '${BF_FFMPEG_LIBPATH}/libschroedinger-1.0.a ${BF_FFMPEG_LIBPATH}/liborc-0.4.a ${BF_FFMPEG_LIBPATH}/libdirac_encoder.a ' + \
    '${BF_FFMPEG_LIBPATH}/libfaad.a'

# Don't depend on system's libstdc++
WITH_BF_STATICCXX = True
BF_CXX_LIB_STATIC = '/usr/lib/gcc/i486-linux-gnu/4.3.4/libstdc++.a'

WITH_BF_OPENAL = True
WITH_BF_STATICOPENAL = True
BF_OPENAL_LIB_STATIC = '/opt/openal/lib/libopenal.a'

WITH_BF_GETTEXT_STATIC = True
BF_FREETYPE_LIB_STATIC = True

WITH_BF_OPENEXR = True
WITH_BF_STATICOPENEXR = True

WITH_BF_TIFF = True
WITH_BF_STATICTIFF = True
BF_TIFF_LIB_STATIC = '${BF_TIFF}/lib/libtiff.a'

WITH_BF_JPEG = True
BF_JPEG_LIB = 'libjpeg'
BF_JPEG_LIBPATH = '/home/sources/staticlibs/lib32'

WITH_BF_PNG = True
BF_PNG_LIB = 'libpng'
BF_PNG_LIBPATH = '/home/sources/staticlibs/lib32'

WITH_BF_STATICLIBSAMPLERATE = True

WITH_BF_ZLIB = True
WITH_BF_STATICZLIB = True
BF_ZLIB_LIB_STATIC = '${BF_ZLIB}/lib/libz.a'

WITH_BF_SDL = True
WITH_BF_OGG = True

WITH_BF_OPENMP = True

WITH_BF_GAMEENGINE = True
WITH_BF_BULLET = True

# Blender player (would be enabled in it's own config)
WITH_BF_PLAYER = False

# Use jemalloc memory manager
WITH_BF_JEMALLOC = True
WITH_BF_STATICJEMALLOC = True
BF_JEMALLOC = '/home/sources/staticlibs/jemalloc'
BF_JEMALLOC_LIBPATH = '${BF_JEMALLOC}/lib32'

# Use 3d mouse library
WITH_BF_3DMOUSE = True
WITH_BF_STATIC3DMOUSE = True
BF_3DMOUSE = '/home/sources/staticlibs/spnav'
BF_3DMOUSE_LIBPATH = '${BF_3DMOUSE}/lib32'

# FFT
WITH_BF_FFTW3 = True
WITH_BF_STATICFFTW3 = True

# JACK
WITH_BF_JACK = True

# Cycles
WITH_BF_CYCLES = True
WITH_BF_CYCLES_CUDA_BINARIES = True
#BF_CYCLES_CUDA_BINARIES_ARCH = ['sm_13', 'sm_20', 'sm_21', 'sm_30']
BF_CYCLES_CUDA_BINARIES_ARCH = ['sm_20', 'sm_21', 'sm_30']

WITH_BF_OIIO = True
WITH_BF_STATICOIIO = True
BF_OIIO = '/opt/oiio'
BF_OIIO_INC = '${BF_OIIO}/include'
BF_OIIO_LIB_STATIC = '${BF_OIIO_LIBPATH}/libOpenImageIO.a ${BF_OPENEXR}/lib/libIlmImf.a'
BF_OIIO_LIBPATH = '${BF_OIIO}/lib'

WITH_BF_CYCLES_OSL = False
WITH_BF_STATICOSL = False
BF_OSL = '/opt/osl'
BF_OSL_INC = '${BF_OSL}/include'
# note oslexec would passed via program linkflags, which is needed to
# make llvm happy with osl_allocate_closure_component
BF_OSL_LIB = 'oslcomp oslexec oslquery'
BF_OSL_LIBPATH = '${BF_OSL}/lib'
BF_OSL_COMPILER = '${BF_OSL}/bin/oslc'

WITH_BF_LLVM = False
WITH_BF_STATICLLVM = False
BF_LLVM = '/opt/llvm-3.1'
BF_LLVM_LIB = 'LLVMBitReader LLVMJIT LLVMipo LLVMVectorize LLVMBitWriter LLVMX86CodeGen LLVMX86Desc LLVMX86Info LLVMX86AsmPrinter ' + \
    'LLVMX86Utils LLVMSelectionDAG LLVMCodeGen LLVMScalarOpts LLVMInstCombine LLVMTransformUtils LLVMipa LLVMAnalysis LLVMExecutionEngine ' + \
    'LLVMTarget LLVMMC LLVMCore LLVMSupport'
BF_LLVM_LIBPATH = '${BF_LLVM}/lib'

# Color management
WITH_BF_OCIO = True
WITH_BF_STATICOCIO = True
BF_OCIO = '/opt/ocio'
BF_OCIO_INC = '${BF_OCIO}/include'
BF_OCIO_LIB_STATIC = '${BF_OCIO_LIBPATH}/libOpenColorIO.a ${BF_OCIO_LIBPATH}/libtinyxml.a ${BF_OCIO_LIBPATH}/libyaml-cpp.a'
BF_OCIO_LIBPATH = '${BF_OCIO}/lib'

WITH_BF_BOOST = True
WITH_BF_STATICBOOST = True
BF_BOOST = '/opt/boost'
BF_BOOST_INC = '${BF_BOOST}/include'
BF_BOOST_LIB_STATIC = '${BF_BOOST_LIBPATH}/libboost_filesystem.a ${BF_BOOST_LIBPATH}/libboost_date_time.a ${BF_BOOST_LIBPATH}/libboost_regex.a ${BF_BOOST_LIBPATH}/libboost_locale.a ${BF_BOOST_LIBPATH}/libboost_system.a ${BF_BOOST_LIBPATH}/libboost_thread.a'
BF_BOOST_LIBPATH = '${BF_BOOST}/lib'

# Ocean Simulation
WITH_BF_OCEANSIM = True

# Compilation and optimization
BF_DEBUG = False
REL_CCFLAGS = ['-O2']  # C & C++
PLATFORM_LINKFLAGS = ['-L/home/sources/staticlibs/lib32']
BF_PROGRAM_LINKFLAGS = ['-Wl,--whole-archive', '-loslexec', '-Wl,--no-whole-archive']
