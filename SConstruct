import string
import os
import sys
from distutils import sysconfig

# Build directory.
root_build_dir = '..' + os.sep + 'build' + os.sep

# Blender version.
config_file = 'config.opts'
version='2.32'

sdl_cenv = Environment ()
sdl_lenv = Environment ()
link_env = Environment ()
env = Environment ()

if sys.platform == 'linux2':
    use_international = 'false'
    use_gameengine = 'false'
    use_openal = 'false'
    use_fmod = 'false'
    use_quicktime = 'false'
    use_sumo = 'false'
    use_ode = 'false'
    release_flags = ['-O2']
    debug_flags = ['-O2', '-g']
    extra_flags = ['-pipe', '-fPIC', '-funsigned-char']
    cxxflags = []
    defines = []
    warn_flags = ['-Wall', '-W']
    window_system = 'X11'
    platform_libs = ['m', 'z', 'GL', 'GLU', 'png', 'jpeg', 'util']
    platform_libpath = []
    platform_linkflags = []
    extra_includes = []
    # SDL specific stuff.
    sdl_cenv.ParseConfig ('sdl-config --cflags')
    sdl_lenv.ParseConfig ('sdl-config --libs')
    sdl_cdict = sdl_cenv.Dictionary()
    sdl_ldict = sdl_lenv.Dictionary()
    sdl_cflags = string.join(sdl_cdict['CCFLAGS'])
    sdl_include = sdl_cdict['CPPPATH'][0]
    link_env.Append (LIBS=sdl_ldict['LIBS'])
    link_env.Append (LIBPATH=sdl_ldict['LIBPATH'])
    solid_include = '#extern/solid/include'
    ode_include = '#extern/ode/dist/include/ode'
    # Python variables.
    python_include = sysconfig.get_python_inc ()
    python_libpath = sysconfig.get_python_lib (0, 1) + '/config'
    python_lib = 'python%d.%d' % sys.version_info[0:2]
    # International stuff
    if (use_international == 'true'):
        defines += ['INTERNATIONAL', 'FTGL_STATIC_LIBRARY', 'WITH_FREETYPE2']
        platform_libpath += ['#../lib/linux-glibc2.2.5-i386/ftgl/lib',
                             '#../lib/linux-glibc2.2.5-i386/freetype/lib']
        platform_libs += ['ftgl', 'freetype']
        extra_includes += ['#../lib/linux-glibc2.2.5-i386/ftgl/include',
                           '#../lib/linux-glibc2.2.5-i386/freetype/include']

elif sys.platform == 'darwin':
    use_international = 'false'
    use_gameengine = 'false'
    use_openal = 'false'
    use_fmod = 'false'
    use_quicktime = 'true'
    use_precomp = 'true'
    use_sumo = 'false'
    use_ode = 'false'
    # TODO: replace darwin-6.8-powerpc with the actual directiory on the
    #       build machine
    darwin_precomp = '#../lib/darwin-6.8-powerpc'
    extra_flags = ['-pipe', '-fPIC', '-funsigned-char']
    cxxflags = []
    defines = ['_THREAD_SAFE']
    if use_quicktime == 'true':
        defines += ['WITH_QUICKTIME']
    warn_flags = ['-Wall', '-W']
    release_flags = []
    debug_flags = ['-g']
    window_system = 'CARBON'
    # SDL specific stuff.
    sdl_cenv.ParseConfig ('sdl-config --cflags')
    sdl_lenv.ParseConfig ('sdl-config --libs')
    sdl_cdict = sdl_cenv.Dictionary()
    sdl_ldict = sdl_lenv.Dictionary()
    sdl_cflags = string.join(sdl_cdict['CCFLAGS'])
    # Want to use precompiled libraries?
    if use_precomp == 'true':
        sdl_ldict['LIBS'] = ['libSDL.a']
        sdl_ldict['LIBPATH'] = [darwin_precomp + '/sdl/lib']
        sdl_cdict['CPPPATH'] = [darwin_precomp + '/sdl/include']

    sdl_include = sdl_cdict['CPPPATH'][0]
    link_env.Append (LIBS=sdl_ldict['LIBS'])
    link_env.Append (LIBPATH=sdl_ldict['LIBPATH'])
    platform_libs = ['z', 'GL', 'GLU', 'png', 'jpeg', 'stdc++'] 
    extra_includes = ['/sw/include']
    platform_libpath = ['/System/Library/Frameworks/OpenGL.framework/Libraries']
    platform_linkflags = []
    # Python variables.
    python_lib = 'python%d.%d' % sys.version_info[0:2]
    python_libpath = sysconfig.get_python_lib (0, 1) + '/config'
    python_include = sysconfig.get_python_inc ()

elif sys.platform == 'cygwin':
    use_international = 'false'
    use_gameengine = 'false'
    use_openal = 'false'
    use_fmod = 'false'
    use_quicktime = 'false'
    use_sumo = 'false'
    use_ode = 'false'
    release_flags = ['-O2']
    debug_flags = ['-O2', '-g']
    extra_flags = ['-pipe', '-mno-cygwin', '-mwindows', '-funsigned-char']
    defines = ['FREE_WINDOWS', 'NDEBUG']
    cxxflags = []
    warn_flags = ['-Wall', '-Wno-char-subscripts']
    platform_libs = ['png', 'jpeg', 'netapi32',
                     'opengl32', 'glu32', 'winmm',
                     'mingw32', 'z']
    platform_libpath = ['/usr/lib/w32api', '/lib/w32api']
    platform_linkflags = ['-mwindows', '-mno-cygwin', '-mconsole']
    window_system = 'WIN32'
    extra_includes = ['/usr/include']
    # SDL specific stuff.
    sdl_cenv.ParseConfig ('sdl-config --cflags')
    sdl_lenv.ParseConfig ('sdl-config --libs')
    sdl_cdict = sdl_cenv.Dictionary()
    sdl_ldict = sdl_lenv.Dictionary()
    sdl_cflags = '-DWIN32'
    sdl_include = sdl_cdict['CPPPATH'][0]
    link_env.Append (LIBS=sdl_ldict['LIBS'])
    link_env.Append (LIBPATH=sdl_ldict['LIBPATH'])
    # We need to force the Cygwin environment to use the g++ linker.
    link_env.Replace (CC='g++')
    # Python variables.
    python_include = sysconfig.get_python_inc ()
    python_libpath = sysconfig.get_python_lib (0, 1) + '/config'
    python_lib = 'python%d.%d' % sys.version_info[0:2]

elif sys.platform == 'win32':
    use_international = 'true'
    use_gameengine = 'true'
    use_openal = 'true'
    use_fmod = 'false'
    use_quicktime = 'true'
    use_sumo = 'false'
    use_ode = 'true'
    release_flags = ['/G6', '/GF']
    debug_flags = ['/Zi']
    extra_flags = ['/EHsc', '/J', '/W3', '/Gd', '/MT']
    cxxflags = []
    defines = ['WIN32', '_CONSOLE', 'FTGL_STATIC_LIBRARY']
    defines += ['INTERNATIONAL', 'WITH_QUICKTIME']
    defines += ['_LIB', 'WITH_FREETYPE2', 'USE_OPENAL']
    warn_flags = []
    platform_libs = ['SDL', 'freetype2ST', 'ftgl_static_ST', 'gnu_gettext',
                     'qtmlClient', 'odelib', 'openal_static', 'soundsystem',
                     'ws2_32', 'dxguid', 'opengl32', 'libjpeg', 'glu32',
                     'vfw32', 'winmm', 'libpng_st', 'libz_st', 'solid',
                     'qhull', 'iconv', 'kernel32', 'user32', 'gdi32',
                     'winspool', 'comdlg32', 'advapi32', 'shell32',
                     'ole32', 'oleaut32', 'uuid', 'odbc32', 'odbccp32',
                     'libcmt', 'libc']
    platform_libpath = ['#../lib/windows/ftgl/lib',
                        '#../lib/windows/freetype/lib',
                        '#../lib/windows/gettext/lib',
                        '#../lib/windows/iconv/lib',
                        '#../lib/windows/jpeg/lib',
                        '#../lib/windows/QTDevWin/Libraries',
                        '#../lib/windows/ode/lib',
                        '#../lib/windows/openal/lib',
                        '#../lib/windows/png/lib',
                        '#../lib/windows/zlib/lib',
                        '#../lib/windows/solid/lib',
                        '#../lib/windows/qhull/lib',
                        '#../lib/windows/sdl/lib']
    platform_linkflags = [
                        '/SUBSYSTEM:CONSOLE',
                        '/MACHINE:IX86',
                        '/ENTRY:mainCRTStartup',
                        '/INCREMENTAL:NO',
                        '/NODEFAULTLIB:"msvcprt.lib"',
                        '/NODEFAULTLIB:"glut32.lib"',
                        '/NODEFAULTLIB:"libcd.lib"',
                        #'/NODEFAULTLIB:"libc.lib"',
                        '/NODEFAULTLIB:"libcpd.lib"',
                        '/NODEFAULTLIB:"libcp.lib"',
                        '/NODEFAULTLIB:"libcmtd.lib"',
                        ]
    window_system = 'WIN32'
    extra_includes = ['#../lib/windows/zlib/include',
                      '#../lib/windows/jpeg/include',
                      '#../lib/windows/png/include']
    if use_international == 'true':
        extra_includes += ['#../lib/windows/ftgl/include',
                           '#../lib/windows/freetype/include',
                           '#../lib/windows/gettext/include']
    if use_quicktime == 'true':
        extra_includes += ['#../lib/windows/QTDevWin/CIncludes']
    if use_openal == 'true':
        extra_includes += ['#../lib/windows/openal/include']
    sdl_include = '#../lib/windows/sdl/include'
    sdl_cflags = ''
    link_env.RES(['source/icons/winblender.rc'])
    window_system = 'WIN32'
    solid_include = '#../lib/windows/solid/include'
    ode_include = '#../lib/windows/ode/include'
    # Python lib name
    python_include = '#../lib/windows/python/include/python2.2'
    python_libpath = '#../lib/windows/python/lib'
    python_lib = 'python22'

elif string.find (sys.platform, 'sunos') != -1:
    use_international = 'true'
    use_gameengine = 'false'
    use_openal = 'false'
    use_fmod = 'false'
    use_quicktime = 'false'
    use_sumo = 'false'
    use_ode = 'false'
    release_flags = ['-O2']
    debug_flags = ['-O2', '-g']
    extra_flags = ['-pipe', '-fPIC', '-funsigned-char']
    cxxflags = []
    defines = []
    env['ENV']['CC']='gcc'
    env['ENV']['CXX']='g++'
    warn_flags = ['-Wall', '-W']
    window_system = 'X11'
    platform_libs = ['m', 'z', 'GL', 'GLU', 'png', 'jpeg', 'util']
    platform_libpath = []
    platform_linkflags = []
    extra_includes = []
    # SDL specific stuff.
    sdl_cenv.ParseConfig ('sdl-config --cflags')
    sdl_lenv.ParseConfig ('sdl-config --libs')
    sdl_cdict = sdl_cenv.Dictionary()
    sdl_ldict = sdl_lenv.Dictionary()
    sdl_cflags = string.join(sdl_cdict['CCFLAGS'])
    sdl_include = sdl_cdict['CPPPATH'][0]
    link_env.Append (LIBS=sdl_ldict['LIBS'])
    link_env.Append (LIBPATH=sdl_ldict['LIBPATH'])
    solid_include = '#extern/solid/include'
    ode_include = '#extern/ode/dist/include/ode'
    # Python variables.
    python_include = sysconfig.get_python_inc ()
    python_libpath = sysconfig.get_python_lib (0, 1) + '/config'
    python_lib = 'python%d.%d' % sys.version_info[0:2]
    # International stuff
    if (use_international == 'true'):
        defines += ['INTERNATIONAL', 'FTGL_STATIC_LIBRARY', 'WITH_FREETYPE2']
        platform_libpath += ['#../lib/solaris-2.8-sparc/ftgl',
                             '#../lib/solaris-2.8-sparc/freetype/lib']
        platform_libs += ['ftgl', 'freetype']
        extra_includes += ['#../lib/solaris-2.8-sparc/ftgl/include',
                           '#../lib/solaris-2.8-sparc/freetype/include']


elif string.find (sys.platform, 'irix') != -1:
    use_international = 'false'
    use_gameengine = 'false'
    use_openal = 'false'
    use_fmod = 'false'
    use_quicktime = 'false'
    use_sumo = 'false'
    use_ode = 'false'
    irix_precomp = '#../lib/irix-6.5-mips'
    extra_flags = ['-n32', '-mips3', '-Xcpluscomm']
    cxxflags = ['-n32', '-mips3', '-Xcpluscomm', '-LANG:std']
    cxxflags += ['-LANG:libc_in_namespace_std=off']
    
    window_system = 'X11'
    release_flags = ['-O2', '-OPT:Olimit=0']
    debug_flags = ['-O2', '-g']
    defines = []
    warn_flags = ['-fullwarn', '-woff', '1001,1110,1201,1209,1355,1424,1681,3201']
    sdl_cflags = ''
    sdl_include = irix_precomp + '/sdl/include/SDL'
    link_env.Append (LIBS=['libSDL.a'])
    link_env.Append (LIBPATH=['/usr/lib32/mips3', irix_precomp + '/sdl/lib'])
    python_libpath = irix_precomp + '/python/lib/python2.2/config'
    python_include = irix_precomp + '/python/include/python2.2'
    python_lib = 'python2.2'

    platform_libs = ['SDL', 'movieGL', 'GLU', 'GL', 'Xmu', 'Xext', 'X11',
                     'c', 'm', 'dmedia', 'cl', 'audio',
                     'Cio', 'png', 'jpeg', 'z', 'pthread']
    platform_libpath = [irix_precomp + '/png/lib',
                        irix_precomp + '/jpeg/lib',
                        '/usr/lib32', '/lib/freeware/lib32']
    platform_linkflags = ['-mips3', '-n32']
    extra_includes = [irix_precomp + '/jpeg/include',
                      irix_precomp + '/png/include',
                      '/usr/freeware/include',
                      '/usr/include']
    solid_include = irix_precomp + '/solid/include'
    ode_include = irix_precomp + '/ode/include'


elif string.find (sys.platform, 'hp-ux') != -1:
    window_system = 'X11'
    defines = []

else:
    print "Unknown platform"

#-----------------------------------------------------------------------------
# End of platform specific section
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# User configurable options to be saved in a config file.
#-----------------------------------------------------------------------------
# Checking for an existing config file - use that one if it exists,
# otherwise create one.
if os.path.exists (config_file):
    print "Using config file: " + config_file
else:
    print "Creating new config file: " + config_file
    config=open (config_file, 'w')
    config.write ("# Configuration file containing user definable options.\n")
    config.write ("VERSION = '2.32-cvs'\n")
    config.write ("BUILD_BINARY = 'release'\n")
    config.write ("BUILD_DIR = '%s'\n"%(root_build_dir))
    config.write ("USE_INTERNATIONAL = '%s'\n"%(use_international))
    config.write ("BUILD_GAMEENGINE = '%s'\n"%(use_gameengine))
    if use_sumo == 'true':
        config.write ("USE_PHYSICS = 'solid'\n")
    else:
        config.write ("USE_PHYSICS = 'ode'\n")
    config.write ("USE_OPENAL = '%s'\n"%(use_openal))
    config.write ("USE_FMOD = '%s'\n"%(use_fmod))
    config.write ("USE_QUICKTIME = '%s'\n"%(use_quicktime))
    config.close ()

#-----------------------------------------------------------------------------
# Read the options from the config file and update the various necessary flags
#-----------------------------------------------------------------------------
user_options_env = Environment ()
user_options = Options (config_file)
user_options.AddOptions (
        ('VERSION', 'Blender version', version),
        ('BUILD_DIR', 'Target directory for intermediate files.',
                     root_build_dir),
        (BoolOption ('USE_INTERNATIONAL',
                     'Set to 1 to have international support.',
                     'false')),
        (EnumOption ('USE_PHYSICS', 'solid',
                     'Select which physics engine to use.',
                     allowed_values = ('ode', 'solid'))),
        (BoolOption ('BUILD_GAMEENGINE',
                     'Set to 1 to build blender with game engine support.',
                     'false')),
        (BoolOption ('USE_OPENAL',
                     'Set to 1 to build the game engine with OpenAL support.',
                     'false')),
        (BoolOption ('USE_FMOD',
                     'Set to 1 to build the game engine with FMod support.',
                     'false')),
        (BoolOption ('USE_QUICKTIME',
                     'Set to 1 to add support for QuickTime.',
                     'false')),
        (EnumOption ('BUILD_BINARY', 'release',
                     'Select a release or debug binary.',
                     allowed_values = ('release', 'debug'))),
    )
user_options.Update (user_options_env)
user_options_dict = user_options_env.Dictionary()

root_build_dir = user_options_dict['BUILD_DIR']
    
if user_options_dict['BUILD_GAMEENGINE'] == 1:
    defines += ['GAMEBLENDER=1']
    if user_options_dict['USE_PHYSICS'] == 'ode':
        defines += ['USE_ODE']
    else:
        defines += ['USE_SUMO_SOLID']
else:
    defines += ['GAMEBLENDER=0']

if user_options_dict['BUILD_BINARY'] == 'release':
    cflags = extra_flags + release_flags + warn_flags
    if sys.platform == 'win32':
        defines += ['NDEBUG']
else:
    cflags = extra_flags + debug_flags + warn_flags
    if sys.platform == 'win32':
        #defines += ['_DEBUG'] specifying this makes msvc want to link to python22_d.lib??
        platform_linkflags += ['/DEBUG','/PDB:blender.pdb']


#-----------------------------------------------------------------------------
# Settings to be exported to other SConscript files
#-----------------------------------------------------------------------------
#cflags = extra_flags + release_flags + warn_flags

Export ('python_include')
Export ('cflags')
Export ('defines')
Export ('cxxflags')
Export ('window_system')
Export ('sdl_cflags')
Export ('sdl_include')
Export ('solid_include')
Export ('ode_include')
Export ('extra_includes')
Export ('platform_libs')
Export ('platform_libpath')
Export ('platform_linkflags')
Export ('root_build_dir')
Export ('user_options_dict')

BuildDir (root_build_dir+'/intern', 'intern', duplicate=0)
SConscript (root_build_dir+'intern/SConscript')
BuildDir (root_build_dir+'/source', 'source', duplicate=0)
SConscript (root_build_dir+'source/SConscript')

libpath = (['#'+root_build_dir+'/lib'])

libraries = (['blender_render',
              'blender_yafray',
              'blender_blendersrc',
              'blender_renderconverter',
              'blender_blenloader',
              'blender_writestreamglue',
              'blender_deflate',
              'blender_writeblenfile',
              'blender_readblenfile',
              'blender_readstreamglue',
              'blender_inflate',
              'blender_img',
              'blender_radiosity',
              'blender_blenkernel',
              'blender_blenpluginapi',
              'blender_imbuf',
              'blender_avi',
              'blender_blenlib',
              'blender_python',
              'blender_makesdna',
              'blender_kernel',
              'blender_BSP',
              'blender_LOD',
              'blender_GHOST',
              'blender_STR',
              'blender_guardedalloc',
              'blender_BMF',
              'blender_CTR',
              'blender_MEM',
              'blender_IK',
              'blender_MT',
              'soundsystem'])

link_env.Append (LIBS=libraries)
link_env.Append (LIBPATH=libpath)
link_env.Append (CPPDEFINES=defines)

if use_international == 'true':
    link_env.Append (LIBS=['blender_FTF'])
if use_quicktime == 'true':
    link_env.Append (LIBS=['blender_quicktime'])
if use_gameengine == 'true':
    link_env.Append (LIBS=['blender_expressions',
                           'KX_blenderhook',
                           'KX_converter',
                           'KX_ketsji',
                           'KX_network',
                           'NG_loopbacknetwork',
                           'NG_network',
                           'PHY_Physics',
                           'PHY_Dummy',
                           'SCA_GameLogic',
                           'RAS_rasterizer',
                           'RAS_OpenGLRasterizer',
                           'SG_SceneGraph'])
    if use_sumo == 'true':
        link_env.Append (LIBS=['PHY_Sumo'])
    if use_ode == 'true':
        link_env.Append (LIBS=['PHY_Ode'])

link_env.Append (LIBS=python_lib)
link_env.Append (LIBPATH=python_libpath)
link_env.Append (LIBS=platform_libs)
link_env.Append (LIBPATH=platform_libpath)
if sys.platform == 'darwin':
    link_env.Append (LINKFLAGS=' -framework Carbon')
    link_env.Append (LINKFLAGS=' -framework AGL')
    if use_quicktime == 'true':
        link_env.Append (LINKFLAGS=' -framework QuickTime')
else:
    link_env.Append (LINKFLAGS=platform_linkflags)

source_files = [root_build_dir+'source/creator/buildinfo.c',
                root_build_dir+'source/creator/creator.c']

if sys.platform == 'win32':
	source_files += ['source/icons/winblender.res']

include_paths = ['#/intern/guardedalloc',
                 '#/source/blender/makesdna',
                 '#/source/blender/blenkernel',
                 '#/source/blender/blenloader',
                 '#/source/blender/python',
                 '#/source/blender/blenlib',
                 '#/source/blender/renderconverter',
                 '#/source/blender/render/extern/include',
                 '#/source/kernel/gen_messaging',
                 '#/source/kernel/gen_system',
                 '#/source/blender/include',
                 '#/source/blender/imbuf']

link_env.BuildDir (root_build_dir, '.', duplicate=0)
link_env.Append (CPPPATH=include_paths)
link_env.Program (target='blender', source=source_files, CCFLAGS=cflags)

if sys.platform == 'darwin':
    bundle = Environment ()
    blender_app = 'blender'
    bundle.Depends ('#/blender.app/Contents/MacOS/' + blender_app, blender_app)
    bundle.Command ('#/blender.app/Contents/Info.plist',
                    '#/source/darwin/blender.app/Contents/Info.plist',
                    "rm -rf blender.app && " + \
                    "cp -R source/darwin/blender.app . && " +
                    "cat $SOURCE | sed s/VERSION/`cat release/VERSION`/ | \
                                   sed s/DATE/`date +'%Y-%b-%d'`/ \
                                   > $TARGET")
    bundle.Command ('blender.app/Contents/MacOS/' + blender_app, blender_app,
                    'cp $SOURCE $TARGET && ' + \
                    'chmod +x $TARGET && ' + \
                    'find $SOURCE -name CVS -prune -exec rm -rf {} \; && ' +
                    'find $SOURCE -name .DS_Store -exec rm -rf {} \;')
