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
    scons_options = ['BF_FANCY=False']

    if builder.find('linux') != -1:
        import shutil

        configs = []
        if builder.endswith('linux_glibc211_x86_64_scons'):
            configs = ['user-config-player-glibc211-x86_64.py',
                       #'user-config-cuda-glibc211-x86_64.py',
                       'user-config-glibc211-x86_64.py'
                       ]
            chroot_name = 'buildbot_squeeze_x86_64'
            cuda_chroot = 'buildbot_squeeze_x86_64'
        elif builder.endswith('linux_glibc211_i386_scons'):
            configs = ['user-config-player-glibc211-i686.py',
                       #'user-config-cuda-glibc211-i686.py',
                       'user-config-glibc211-i686.py']
            chroot_name = 'buildbot_squeeze_i686'

            # use 64bit cuda toolkit, so there'll be no memory limit issues
            cuda_chroot = 'buildbot_squeeze_x86_64'

        # Compilation will happen inside of chroot environment
        prog_scons_cmd = ['schroot', '-c', chroot_name, '--'] + scons_cmd
        cuda_scons_cmd = ['schroot', '-c', cuda_chroot, '--'] + scons_cmd

        # We're using the same rules as release builder, so tweak
        # build and install dirs
        build_dir = os.path.join('..', 'build', builder)
        install_dir = os.path.join('..', 'install', builder)

        common_options = ['BF_INSTALLDIR=' + install_dir] + scons_options

        # Clean install directory so we'll be sure there's no
        if os.path.isdir(install_dir):
            shutil.rmtree(install_dir)

        buildbot_dir = os.path.dirname(os.path.realpath(__file__))
        config_dir = os.path.join(buildbot_dir, 'config')

        for config in configs:
            config_fpath = os.path.join(config_dir, config)

            scons_options = []

            if config.find('player') != -1:
                scons_options.append('BF_BUILDDIR=%s_player' % (build_dir))
            else:
                scons_options.append('BF_BUILDDIR=%s' % (build_dir))

            scons_options += common_options

            if config.find('player') != -1:
                scons_options.append('blenderplayer')
                cur_scons_cmd = prog_scons_cmd
            elif config.find('cuda') != -1:
                scons_options.append('cudakernels')
                cur_scons_cmd = cuda_scons_cmd

                if config.find('i686') != -1:
                    scons_options.append('BF_BITNESS=32')
                elif config.find('x86_64') != -1:
                    scons_options.append('BF_BITNESS=64')
            else:
                scons_options.append('blender')
                cur_scons_cmd = prog_scons_cmd

            scons_options.append('BF_CONFIG=' + config_fpath)

            retcode = subprocess.call(cur_scons_cmd + scons_options)
            if retcode != 0:
                print('Error building rules wuth config ' + config)
                sys.exit(retcode)

        sys.exit(0)
    else:
        if builder.find('win') != -1:
            bitness = '32'

            if builder.find('win64') != -1:
                bitness = '64'

            scons_options.append('BF_BITNESS=' + bitness)
            scons_options.append('WITH_BF_CYCLES_CUDA_BINARIES=True')
            scons_options.append('BF_CYCLES_CUDA_NVCC=nvcc.exe')
            if builder.find('mingw') != -1:
                scons_options.append('BF_TOOLSET=mingw')

        retcode = subprocess.call(['python', 'scons/scons.py'] + scons_options)
        sys.exit(retcode)
