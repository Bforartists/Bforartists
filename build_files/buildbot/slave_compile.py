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

import os
import subprocess
import sys

# get builder name
if len(sys.argv) < 2:
    sys.stderr.write("Not enough arguments, expecting builder name\n")
    sys.exit(1)

builder = sys.argv[1]

# we run from build/ directory
blender_dir = '../blender'

if builder.find('cmake') != -1:
    # cmake

    # set build options
    cmake_options = ['-DCMAKE_BUILD_TYPE:STRING=Release']

    if builder.endswith('mac_x86_64_cmake'):
        cmake_options.append('-DCMAKE_OSX_ARCHITECTURES:STRING=x86_64')
    elif builder.endswith('mac_i386_cmake'):
        cmake_options.append('-DCMAKE_OSX_ARCHITECTURES:STRING=i386')
    elif builder.endswith('mac_ppc_cmake'):
        cmake_options.append('-DCMAKE_OSX_ARCHITECTURES:STRING=ppc')

    # configure and make
    retcode = subprocess.call(['cmake', blender_dir] + cmake_options)
    if retcode != 0:
        sys.exit(retcode)
    retcode = subprocess.call(['make', '-s', '-j4', 'install'])
    sys.exit(retcode)
else:
    # scons
    os.chdir(blender_dir)
    scons_cmd = ['python', 'scons/scons.py']
    scons_options = []

    if builder.find('linux') != -1:
        import shutil

        # We're using the same rules as release builder, so tweak
        # build and install dirs
        build_dir = os.path.join('..', 'build', builder)
        install_dir = os.path.join('..', 'install', builder)

        common_options = ['BF_INSTALLDIR=' + install_dir]

        # Clean install directory so we'll be sure there's no
        if os.path.isdir(install_dir):
            shutil.rmtree(install_dir)

        buildbot_dir = os.path.dirname(os.path.realpath(__file__))
        config_dir = os.path.join(buildbot_dir, 'config')

        configs = []
        if builder.endswith('linux_x86_64_scons'):
            configs = ['user-config-player-x86_64.py',
                       'user-config-x86_64.py']
        elif builder.endswith('linux_i386_scons'):
            configs = ['user-config-player-i686.py',
                       'user-config-i686.py']

        for config in configs:
            config_fpath = os.path.join(config_dir, config)

            scons_options = []

            if config.find('player') != -1:
                scons_options.append('BF_BUILDDIR=%s_player' % (build_dir))
            else:
                scons_options.append('BF_BUILDDIR=%s' % (build_dir))

            scons_options += common_options

            if config.find('player') == -1:
                scons_options.append('blender')
            else:
                scons_options.append('blenderplayer')

            scons_options.append('BF_CONFIG=' + config_fpath)

            retcode = subprocess.call(scons_cmd + scons_options)
            if retcode != 0:
                print('Error building rules wuth config ' + config)
                sys.exit(retcode)

        sys.exit(0)
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

            scons_options.append('BF_BITNESS=' + bitness)

        retcode = subprocess.call(['python', 'scons/scons.py'] + scons_options)
        sys.exit(retcode)
