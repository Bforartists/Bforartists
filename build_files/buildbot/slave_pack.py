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

# <pep8 compliant>

# Runs on buildbot slave, creating a release package using the build
# system and zipping it into buildbot_upload.zip. This is then uploaded
# to the master in the next buildbot step.

import os
import subprocess
import sys
import zipfile

# get builder name
if len(sys.argv) < 2:
    sys.stderr.write("Not enough arguments, expecting builder name\n")
    sys.exit(1)

builder = sys.argv[1]
branch = ''

if len(sys.argv) >= 3:
    branch = sys.argv[2]

# scons does own packaging
if builder.find('scons') != -1:
    os.chdir('../blender')
    scons_options = ['BF_QUICK=slnt', 'BUILDBOT_BRANCH=' + branch, 'buildslave']

    if builder.find('linux') != -1:
        buildbot_dir = os.path.dirname(os.path.realpath(__file__))
        config_dir = os.path.join(buildbot_dir, 'config')
        build_dir = os.path.join('..', 'build', builder)
        install_dir = os.path.join('..', 'install', builder)

        scons_options += ['WITH_BF_NOBLENDER=True', 'WITH_BF_PLAYER=False',
            'BF_BUILDDIR=' + build_dir,
            'BF_INSTALLDIR=' + install_dir,
            'WITHOUT_BF_INSTALL=True']

        config = None

        if builder.endswith('linux_x86_64_scons'):
            config = 'user-config-x86_64.py'
        elif builder.endswith('linux_i386_scons'):
            config = 'user-config-x86_64.py'

        if config is not None:
            config_fpath = os.path.join(config_dir, config)
            scons_options.append('BF_CONFIG=' + config_fpath)

        blender = os.path.join(install_dir, 'blender')
        blenderplayer = os.path.join(install_dir, 'blenderplayer')
        subprocess.call(['strip', '--strip-all', blender, blenderplayer])

        retcode = subprocess.call(['python', 'scons/scons.py'] + scons_options)
        sys.exit(retcode)
    else:
        bitness = '32'
        # Switch to new FFmpeg library
        if builder.find('win') != -1:
            if builder.find('win32') != -1:
                LCGDIR = '#../lib/windows'
            elif builder.find('win64') != -1:
                LCGDIR = '#../lib/win64'
                bitness = '64'

            all_ffmpeg_libs = ['avcodec-53',
                               'avdevice-53',
                               'avformat-53',
                               'avutil-51',
                               'swscale-2']

            ffmpeg_lib = []
            ffmpeg_dll = []

            for lib in all_ffmpeg_libs:
                ffmpeg_lib.append(lib + '.lib')
                ffmpeg_dll.append('${BF_FFMPEG_LIBPATH}/' + lib + '.dll')

            scons_options.append('BF_FFMPEG=' + LCGDIR + '/ffmpeg-0.8')
            scons_options.append('BF_FFMPEG_LIB=' + (' '.join(ffmpeg_lib)))
            scons_options.append('BF_FFMPEG_DLL=' + (' '.join(ffmpeg_dll)))

            scons_options.append('BF_BITNESS='+bitness)

        retcode = subprocess.call(['python', 'scons/scons.py'] + scons_options)
        sys.exit(retcode)

# clean release directory if it already exists
dir = 'release'

if os.path.exists(dir):
    for f in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, f)):
            os.remove(os.path.join(dir, f))

# create release package
try:
    subprocess.call(['make', 'package_archive'])
except Exception, ex:
    sys.stderr.write('Make package release failed' + str(ex) + '\n')
    sys.exit(1)

# find release directory, must exist this time
if not os.path.exists(dir):
    sys.stderr.write("Failed to find release directory.\n")
    sys.exit(1)

# find release package
file = None
filepath = None

for f in os.listdir(dir):
    rf = os.path.join(dir, f)
    if os.path.isfile(rf) and f.startswith('blender'):
        file = f
        filepath = rf

if not file:
    sys.stderr.write("Failed to find release package.\n")
    sys.exit(1)

# create zip file
try:
    upload_zip = "buildbot_upload.zip"
    if os.path.exists(upload_zip):
        os.remove(upload_zip)
    z = zipfile.ZipFile(upload_zip, "w", compression=zipfile.ZIP_STORED)
    z.write(filepath, arcname=file)
    z.close()
except Exception, ex:
    sys.stderr.write('Create buildbot_upload.zip failed' + str(ex) + '\n')
    sys.exit(1)
