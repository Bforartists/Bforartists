#!/usr/bin/env python

"""
tools.BlenderEnvironment

This environment builds on SCons.Script.SConscript.SConsEnvironment

* library repository
* custom printout
* wrapper functions

TODO: clean up and sanitise code - crosscheck with btools and SConstruct
to kill any code duplication

"""

import os
import os.path
import string
import glob
import time
import sys

from SCons.Script.SConscript import SConsEnvironment
import SCons.Action
import SCons.Util
import SCons.Builder
import SCons.Tool
import bcolors
bc = bcolors.bcolors()

Split = SCons.Util.Split
Action = SCons.Action.Action
Builder = SCons.Builder.Builder
GetBuildPath = SConsEnvironment.GetBuildPath

# a few globals
root_build_dir = ''
doc_build_dir = ''
quickie = None # Anything else than None if BF_QUICK has been passed
quicklist = [] # The list of libraries/programs to compile during a quickie
program_list = [] # A list holding Nodes to final binaries, used to create installs
arguments = None
targets = None
resources = []

#some internals
blenderdeps = [] # don't manipulate this one outside this module!

##### LIB STUFF ##########

possible_types = ['core'] # can be set in ie. SConstruct
libs = {}
vcp = []

def getresources():
	return resources

def init_lib_dict():
	for pt in possible_types:
		libs[pt] = {}

# helper func for add_lib_to_dict
def internal_lib_to_dict(dict = None, libtype = None, libname = None, priority = 100):
	if not libname in dict[libtype]:
		done = None
		while not done:
			if dict[libtype].has_key(priority):
				priority = priority + 1
			else:
				done = True
		dict[libtype][priority] = libname

# libtype and priority can both be lists, for defining lib in multiple places
def add_lib_to_dict(env, dict = None, libtype = None, libname = None, priority = 100):
	if not dict or not libtype or not libname:
		print "Passed wrong arg"
		env.Exit()

	if type(libtype) is str and type(priority) is int:
		internal_lib_to_dict(dict, libtype, libname, priority)
	elif type(libtype) is list and type(priority) is list:
		if len(libtype)==len(priority):
			for lt, p in zip(libtype, priority):
				internal_lib_to_dict(dict, lt, libname, p)
		else:
			print "libtype and priority lists are unequal in length"
			env.Exit()
	else:
		print "Wrong type combinations for libtype and priority. Only str and int or list and list"
		env.Exit()

def create_blender_liblist(lenv = None, libtype = None):
	if not lenv or not libtype:
		print "missing arg"

	lst = []
	if libtype in possible_types:
		curlib = libs[libtype]
		sortlist = curlib.keys()
		sortlist.sort()
		for sk in sortlist:
			v = curlib[sk]
			target = os.path.abspath(os.getcwd() + os.sep + root_build_dir + 'lib' + os.sep +lenv['LIBPREFIX'] + v + lenv['LIBSUFFIX'])
			lst.append(target)

	return lst

## TODO: static linking
def setup_staticlibs(lenv):
	statlibs = [
		#here libs for static linking
	]
	libincs = [
		lenv['BF_OPENGL_LIBPATH'],
		lenv['BF_JPEG_LIBPATH'],
		lenv['BF_PNG_LIBPATH'],
		lenv['BF_ZLIB_LIBPATH'],
		lenv['BF_LIBSAMPLERATE_LIBPATH'],
		lenv['BF_ICONV_LIBPATH']
		]

	if lenv['OURPLATFORM'] != 'linuxcross':
		libincs = ['/usr/lib'] + libincs

	libincs += Split(lenv['BF_FREETYPE_LIBPATH'])
	if lenv['WITH_BF_PYTHON']:
		libincs += Split(lenv['BF_PYTHON_LIBPATH'])
	if lenv['WITH_BF_SDL']:
		libincs += Split(lenv['BF_SDL_LIBPATH'])
	if lenv['WITH_BF_FFMPEG']:
		libincs += Split(lenv['BF_FFMPEG_LIBPATH'])
	if lenv['WITH_BF_JACK']:
		libincs += Split(lenv['BF_JACK_LIBPATH'])
	if lenv['WITH_BF_OPENEXR']:
		libincs += Split(lenv['BF_OPENEXR_LIBPATH'])
		if lenv['WITH_BF_STATICOPENEXR']:
			statlibs += Split(lenv['BF_OPENEXR_LIB_STATIC'])
	if lenv['WITH_BF_FFTW3']:
		libincs += Split(lenv['BF_FFTW3_LIBPATH'])
	if lenv['WITH_BF_INTERNATIONAL']:
		libincs += Split(lenv['BF_GETTEXT_LIBPATH'])
	if lenv['WITH_BF_OPENAL']:
		libincs += Split(lenv['BF_OPENAL_LIBPATH'])
		if lenv['WITH_BF_STATICOPENAL']:
			statlibs += Split(lenv['BF_OPENAL_LIB_STATIC'])
	if lenv['WITH_BF_STATICOPENGL']:
		statlibs += Split(lenv['BF_OPENGL_LIB_STATIC'])
	if lenv['WITH_BF_STATICCXX']:
		statlibs += Split(lenv['BF_CXX_LIB_STATIC'])

	if lenv['WITH_BF_PYTHON'] and lenv['WITH_BF_STATICPYTHON']:
		statlibs += Split(lenv['BF_PYTHON_LIB_STATIC'])

	if lenv['OURPLATFORM'] in ('win32-vc', 'win32-mingw', 'linuxcross', 'win64-vc'):
		libincs += Split(lenv['BF_PTHREADS_LIBPATH'])

	return statlibs, libincs

def setup_syslibs(lenv):
	syslibs = [
		
		lenv['BF_JPEG_LIB'],
		lenv['BF_PNG_LIB'],
		lenv['BF_ZLIB_LIB'],
		lenv['BF_LIBSAMPLERATE_LIB']
		]

	syslibs += Split(lenv['BF_FREETYPE_LIB'])
	if lenv['WITH_BF_UNIT_TEST']:
		syslibs.append(lenv['BF_CHECK_LIB'])
	if lenv['WITH_BF_PYTHON'] and not lenv['WITH_BF_STATICPYTHON']:
		if lenv['BF_DEBUG'] and lenv['OURPLATFORM'] in ('win32-vc', 'win64-vc'):
			syslibs.append(lenv['BF_PYTHON_LIB']+'_d')
		else:
			syslibs.append(lenv['BF_PYTHON_LIB'])
	if lenv['WITH_BF_INTERNATIONAL']:
		syslibs += Split(lenv['BF_GETTEXT_LIB'])
	if lenv['WITH_BF_OPENAL']:
		if not lenv['WITH_BF_STATICOPENAL']:
			syslibs += Split(lenv['BF_OPENAL_LIB'])
	if lenv['WITH_BF_OPENMP'] and lenv['CC'] != 'icc':
		if lenv['CC'] == 'cl.exe':
			syslibs += ['vcomp']
		else:
			syslibs += ['gomp']
	if lenv['WITH_BF_ICONV']:
		syslibs += Split(lenv['BF_ICONV_LIB'])
	if lenv['WITH_BF_OPENEXR']:
		if not lenv['WITH_BF_STATICOPENEXR']:
			syslibs += Split(lenv['BF_OPENEXR_LIB'])
	if lenv['WITH_BF_FFMPEG']:
		syslibs += Split(lenv['BF_FFMPEG_LIB'])
		if lenv['WITH_BF_OGG']:
			syslibs += Split(lenv['BF_OGG_LIB'])
	if lenv['WITH_BF_JACK']:
			syslibs += Split(lenv['BF_JACK_LIB'])
	if lenv['WITH_BF_FFTW3']:
		syslibs += Split(lenv['BF_FFTW3_LIB'])
	if lenv['WITH_BF_SDL']:
		syslibs += Split(lenv['BF_SDL_LIB'])
	if not lenv['WITH_BF_STATICOPENGL']:
		syslibs += Split(lenv['BF_OPENGL_LIB'])
	if lenv['OURPLATFORM'] in ('win32-vc', 'win32-mingw','linuxcross', 'win64-vc'):
		syslibs += Split(lenv['BF_PTHREADS_LIB'])
	if lenv['WITH_BF_LCMS']:
		syslibs.append(lenv['BF_LCMS_LIB'])


	syslibs += lenv['LLIBS']

	return syslibs

def propose_priorities():
	print bc.OKBLUE+"Priorities:"+bc.ENDC
	for t in possible_types:
		print bc.OKGREEN+"\t"+t+bc.ENDC
		new_priority = 0
		curlib = libs[t]
		sortlist = curlib.keys()
		sortlist.sort()

		for sk in sortlist:
			v = curlib[sk]
			#for p,v in sorted(libs[t].iteritems()):
			print "\t\t",new_priority, v
			new_priority += 5

## TODO: see if this can be made in an emitter
def buildinfo(lenv, build_type):
	"""
	Generate a buildinfo object
	"""
	build_date = time.strftime ("%Y-%m-%d")
	build_time = time.strftime ("%H:%M:%S")
	build_rev = os.popen('svnversion').read()[:-1] # remove \n

	obj = []
	if lenv['BF_BUILDINFO']:
		if sys.platform=='win32' or lenv['OURPLATFORM']=='linuxcross':
			build_info_file = open("source/creator/winbuildinfo.h", 'w')
			build_info_file.write("char *build_date=\"%s\";\n"%build_date)
			build_info_file.write("char *build_time=\"%s\";\n"%build_time)
			build_info_file.write("char *build_rev=\"%s\";\n"%build_rev)
			build_info_file.write("char *build_platform=\"win32\";\n")
			build_info_file.write("char *build_type=\"dynamic\";\n")
			build_info_file.close()
			lenv.Append (CPPDEFINES = ['NAN_BUILDINFO', 'BUILD_DATE'])
		else:
			lenv.Append (CPPDEFINES = ['BUILD_TIME=\'"%s"\''%(build_time),
										'BUILD_DATE=\'"%s"\''%(build_date),
										'BUILD_TYPE=\'"dynamic"\'',
										'BUILD_REV=\'"%s"\''%(build_rev),
										'NAN_BUILDINFO',
										'BUILD_PLATFORM=\'"%s"\''%(sys.platform)])
		obj = [lenv.Object (root_build_dir+'source/creator/%s_buildinfo'%build_type,
						[root_build_dir+'source/creator/buildinfo.c'])]
	return obj

##### END LIB STUFF ############

##### ACTION STUFF #############

def my_compile_print(target, source, env):
	a = '%s' % (source[0])
	d, f = os.path.split(a)
	return bc.OKBLUE+"Compiling"+bc.ENDC +" ==> '"+bc.OKGREEN+"%s" % (f) + "'"+bc.ENDC

def my_moc_print(target, source, env):
	a = '%s' % (source[0])
	d, f = os.path.split(a)
	return bc.OKBLUE+"Creating MOC"+bc.ENDC+ " ==> '"+bc.OKGREEN+"%s" %(f) + "'"+bc.ENDC

def my_linking_print(target, source, env):
	t = '%s' % (target[0])
	d, f = os.path.split(t)
	return bc.OKBLUE+"Linking library"+bc.ENDC +" ==> '"+bc.OKGREEN+"%s" % (f) + "'"+bc.ENDC

def my_program_print(target, source, env):
	t = '%s' % (target[0])
	d, f = os.path.split(t)
	return bc.OKBLUE+"Linking program"+bc.ENDC +" ==> '"+bc.OKGREEN+"%s" % (f) + "'"+bc.ENDC

def msvc_hack(env):
	static_lib = SCons.Tool.createStaticLibBuilder(env)
	program = SCons.Tool.createProgBuilder(env)
	
	env['BUILDERS']['Library'] = static_lib
	env['BUILDERS']['StaticLibrary'] = static_lib
	env['BUILDERS']['Program'] = program
		
def set_quiet_output(env):
	mycaction = Action("$CCCOM", strfunction=my_compile_print)
	myshcaction = Action("$SHCCCOM", strfunction=my_compile_print)
	mycppaction = Action("$CXXCOM", strfunction=my_compile_print)
	myshcppaction = Action("$SHCXXCOM", strfunction=my_compile_print)
	mylibaction = Action("$ARCOM", strfunction=my_linking_print)
	mylinkaction = Action("$LINKCOM", strfunction=my_program_print)

	static_ob, shared_ob = SCons.Tool.createObjBuilders(env)
	static_ob.add_action('.c', mycaction)
	static_ob.add_action('.cpp', mycppaction)
	shared_ob.add_action('.c', myshcaction)
	shared_ob.add_action('.cpp', myshcppaction)

	static_lib = SCons.Builder.Builder(action = mylibaction,
									   emitter = '$LIBEMITTER',
									   prefix = '$LIBPREFIX',
									   suffix = '$LIBSUFFIX',
									   src_suffix = '$OBJSUFFIX',
									   src_builder = 'StaticObject')

	program = SCons.Builder.Builder(action = mylinkaction,
									emitter = '$PROGEMITTER',
									prefix = '$PROGPREFIX',
									suffix = '$PROGSUFFIX',
									src_suffix = '$OBJSUFFIX',
									src_builder = 'Object',
									target_scanner = SCons.Defaults.ProgScan)

	env['BUILDERS']['Object'] = static_ob
	env['BUILDERS']['StaticObject'] = static_ob
	env['BUILDERS']['StaticLibrary'] = static_lib
	env['BUILDERS']['Library'] = static_lib
	env['BUILDERS']['Program'] = program

def  my_appit_print(target, source, env):
	a = '%s' % (target[0])
	d, f = os.path.split(a)
	return "making bundle for " + f

def AppIt(target=None, source=None, env=None):
	import shutil
	import commands
	import os.path
	
	
	a = '%s' % (target[0])
	builddir, b = os.path.split(a)
	libdir = env['LCGDIR'][1:]

	bldroot = env.Dir('.').abspath
	binary = env['BINARYKIND']
	 
	if b=='verse':
		print bc.OKBLUE+"no bundle for verse"+bc.ENDC 
		return 0
	
	sourcedir = bldroot + '/source/darwin/%s.app'%binary
	sourceinfo = bldroot + "/source/darwin/%s.app/Contents/Info.plist"%binary
	targetinfo = builddir +'/' + "%s.app/Contents/Info.plist"%binary
	cmd = builddir + '/' +'%s.app'%binary
	
	if os.path.isdir(cmd):
		shutil.rmtree(cmd)
	shutil.copytree(sourcedir, cmd)
	cmd = "cat %s | sed s/VERSION/`cat release/VERSION`/ | sed s/DATE/`date +'%%Y-%%b-%%d'`/ > %s"%(sourceinfo,targetinfo)
	commands.getoutput(cmd)
	cmd = 'cp %s/%s %s/%s.app/Contents/MacOS/%s'%(builddir, binary,builddir, binary, binary)
	commands.getoutput(cmd)
	cmd = 'mkdir %s/%s.app/Contents/MacOS/.blender/'%(builddir, binary)
	print cmd
	commands.getoutput(cmd)
	cmd = builddir + '/%s.app/Contents/MacOS/.blender'%binary
	shutil.copy(bldroot + '/bin/.blender/.bfont.ttf', cmd)
	shutil.copy(bldroot + '/bin/.blender/.Blanguages', cmd)
	cmd = 'cp -R %s/bin/.blender/locale %s/%s.app/Contents/Resources/'%(bldroot,builddir,binary)
	commands.getoutput(cmd) 
	cmd = 'cp -R %s/bin/.blender/locale %s/%s.app/Contents/MacOS/.blender/'%(bldroot,builddir,binary)
	commands.getoutput(cmd) 
	cmd = 'cp %s/bin/.blender/.Blanguages %s/%s.app/Contents/Resources/'%(bldroot,builddir,binary)
	commands.getoutput(cmd) 
	cmd = 'mkdir %s/%s.app/Contents/MacOS/.blender/python/'%(builddir,binary)
	commands.getoutput(cmd) 
	cmd = 'unzip -q %s/release/python.zip -d %s/%s.app/Contents/MacOS/.blender/python/'%(libdir,builddir,binary)
	commands.getoutput(cmd) 
	cmd = 'cp -R %s/release/scripts %s/%s.app/Contents/MacOS/.blender/'%(bldroot,builddir,binary)
	commands.getoutput(cmd)
	cmd = 'cp -R %s/release/ui %s/%s.app/Contents/MacOS/.blender/'%(bldroot,builddir,binary)
	commands.getoutput(cmd)
	cmd = 'cp -R %s/release/io %s/%s.app/Contents/MacOS/.blender/'%(bldroot,builddir,binary)
	commands.getoutput(cmd)
	cmd = 'chmod +x  %s/%s.app/Contents/MacOS/%s'%(builddir,binary, binary)
	commands.getoutput(cmd)
	cmd = 'find %s/%s.app -name .svn -prune -exec rm -rf {} \;'%(builddir, binary)
	commands.getoutput(cmd)
	cmd = 'find %s/%s.app -name .DS_Store -exec rm -rf {} \;'%(builddir, binary)
	commands.getoutput(cmd)

# extract copy system python, be sure to update other build systems
# when making changes to the files that are copied.
def my_pyinst_print(target, source, env):
	pass

def PyInstall(target=None, source=None, env=None):
	# Any Unix except osx
	#-- .blender/python/lib/python3.1
	
	import commands
	
	def run(cmd):
		print 'Install command:', cmd
		commands.getoutput(cmd)
	
	py_src =	env.subst( env['BF_PYTHON_LIBPATH'] + '/python'+env['BF_PYTHON_VERSION'] )
	py_target =	env.subst( env['BF_INSTALLDIR'] + '/.blender/python/lib/python'+env['BF_PYTHON_VERSION'] )
	
	# Copied from source/creator/CMakeLists.txt, keep in sync.
	print 'Install python from:'
	print '\t"%s" into...' %	py_src
	print '\t"%s"\n' %			py_target
	
	run('rm -rf "%s"' % py_target)
	try:	os.makedirs(os.path.dirname(py_target)) # the final part is copied
	except:pass
	
	run('cp -R "%s" "%s"' % (py_src, os.path.dirname(py_target)))
	run('rm -rf "%s/distutils"' % py_target)
	run('rm -rf "%s/lib2to3"' % py_target)
	run('rm -rf "%s/idlelib"' % py_target)
	run('rm -rf "%s/tkinter"' % py_target)
	run('rm -rf "%s/config"' % py_target)

	run('rm -rf "%s/site-packages"' % py_target)
	run('mkdir "%s/site-packages"' % py_target)    # python needs it.'

	run('rm "%s/lib-dynload/_tkinter.so"' % py_target)
	run('find "%s" -name "test" -prune -exec rm -rf {} \;' % py_target)
	run('find "%s" -name "*.py?" -exec rm -rf {} \;' % py_target)
	run('find "%s" -name "*.so"-exec strip -s {} \;' % py_target)

#### END ACTION STUFF #########

def bsc(env, target, source):
	
	bd = os.path.dirname(target[0].abspath)
	bscfile = '\"'+target[0].abspath+'\"'
	bscpathcollect = '\"'+bd + os.sep + '*.sbr\"'
	bscpathtmp = '\"'+bd + os.sep + 'bscmake.tmp\"'

	os.system('dir /b/s '+bscpathcollect+' >'+bscpathtmp)

	myfile = open(bscpathtmp[1:-1], 'r')
	lines = myfile.readlines()
	myfile.close()

	newfile = open(bscpathtmp[1:-1], 'w')
	for l in lines:
		newfile.write('\"'+l[:-1]+'\"\n')
	newfile.close()
				
	os.system('bscmake /nologo /n /o'+bscfile+' @'+bscpathtmp)
	os.system('del '+bscpathtmp)

class BlenderEnvironment(SConsEnvironment):

	def BlenderRes(self=None, libname=None, source=None, libtype=['core'], priority=[100]):
		global libs
		if not self or not libname or not source:
			print bc.FAIL+'Cannot continue.  Missing argument for BlenderRes '+libname+bc.ENDC
			self.Exit()
		if self['OURPLATFORM'] not in ('win32-vc','win32-mingw','linuxcross', 'win64-vc'):
			print bc.FAIL+'BlenderRes is for windows only!'+bc.END
			self.Exit()
		
		print bc.HEADER+'Configuring resource '+bc.ENDC+bc.OKGREEN+libname+bc.ENDC
		lenv = self.Clone()
		res = lenv.RES('#'+root_build_dir+'lib/'+libname, source)
		
		SConsEnvironment.Default(self, res)
		resources.append(res)

	def BlenderLib(self=None, libname=None, sources=None, includes=[], defines=[], libtype='common', priority = 100, compileflags=None, cc_compileflags=None, cxx_compileflags=None):
		global vcp
		if not self or not libname or not sources:
			print bc.FAIL+'Cannot continue. Missing argument for BuildBlenderLib '+libname+bc.ENDC
			self.Exit()

		def list_substring(quickie, libname):
			for q in quickie:
				if libname.find(q) != -1:
					return True
			return False

		if list_substring(quickie, libname) or len(quickie)==0:
			if list_substring(quickdebug, libname):
				print bc.HEADER+'Configuring library '+bc.ENDC+bc.OKGREEN+libname +bc.ENDC+bc.OKBLUE+ " (debug mode)" + bc.ENDC
			else:
				print bc.HEADER+'Configuring library '+bc.ENDC+bc.OKGREEN+libname + bc.ENDC
			lenv = self.Clone()
			lenv.Append(CPPPATH=includes)
			lenv.Append(CPPDEFINES=defines)
			if lenv['BF_DEBUG'] or (libname in quickdebug):
					lenv.Append(CFLAGS = lenv['BF_DEBUG_CFLAGS'])
					lenv.Append(CCFLAGS = lenv['BF_DEBUG_CCFLAGS'])
					lenv.Append(CXXFLAGS = lenv['BF_DEBUG_CXXFLAGS'])
			else:
					lenv.Append(CFLAGS = lenv['REL_CFLAGS'])
					lenv.Append(CCFLAGS = lenv['REL_CCFLAGS'])
					lenv.Append(CXXFLAGS = lenv['REL_CXXFLAGS'])
			if lenv['BF_PROFILE']:
					lenv.Append(CFLAGS = lenv['BF_PROFILE_CFLAGS'])
					lenv.Append(CCFLAGS = lenv['BF_PROFILE_CCFLAGS'])
					lenv.Append(CXXFLAGS = lenv['BF_PROFILE_CXXFLAGS'])
			if compileflags:
				lenv.Replace(CFLAGS = compileflags)
			if cc_compileflags:
				lenv.Replace(CCFLAGS = cc_compileflags)
			if cxx_compileflags:
				lenv.Replace(CXXFLAGS = cxx_compileflags)
			lenv.Append(CFLAGS = lenv['C_WARN'])
			lenv.Append(CCFLAGS = lenv['CC_WARN'])
			lenv.Append(CXXFLAGS = lenv['CXX_WARN'])

			if lenv['OURPLATFORM'] in ('win32-vc', 'win64-vc'):
				if lenv['BF_DEBUG']:
					lenv.Append(CCFLAGS = ['/MTd'])
				else:
					lenv.Append(CCFLAGS = ['/MT'])
			
			targetdir = root_build_dir+'lib/' + libname
			if not (root_build_dir[0]==os.sep or root_build_dir[1]==':'):
				targetdir = '#'+targetdir
			lib = lenv.Library(target= targetdir, source=sources)
			SConsEnvironment.Default(self, lib) # we add to default target, because this way we get some kind of progress info during build
			if self['BF_MSVS'] and self['OURPLATFORM'] in ('win32-vc', 'win64-vc'):
				#if targetdir[0] == '#':
				#	targetdir = targetdir[1:-1]
				print "! ",targetdir+ '.vcproj' # + self['MSVSPROJECTSUFFIX']
				vcproject = self.MSVSProject(target = targetdir + '.vcproj', # + self['MSVSPROJECTSUFFIX'],
						 srcs = sources,
						 buildtarget = lib,
						 variant = 'Release',
						 auto_build_solution=0)
				vcp.append(vcproject)
				SConsEnvironment.Default(self, vcproject)
		else:
			print bc.WARNING+'Not building '+bc.ENDC+bc.OKGREEN+libname+bc.ENDC+' for '+bc.OKBLUE+'BF_QUICK'+bc.ENDC
		# note: libs is a global
		add_lib_to_dict(self, libs, libtype, libname, priority)

	def BlenderProg(self=None, builddir=None, progname=None, sources=None, includes=None, libs=None, libpath=None, binarykind=''):
		global vcp
		print bc.HEADER+'Configuring program '+bc.ENDC+bc.OKGREEN+progname+bc.ENDC
		lenv = self.Clone()
		if lenv['OURPLATFORM'] in ('win32-vc', 'cygwin', 'win64-vc'):
			lenv.Append(LINKFLAGS = lenv['PLATFORM_LINKFLAGS'])
			lenv.Append(LINKFLAGS = ['/FORCE:MULTIPLE'])
			if lenv['BF_DEBUG']:
				lenv.Prepend(LINKFLAGS = ['/DEBUG','/PDB:'+progname+'.pdb'])
		if  lenv['OURPLATFORM']=='linux2':
			lenv.Append(LINKFLAGS = lenv['PLATFORM_LINKFLAGS'])
			if lenv['WITH_BF_PYTHON']:
				lenv.Append(LINKFLAGS = lenv['BF_PYTHON_LINKFLAGS'])
		if  lenv['OURPLATFORM']=='sunos5':
			lenv.Append(LINKFLAGS = lenv['PLATFORM_LINKFLAGS'])
			if lenv['WITH_BF_PYTHON']:
				lenv.Append(LINKFLAGS = lenv['BF_PYTHON_LINKFLAGS'])
			if lenv['CXX'].endswith('CC'):
				 lenv.Replace(LINK = '$CXX')
		if  lenv['OURPLATFORM']=='darwin':
			lenv.Append(LINKFLAGS = lenv['PLATFORM_LINKFLAGS'])
			if lenv['WITH_BF_PYTHON']:
				lenv.Append(LINKFLAGS = lenv['BF_PYTHON_LINKFLAGS'])
			lenv.Append(LINKFLAGS = lenv['BF_OPENGL_LINKFLAGS'])
		if lenv['BF_PROFILE']:
			lenv.Append(LINKFLAGS = lenv['BF_PROFILE_LINKFLAGS'])
		lenv.Append(CPPPATH=includes)
		if root_build_dir[0]==os.sep or root_build_dir[1]==':':
			lenv.Append(LIBPATH=root_build_dir + '/lib')
		lenv.Append(LIBPATH=libpath)
		lenv.Append(LIBS=libs)
		if lenv['WITH_BF_QUICKTIME']:
			 lenv.Append(LIBS = lenv['BF_QUICKTIME_LIB'])
			 lenv.Append(LIBPATH = lenv['BF_QUICKTIME_LIBPATH'])
		prog = lenv.Program(target=builddir+'bin/'+progname, source=sources)
		if lenv['BF_DEBUG'] and lenv['OURPLATFORM'] in ('win32-vc', 'win64-vc') and lenv['BF_BSC']:
			f = lenv.File(progname + '.bsc', builddir)
			brs = lenv.Command(f, prog, [bsc])
			SConsEnvironment.Default(self, brs)
		SConsEnvironment.Default(self, prog)
		if self['BF_MSVS'] and self['OURPLATFORM'] in ('win32-vc', 'win64-vc') and progname == 'blender':
			print "! ",builddir + "/" + progname + '.sln'
			sln = self.MSVSProject(target = builddir + "/" + progname + '.sln',
					 projects= vcp,
					 variant = 'Release')
			SConsEnvironment.Default(self, sln)
		program_list.append(prog)
		if  lenv['OURPLATFORM']=='darwin':
			lenv['BINARYKIND'] = binarykind
			lenv.AddPostAction(prog,Action(AppIt,strfunction=my_appit_print))
		elif os.sep == '/': # any unix
			if lenv['WITH_BF_PYTHON']:
				if not lenv['WITHOUT_BF_INSTALL'] and not lenv['WITHOUT_BF_PYTHON_INSTALL']:
					lenv.AddPostAction(prog,Action(PyInstall,strfunction=my_pyinst_print))
		
		return prog

	def Glob(lenv, pattern):
		path = string.replace(GetBuildPath(lenv,'SConscript'),'SConscript', '')
		files = []
		for i in glob.glob(path + pattern):
			files.append(string.replace(i, path, ''))
		return files
