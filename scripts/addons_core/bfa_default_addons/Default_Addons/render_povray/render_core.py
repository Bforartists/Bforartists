# SPDX-FileCopyrightText: 2022-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Define the POV render engine from generic Blender RenderEngine class."""
import bpy

import builtins as __builtin__
import subprocess
import os
from sys import platform
import time
import re
import tempfile
from bpy.utils import register_class, unregister_class
from . import render

def console_get(context):
    #context = bpy.context
    for win in context.window_manager.windows:
        if win.screen is not None:
            scr = win.screen
            for area in scr.areas:
                if area.type == 'CONSOLE':
                    for space in area.spaces:
                        if space.type == 'CONSOLE':
                            return area, space, win, scr
    return None, None, None, None

def console_write(txt):
    area, space, window, screen = console_get()
    if space is None:
        return
    context = bpy.context.copy()
    context.update(dict(
        area=area,
        space_data=space,
        region=area.regions[-1],
        window=window,
        screen=screen,
    ))
    with bpy.context.temp_override(**context):
        for line in txt.split("\n"):
            bpy.ops.console.scrollback_append(text=line, type='INFO')
"""
class RENDER_OT_test(bpy.types.Operator):
    bl_idname = 'pov.oha_test'
    bl_label = 'Test'
    bl_options = {'REGISTER', 'UNDO'}

    txt: bpy.props.StringProperty(
        name='text',
        default='what?'
    )
    def execute(self, context):
        try:
            console_write(self.txt)
            return {'FINISHED'}
        except:
            self.report({'INFO'}, 'Printing report to Info window.')
            return {'CANCELLED'}

def console_print(*args, **kwargs):
    context = bpy.context
    #screens = (win.screen for win in context.window_manager.windows if win.screen is not None)
    for win in context.window_manager.windows:
        if win.screen is not None:
            scr = win.screen
            for a in scr.areas:
                if a.type == 'CONSOLE':
                    try:
                        c = {}
                        c['area'] = a
                        c['space_data'] = a.spaces.active
                        c['region'] = a.regions[-1]
                        c['window'] = win
                        c['screen'] = scr
                        s = " ".join([str(arg) for arg in args])
                        for line in s.split("\n"):
                            bpy.ops.console.scrollback_append(c, text=line, type='INFO')

                    except BaseException as e:
                        print(e.__doc__)
                        print('An exception occurred: {}'.format(e))
                        pass


def print(*args, **kwargs):
    console_print(*args, **kwargs)       # to Python Console
    __builtin__.print(*args, **kwargs)   # to System Console
"""

user_dir = bpy.utils.resource_path('USER')
preview_dir = os.path.join(user_dir, "preview")
# Make sure Preview directory exists and is empty
smoke_path = os.path.join(preview_dir, "smoke.df3")

class PovRender(bpy.types.RenderEngine):
    """Define the external renderer"""

    bl_idname = 'POVRAY_RENDER'
    bl_label = "Persitence Of Vision"
    bl_use_eevee_viewport = True
    bl_use_shading_nodes_custom = False
    DELAY = 0.5

    @staticmethod
    def _locate_binary():
        """Identify POV engine"""
        addon_prefs = bpy.context.preferences.addons[__package__].preferences

        # Use the system preference if its set.
        if pov_binary:= addon_prefs.filepath_povray:
            if os.path.exists(pov_binary):
                return pov_binary
            # Implicit else, as here return was still not triggered:
            print("User Preferences path to povray %r NOT FOUND, checking $PATH" % pov_binary)

        # Windows Only
        # assume if there is a 64bit binary that the user has a 64bit capable OS
        if platform.startswith('win'):
            import winreg

            win_reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Software\\POV-Ray\\v3.7\\Windows"
            )
            win_home = winreg.QueryValueEx(win_reg_key, "Home")[0]

            # First try 64bits UberPOV
            pov_binary = os.path.join(win_home, "bin", "uberpov64.exe")
            if os.path.exists(pov_binary):
                return pov_binary

            # Then try 64bits POV
            pov_binary = os.path.join(win_home, "bin", "pvengine64.exe")
            if os.path.exists(pov_binary):
                return pov_binary

        # search the path all os's
        pov_binary_default = "povray"

        os_path_ls = os.getenv("PATH").split(':') + [""]

        for dir_name in os_path_ls:
            pov_binary = os.path.join(dir_name, pov_binary_default)
            if os.path.exists(pov_binary):
                return pov_binary
        return ""

    def _export(self, depsgraph, pov_path, image_render_path):
        """gather all necessary output files paths user defined and auto generated and export there"""

        scene = bpy.context.scene
        if scene.pov.tempfiles_enable:
            self._temp_file_in = tempfile.NamedTemporaryFile(suffix=".pov", delete=False).name
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            # self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".tga", delete=False).name
            self._temp_file_ini = tempfile.NamedTemporaryFile(suffix=".ini", delete=False).name
            log_path = os.path.join(tempfile.gettempdir(), "alltext.out")
        else:
            self._temp_file_in = pov_path + ".pov"
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = image_render_path + ".png"
            # self._temp_file_out = image_render_path + ".tga"
            self._temp_file_ini = pov_path + ".ini"
            scene_path = scene.pov.scene_path
            abs_log_path = bpy.path.abspath(scene_path)
            log_path= os.path.join(abs_log_path, "alltext.out")
            '''
            self._temp_file_in = "/test.pov"
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = "/test.png"
            #self._temp_file_out = "/test.tga"
            self._temp_file_ini = "/test.ini"
            '''

        self._temp_file_log = log_path
        # self._temp_file_log = log_path.replace('\\', '/') # unnecessary relying on os.path

        if scene.pov.text_block == "":

            def info_callback(txt):
                self.update_stats("", "POV-Ray 3.7: " + txt)

            # os.makedirs(user_dir, exist_ok=True)  # handled with previews
            os.makedirs(preview_dir, exist_ok=True)

            render.write_pov(self._temp_file_in, scene, info_callback)
        else:
            pass

    def _render(self, depsgraph):
        """Export necessary files and render image."""
        scene = bpy.context.scene
        try:
            os.remove(self._temp_file_out)  # so as not to load the old file
        except OSError:
            pass

        pov_binary = PovRender._locate_binary()
        if not pov_binary:
            print("POV-Ray 3.7: could not execute povray, possibly POV-Ray isn't installed")
            return False

        render.write_pov_ini(
            self._temp_file_ini, self._temp_file_log, self._temp_file_in, self._temp_file_out
        )

        print("***-STARTING-***")

        extra_args = []
        # Always add user preferences include path field when specified
        if (pov_documents := bpy.context.preferences.addons[__package__].preferences.docpath_povray)!="":
            extra_args.append("+L"+ pov_documents)
        if scene.pov.command_line_switches != "":
            extra_args.extend(iter(scene.pov.command_line_switches.split(" ")))
        self._is_windows = False
        if platform.startswith('win'):
            self._is_windows = True
            if "/EXIT" not in extra_args and not scene.pov.pov_editor:
                extra_args.append("/EXIT")
        else:
            # added -d option to prevent render window popup which leads to segfault on linux
            extra_args.append("-d")

        # Start Rendering!
        try:
            self._process = subprocess.Popen(
                [pov_binary, self._temp_file_ini] + extra_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except OSError:
            # TODO, report api
            print("POV-Ray 3.7: could not execute '%s'" % pov_binary)
            import traceback

            traceback.print_exc()
            print("***-DONE-***")
            return False

        else:
            print("Engine ready!...")
            print("Command line arguments passed: " + str(extra_args))
            return True

    def _cleanup(self):
        """Delete temp files and unpacked ones"""
        for f in (self._temp_file_in, self._temp_file_ini, self._temp_file_out):
            for i in range(5):
                try:
                    os.unlink(f)
                    break
                except OSError:
                    # Wait a bit before retrying file might be still in use by Blender,
                    # and Windows does not know how to delete a file in use!
                    time.sleep(self.DELAY)
        for i in render.unpacked_images:
            for j in range(5):
                try:
                    os.unlink(i)
                    break
                except OSError:
                    # Wait a bit before retrying file might be still in use by Blender,
                    # and Windows does not know how to delete a file in use!
                    time.sleep(self.DELAY)
        # avoid some crashes if memory leaks from one render to the next?
        #self.free_blender_memory()

    def render(self, depsgraph):
        """Export necessary files from text editor and render image."""

        scene = bpy.context.scene
        r = scene.render
        x = int(r.resolution_x * r.resolution_percentage * 0.01)
        y = int(r.resolution_y * r.resolution_percentage * 0.01)
        print("\n***INITIALIZING***")

        # This makes some tests on the render, returning True if all goes good, and False if
        # it was finished one way or the other.
        # It also pauses the script (time.sleep())
        def _test_wait():
            time.sleep(self.DELAY)

            # User interrupts the rendering
            if self.test_break():
                try:
                    self._process.terminate()
                    print("***POV INTERRUPTED***")
                except OSError:
                    pass
                return False
            try:
                poll_result = self._process.poll()
            except AttributeError:
                print("***CHECK POV PATH IN PREFERENCES***")
                return False
            # POV process is finisehd, one way or the other
            if poll_result is not None:
                if poll_result < 0:
                    print("***POV PROCESS FAILED : %s ***" % poll_result)
                    self.update_stats("", "POV-Ray 3.7: Failed")
                return False

            return True

        if bpy.context.scene.pov.text_block != "":
            if scene.pov.tempfiles_enable:
                self._temp_file_in = tempfile.NamedTemporaryFile(suffix=".pov", delete=False).name
                self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                # self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".tga", delete=False).name
                self._temp_file_ini = tempfile.NamedTemporaryFile(suffix=".ini", delete=False).name
                self._temp_file_log = os.path.join(tempfile.gettempdir(), "alltext.out")
            else:
                pov_path = scene.pov.text_block
                image_render_path = os.path.splitext(pov_path)[0]
                self._temp_file_out = os.path.join(preview_dir, image_render_path)
                self._temp_file_in = os.path.join(preview_dir, pov_path)
                self._temp_file_ini = os.path.join(
                    preview_dir, (os.path.splitext(self._temp_file_in)[0] + ".INI")
                )
                self._temp_file_log = os.path.join(preview_dir, "alltext.out")

            '''
            try:
                os.remove(self._temp_file_in)  # so as not to load the old file
            except OSError:
                pass
            '''
            print(scene.pov.text_block)
            text = bpy.data.texts[scene.pov.text_block]
            with open(self._temp_file_in, "w") as file:
                # Why are the newlines needed?
                file.write("\n")
                file.write(text.as_string())
                file.write("\n")


            # has to be called to update the frame on exporting animations
            scene.frame_set(scene.frame_current)

            pov_binary = PovRender._locate_binary()

            if not pov_binary:
                print("Could not execute POV-Ray, which installation possibly isn't standard ?")
                return False

            # start ini UI options export
            self.update_stats("", "POV-Ray 3.7: Exporting ini options from Blender")

            render.write_pov_ini(
                self._temp_file_ini,
                self._temp_file_log,
                self._temp_file_in,
                self._temp_file_out,
            )

            print("***-STARTING-***")

            extra_args = []

            if scene.pov.command_line_switches != "":
                for new_arg in scene.pov.command_line_switches.split(" "):
                    extra_args.append(new_arg)

            if platform.startswith('win'):
                if "/EXIT" not in extra_args and not scene.pov.pov_editor:
                    extra_args.append("/EXIT")
            else:
                # added -d option to prevent render window popup which leads to segfault on linux
                extra_args.append("-d")

            # Start Rendering!
            try:
                if scene.pov.sdl_window_enable and not platform.startswith(
                    'win'
                ):  # segfault on linux == False !!!
                    env = {'POV_DISPLAY_SCALED': 'off'}
                    env.update(os.environ)
                    self._process = subprocess.Popen(
                        [pov_binary, self._temp_file_ini],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        env=env,
                    )
                else:
                    self._process = subprocess.Popen(
                        [pov_binary, self._temp_file_ini] + extra_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
            except OSError:
                # TODO, report api
                print("POV-Ray 3.7: could not execute '%s'" % pov_binary)
                import traceback

                traceback.print_exc()
                print("***-DONE-***")
                return False

            else:
                print("Engine ready!...")
                print("Command line arguments passed: " + str(extra_args))
                # return True
                self.update_stats("", "POV-Ray 3.7: Parsing File")

            # Indented in main function now so repeated here but still not working
            # to bring back render result to its buffer

            if os.path.exists(self._temp_file_out):
                xmin = int(r.border_min_x * x)
                ymin = int(r.border_min_y * y)
                xmax = int(r.border_max_x * x)
                ymax = int(r.border_max_y * y)
                result = self.begin_result(0, 0, x, y)
                lay = result.layers[0]

                time.sleep(self.DELAY)
                try:
                    lay.load_from_file(self._temp_file_out)
                except RuntimeError:
                    print("***POV ERROR WHILE READING OUTPUT FILE***")
                self.end_result(result)
            # print(self._temp_file_log) #bring the pov log to blender console with proper path?
            with open(
                self._temp_file_log
            ) as f:  # The with keyword automatically closes the file when you are done
                print(f.read()) # console_write(f.read())

            self.update_stats("", "")

            if scene.pov.tempfiles_enable or scene.pov.deletefiles_enable:
                self._cleanup()
        else:

            # WIP output format
            #         if r.image_settings.file_format == 'OPENEXR':
            #             fformat = 'EXR'
            #             render.image_settings.color_mode = 'RGBA'
            #         else:
            #             fformat = 'TGA'
            #             r.image_settings.file_format = 'TARGA'
            #             r.image_settings.color_mode = 'RGBA'

            blend_scene_name = bpy.data.filepath.split(os.path.sep)[-1].split(".")[0]
            pov_scene_name = ""
            pov_path = ""
            image_render_path = ""

            # has to be called to update the frame on exporting animations
            scene.frame_set(scene.frame_current)

            if not scene.pov.tempfiles_enable:

                # check paths
                pov_path = bpy.path.abspath(scene.pov.scene_path).replace('\\', '/')
                if pov_path == "":
                    if bpy.data.is_saved:
                        pov_path = bpy.path.abspath("//")
                    else:
                        pov_path = tempfile.gettempdir()
                elif pov_path.endswith("/"):
                    if pov_path == "/":
                        pov_path = bpy.path.abspath("//")
                    else:
                        pov_path = bpy.path.abspath(scene.pov.scene_path)

                if not os.path.exists(pov_path):
                    try:
                        os.makedirs(pov_path)
                    except BaseException as e:
                        print(e.__doc__)
                        print('An exception occurred: {}'.format(e))
                        import traceback

                        traceback.print_exc()

                        print("POV-Ray 3.7: Cannot create scenes directory: %r" % pov_path)
                        self.update_stats(
                            "", "POV-Ray 3.7: Cannot create scenes directory %r" % pov_path
                        )
                        time.sleep(2.0)
                        # return

                '''
                # Bug in POV-Ray RC3
                image_render_path = bpy.path.abspath(scene.pov.renderimage_path).replace('\\','/')
                if image_render_path == "":
                    if bpy.data.is_saved:
                        image_render_path = bpy.path.abspath("//")
                    else:
                        image_render_path = tempfile.gettempdir()
                    #print("Path: " + image_render_path)
                elif path.endswith("/"):
                    if image_render_path == "/":
                        image_render_path = bpy.path.abspath("//")
                    else:
                        image_render_path = bpy.path.abspath(scene.pov.)
                if not os.path.exists(path):
                    print("POV-Ray 3.7: Cannot find render image directory")
                    self.update_stats("", "POV-Ray 3.7: Cannot find render image directory")
                    time.sleep(2.0)
                    return
                '''

                # check name
                if scene.pov.scene_name == "":
                    if blend_scene_name != "":
                        pov_scene_name = blend_scene_name
                    else:
                        pov_scene_name = "untitled"
                else:
                    pov_scene_name = scene.pov.scene_name
                    if os.path.isfile(pov_scene_name):
                        pov_scene_name = os.path.basename(pov_scene_name)
                    pov_scene_name = pov_scene_name.split('/')[-1].split('\\')[-1]
                    if not pov_scene_name:
                        print("POV-Ray 3.7: Invalid scene name")
                        self.update_stats("", "POV-Ray 3.7: Invalid scene name")
                        time.sleep(2.0)
                        # return
                    pov_scene_name = os.path.splitext(pov_scene_name)[0]

                print("Scene name: " + pov_scene_name)
                print("Export path: " + pov_path)
                pov_path = os.path.join(pov_path, pov_scene_name)
                pov_path = os.path.realpath(pov_path)

                image_render_path = pov_path
                # print("Render Image path: " + image_render_path)

            # start export
            self.update_stats("", "POV-Ray 3.7: Exporting data from Blender")
            self._export(depsgraph, pov_path, image_render_path)
            self.update_stats("", "POV-Ray 3.7: Parsing File")

            if not self._render(depsgraph):
                self.update_stats("", "POV-Ray 3.7: Not found")
                # return

            # r = scene.render
            # compute resolution
            # x = int(r.resolution_x * r.resolution_percentage * 0.01)
            # y = int(r.resolution_y * r.resolution_percentage * 0.01)

            # Wait for the file to be created
            # XXX This is no more valid, as 3.7 always creates output file once render is finished!
            parsing = re.compile(br"= \[Parsing\.\.\.\] =")
            rendering = re.compile(br"= \[Rendering\.\.\.\] =")
            percent = re.compile(r"\(([0-9]{1,3})%\)")
            # print("***POV WAITING FOR FILE***")

            data = b""
            last_line = ""
            while _test_wait():
                # POV in Windows did not output its stdout/stderr, it displayed them in its GUI
                # But now writes file
                if self._is_windows:
                    self.update_stats("", "POV-Ray 3.7: Rendering File")
                else:
                    t_data = self._process.stdout.read(10000)
                    if not t_data:
                        continue

                    data += t_data
                    # XXX This is working for UNIX, not sure whether it might need adjustments for
                    #     other OSs
                    # First replace is for windows
                    t_data = str(t_data).replace('\\r\\n', '\\n').replace('\\r', '\r')
                    lines = t_data.split('\\n')
                    last_line += lines[0]
                    lines[0] = last_line
                    print('\n'.join(lines), end="")
                    last_line = lines[-1]

                    if rendering.search(data):
                        _pov_rendering = True
                        match = percent.findall(str(data))
                        if match:
                            self.update_stats("", "POV-Ray 3.7: Rendering File (%s%%)" % match[-1])
                        else:
                            self.update_stats("", "POV-Ray 3.7: Rendering File")

                    elif parsing.search(data):
                        self.update_stats("", "POV-Ray 3.7: Parsing File")

            if os.path.exists(self._temp_file_out):
                # print("***POV FILE OK***")
                # self.update_stats("", "POV-Ray 3.7: Rendering")

                # prev_size = -1

                xmin = int(r.border_min_x * x)
                ymin = int(r.border_min_y * y)
                xmax = int(r.border_max_x * x)
                ymax = int(r.border_max_y * y)

                # print("***POV UPDATING IMAGE***")
                result = self.begin_result(0, 0, x, y)
                # XXX, tests for border render.
                # result = self.begin_result(xmin, ymin, xmax - xmin, ymax - ymin)
                # result = self.begin_result(0, 0, xmax - xmin, ymax - ymin)
                lay = result.layers[0]

                # This assumes the file has been fully written We wait a bit, just in case!
                time.sleep(self.DELAY)
                try:
                    lay.load_from_file(self._temp_file_out)
                    # XXX, tests for border render.
                    # lay.load_from_file(self._temp_file_out, xmin, ymin)
                except RuntimeError:
                    print("***POV ERROR WHILE READING OUTPUT FILE***")

                # Not needed right now, might only be useful if we find a way to use temp raw output of
                # pov 3.7 (in which case it might go under _test_wait()).
                '''
                def update_image():
                    # possible the image wont load early on.
                    try:
                        lay.load_from_file(self._temp_file_out)
                        # XXX, tests for border render.
                        #lay.load_from_file(self._temp_file_out, xmin, ymin)
                        #lay.load_from_file(self._temp_file_out, xmin, ymin)
                    except RuntimeError:
                        pass

                # Update while POV-Ray renders
                while True:
                    # print("***POV RENDER LOOP***")

                    # test if POV-Ray exists
                    if self._process.poll() is not None:
                        print("***POV PROCESS FINISHED***")
                        update_image()
                        break

                    # user exit
                    if self.test_break():
                        try:
                            self._process.terminate()
                            print("***POV PROCESS INTERRUPTED***")
                        except OSError:
                            pass

                        break

                    # Would be nice to redirect the output
                    # stdout_value, stderr_value = self._process.communicate() # locks

                    # check if the file updated
                    new_size = os.path.getsize(self._temp_file_out)

                    if new_size != prev_size:
                        update_image()
                        prev_size = new_size

                    time.sleep(self.DELAY)
                '''

                self.end_result(result)
            else:
                print("***NO POV OUTPUT IMAGE***")

            print("***POV INPUT FILE WRITTEN***")

            # print(filename_log) #bring the pov log to blender console with proper path?
            try:
                with open(
                    self._temp_file_log, encoding='utf-8'
                ) as f:  # The with keyword automatically closes the file when you are done
                    msg = f.read()
                    if isinstance(msg, str):
                        stdmsg = msg
                        #decoded = False
                    elif type(msg) == bytes:
                        #stdmsg = msg.split('\n')
                        stdmsg = msg.encode('utf-8', "replace")
                    # stdmsg = msg.encode("utf-8", "replace")

                    # stdmsg = msg.decode(encoding)
                    # decoded = True
                    # msg.encode('utf-8').decode('utf-8')
                    stdmsg.replace("\t", "    ")
                    print(stdmsg) # console_write(stdmsg) # todo fix segfault and use
            except FileNotFoundError:
                print("No render log to read")
            self.update_stats("", "")

            if scene.pov.tempfiles_enable or scene.pov.deletefiles_enable:
                self._cleanup()

            sound_on = bpy.context.preferences.addons[__package__].preferences.use_sounds
            finished_render_message = "\'Et Voilà!\'"

            if platform.startswith('win') and sound_on:
                # Could not find tts Windows command so playing beeps instead :-)
                # "Korobeiniki"(Коробе́йники)
                # aka "A-Type" Tetris theme
                import winsound

                winsound.Beep(494, 250)  # B
                winsound.Beep(370, 125)  # F
                winsound.Beep(392, 125)  # G
                winsound.Beep(440, 250)  # A
                winsound.Beep(392, 125)  # G
                winsound.Beep(370, 125)  # F#
                winsound.Beep(330, 275)  # E
                winsound.Beep(330, 125)  # E
                winsound.Beep(392, 125)  # G
                winsound.Beep(494, 275)  # B
                winsound.Beep(440, 125)  # A
                winsound.Beep(392, 125)  # G
                winsound.Beep(370, 275)  # F
                winsound.Beep(370, 125)  # F
                winsound.Beep(392, 125)  # G
                winsound.Beep(440, 250)  # A
                winsound.Beep(494, 250)  # B
                winsound.Beep(392, 250)  # G
                winsound.Beep(330, 350)  # E
                time.sleep(0.5)
                winsound.Beep(440, 250)  # A
                winsound.Beep(440, 150)  # A
                winsound.Beep(523, 125)  # D8
                winsound.Beep(659, 250)  # E8
                winsound.Beep(587, 125)  # D8
                winsound.Beep(523, 125)  # C8
                winsound.Beep(494, 250)  # B
                winsound.Beep(494, 125)  # B
                winsound.Beep(392, 125)  # G
                winsound.Beep(494, 250)  # B
                winsound.Beep(440, 150)  # A
                winsound.Beep(392, 125)  # G
                winsound.Beep(370, 250)  # F#
                winsound.Beep(370, 125)  # F#
                winsound.Beep(392, 125)  # G
                winsound.Beep(440, 250)  # A
                winsound.Beep(494, 250)  # B
                winsound.Beep(392, 250)  # G
                winsound.Beep(330, 300)  # E

            # Mac supports natively say command
            elif platform == "darwin":
                # We don't want the say command to block Python,
                # so we add an ampersand after the message
                # but if the os TTS package isn't up to date it
                # still does thus, the try except clause
                try:
                    os.system("say -v Amelie %s &" % finished_render_message)
                except BaseException as e:
                    print(e.__doc__)
                    print("your Mac may need an update, try to restart computer")
                    pass
            # While Linux frequently has espeak installed or at least can suggest
            # Maybe windows could as well ?
            elif platform == "linux":
                # We don't want the espeak command to block Python,
                # so we add an ampersand after the message
                # but if the espeak TTS package isn't installed it
                # still does thus, the try except clause
                try:
                    os.system("echo %s | espeak &" % finished_render_message)
                except BaseException as e:
                    print(e.__doc__)
                    pass

classes = (
    PovRender,
)


def register():
    for cls in classes:
        register_class(cls)



def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
