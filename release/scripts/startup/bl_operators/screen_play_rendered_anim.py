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

# <pep8-80 compliant>

# Originally written by Matt Ebb

import bpy
from bpy.types import Operator
import os

from bpy.app.translations import pgettext_tip as tip_


def guess_player_path(preset):
    import sys

    if preset == 'INTERNAL':
        return bpy.app.binary_path

    elif preset == 'DJV':
        player_path = "djv"
        if sys.platform == "darwin":
            test_path = "/Applications/DJV2.app/Contents/Resources/bin/djv"
            if os.path.exists(test_path):
                player_path = test_path

    elif preset == 'FRAMECYCLER':
        player_path = "framecycler"

    elif preset == 'RV':
        player_path = "rv"

    elif preset == 'MPLAYER':
        player_path = "mplayer"

    else:
        player_path = ""

    return player_path


class PlayRenderedAnim(Operator):
    """Play back rendered frames/movies using an external player"""
    bl_idname = "render.play_rendered_anim"
    bl_label = "Play Rendered Animation"
    bl_options = {'REGISTER'}

    def execute(self, context):
        import subprocess
        from shlex import quote

        scene = context.scene
        rd = scene.render
        prefs = context.preferences
        fps_final = rd.fps / rd.fps_base

        preset = prefs.filepaths.animation_player_preset
        # file_path = bpy.path.abspath(rd.filepath)  # UNUSED
        is_movie = rd.is_movie_format

        # try and guess a command line if it doesn't exist
        if preset == 'CUSTOM':
            player_path = prefs.filepaths.animation_player
        else:
            player_path = guess_player_path(preset)

        if is_movie is False and preset in {'FRAMECYCLER', 'RV', 'MPLAYER'}:
            # replace the number with '#'
            file_a = rd.frame_path(frame=0)

            # TODO, make an api call for this
            frame_tmp = 9
            file_b = rd.frame_path(frame=frame_tmp)

            while len(file_a) == len(file_b):
                frame_tmp = (frame_tmp * 10) + 9
                file_b = rd.frame_path(frame=frame_tmp)
            file_b = rd.frame_path(frame=int(frame_tmp / 10))

            file = ("".join((c if file_b[i] == c else "#")
                            for i, c in enumerate(file_a)))
            del file_a, file_b, frame_tmp
            file = bpy.path.abspath(file)  # expand '//'
        else:
            path_valid = True
            # works for movies and images
            file = rd.frame_path(frame=scene.frame_start, preview=scene.use_preview_range)
            file = bpy.path.abspath(file)  # expand '//'
            if not os.path.exists(file):
                err_msg = tip_("File %r not found") % file
                self.report({'WARNING'}, err_msg)
                path_valid = False

            # one last try for full range if we used preview range
            if scene.use_preview_range and not path_valid:
                file = rd.frame_path(frame=scene.frame_start, preview=False)
                file = bpy.path.abspath(file)  # expand '//'
                err_msg = tip_("File %r not found") % file
                if not os.path.exists(file):
                    self.report({'WARNING'}, err_msg)

        cmd = [player_path]
        # extra options, fps controls etc.
        if scene.use_preview_range:
            frame_start = scene.frame_preview_start
            frame_end = scene.frame_preview_end
        else:
            frame_start = scene.frame_start
            frame_end = scene.frame_end
        if preset == 'INTERNAL':
            opts = [
                "-a",
                "-f", str(rd.fps), str(rd.fps_base),
                "-s", str(frame_start),
                "-e", str(frame_end),
                "-j", str(scene.frame_step),
                file,
            ]
            cmd.extend(opts)
        elif preset == 'DJV':
            opts = [
                file,
                "-speed", str(fps_final),
                "-in_out", str(frame_start), str(frame_end),
                "-frame", str(scene.frame_current),
                "-time_units", "Frames"
            ]
            cmd.extend(opts)
        elif preset == 'FRAMECYCLER':
            opts = [file, f"{scene.frame_start:d}-{scene.frame_end:d}"]
            cmd.extend(opts)
        elif preset == 'RV':
            opts = ["-fps", str(rd.fps), "-play", f"[ {file:s} ]"]
            cmd.extend(opts)
        elif preset == 'MPLAYER':
            opts = []
            if is_movie:
                opts.append(file)
            else:
                opts += [
                    ("mf://" + file.replace("#", "?")),
                    "-mf",
                    f"fps={fps_final:4f}"
                ]

            opts += ["-loop", "0", "-really-quiet", "-fs"]
            cmd.extend(opts)
        else:  # 'CUSTOM'
            cmd.append(file)

        # launch it
        print("Executing command:\n ", " ".join(quote(c) for c in cmd))

        try:
            subprocess.Popen(cmd)
        except Exception as e:
            err_msg = tip_("Couldn't run external animation player with command %r\n%s") % (cmd, e)
            self.report(
                {'ERROR'},
                err_msg,
            )
            return {'CANCELLED'}

        return {'FINISHED'}


classes = (
    PlayRenderedAnim,
)
