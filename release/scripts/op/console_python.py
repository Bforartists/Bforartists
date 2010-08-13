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
import sys
import bpy

language_id = 'python'

# store our own __main__ module, not 100% needed
# but python expects this in some places
_BPY_MAIN_OWN = True

def add_scrollback(text, text_type):
    for l in text.split('\n'):
        bpy.ops.console.scrollback_append(text=l.replace('\t', '    '),
            type=text_type)


def get_console(console_id):
    '''
    helper function for console operators
    currently each text datablock gets its own
    console - code.InteractiveConsole()
    ...which is stored in this function.

    console_id can be any hashable type
    '''
    from code import InteractiveConsole

    consoles = getattr(get_console, "consoles", None)
    hash_next = hash(bpy.context.manager)

    if consoles is None:
        consoles = get_console.consoles = {}
        get_console.consoles_namespace_hash = hash_next
    else:
        # check if clearning the namespace is needed to avoid a memory leak.
        # the window manager is normally loaded with new blend files
        # so this is a reasonable way to deal with namespace clearing.
        # bpy.data hashing is reset by undo so cant be used.
        hash_prev = getattr(get_console, "consoles_namespace_hash", 0)

        if hash_prev != hash_next:
            get_console.consoles_namespace_hash = hash_next
            consoles.clear()

    console_data = consoles.get(console_id)

    if console_data:
        console, stdout, stderr = console_data

        # XXX, bug in python 3.1.2 ? (worked in 3.1.1)
        # seems there is no way to clear StringIO objects for writing, have to make new ones each time.
        import io
        stdout = io.StringIO()
        stderr = io.StringIO()
    else:
        if _BPY_MAIN_OWN:
            import types
            bpy_main_mod = types.ModuleType("__main__")
            namespace = bpy_main_mod.__dict__
        else:
            namespace = {}
        
        namespace["__builtins__"] = sys.modules["builtins"]
        namespace["bpy"] = bpy
        namespace["C"] = bpy.context

        console = InteractiveConsole(locals=namespace, filename="<blender_console>")
        
        if _BPY_MAIN_OWN:
            console._bpy_main_mod = bpy_main_mod

        import io
        stdout = io.StringIO()
        stderr = io.StringIO()

        consoles[console_id] = console, stdout, stderr

    return console, stdout, stderr


# Both prompts must be the same length
PROMPT = '>>> '
PROMPT_MULTI = '... '


def execute(context):
    sc = context.space_data

    try:
        line_object = sc.history[-1]
    except:
        return {'CANCELLED'}

    if sc.console_type != 'PYTHON':
        return {'CANCELLED'}

    console, stdout, stderr = get_console(hash(context.region))

    # redirect output
    sys.stdout = stdout
    sys.stderr = stderr

    # dont allow the stdin to be used, can lock blender.
    stdin_backup = sys.stdin
    sys.stdin = None

    if _BPY_MAIN_OWN:
        main_mod_back = sys.modules["__main__"]
        sys.modules["__main__"] = console._bpy_main_mod

    # incase exception happens
    line = "" # incase of encodingf error
    is_multiline = False

    try:
        line = line_object.body

        # run the console, "\n" executes a multiline statement
        line_exec = line if line.strip() else "\n"

        is_multiline = console.push(line_exec)
    except:
        # unlikely, but this can happen with unicode errors for example.
        import traceback
        stderr.write(traceback.format_exc())

    if _BPY_MAIN_OWN:
        sys.modules["__main__"] = main_mod_back

    stdout.seek(0)
    stderr.seek(0)

    output = stdout.read()
    output_err = stderr.read()

    # cleanup
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    sys.last_traceback = None

    # So we can reuse, clear all data
    stdout.truncate(0)
    stderr.truncate(0)

    bpy.ops.console.scrollback_append(text=sc.prompt + line, type='INPUT')

    if is_multiline:
        sc.prompt = PROMPT_MULTI
    else:
        sc.prompt = PROMPT

    # insert a new blank line
    bpy.ops.console.history_append(text="", current_character=0,
        remove_duplicates=True)

    # Insert the output into the editor
    # not quite correct because the order might have changed,
    # but ok 99% of the time.
    if output:
        add_scrollback(output, 'OUTPUT')
    if output_err:
        add_scrollback(output_err, 'ERROR')

    # restore the stdin
    sys.stdin = stdin_backup

    return {'FINISHED'}


def autocomplete(context):
    from console import intellisense

    sc = context.space_data

    console = get_console(hash(context.region))[0]

    if not console:
        return {'CANCELLED'}

    if sc.console_type != 'PYTHON':
        return {'CANCELLED'}

    # dont allow the stdin to be used, can lock blender.
    # note: unlikely stdin would be used for autocomp. but its possible.
    stdin_backup = sys.stdin
    sys.stdin = None

    scrollback = ""
    scrollback_error = ""

    try:
        current_line = sc.history[-1]
        line = current_line.body

        # This function isnt aware of the text editor or being an operator
        # just does the autocomp then copy its results back
        current_line.body, current_line.current_character, scrollback = \
            intellisense.expand(
                line=current_line.body,
                cursor=current_line.current_character,
                namespace=console.locals,
                private=bpy.app.debug)
    except:
        # unlikely, but this can happen with unicode errors for example.
        # or if the api attribute access its self causes an error.
        import traceback
        scrollback_error = traceback.format_exc()

    # Separate automplete output by command prompts
    if scrollback != '':
        bpy.ops.console.scrollback_append(text=sc.prompt + current_line.body, type='INPUT')

    # Now we need to copy back the line from blender back into the
    # text editor. This will change when we dont use the text editor
    # anymore
    if scrollback:
        add_scrollback(scrollback, 'INFO')

    if scrollback_error:
        add_scrollback(scrollback_error, 'ERROR')

    # restore the stdin
    sys.stdin = stdin_backup

    context.area.tag_redraw()

    return {'FINISHED'}


def banner(context):
    sc = context.space_data
    version_string = sys.version.strip().replace('\n', ' ')

    add_scrollback(" * Python Interactive Console %s *" % version_string, 'OUTPUT')
    add_scrollback("Command History:  Up/Down Arrow", 'OUTPUT')
    add_scrollback("Cursor:           Left/Right Home/End", 'OUTPUT')
    add_scrollback("Remove:           Backspace/Delete", 'OUTPUT')
    add_scrollback("Execute:          Enter", 'OUTPUT')
    add_scrollback("Autocomplete:     Ctrl+Space", 'OUTPUT')
    add_scrollback("Ctrl +/-  Wheel:  Zoom", 'OUTPUT')
    add_scrollback("Builtin Modules: bpy, bpy.data, bpy.ops, bpy.props, bpy.types, bpy.context, bgl, blf, mathutils, geometry", 'OUTPUT')
    add_scrollback("", 'OUTPUT')
    add_scrollback("  WARNING!!! Blender 2.5 API is subject to change, see API reference for more info.", 'ERROR')
    add_scrollback("", 'OUTPUT')
    sc.prompt = PROMPT

    return {'FINISHED'}


def register():
    pass


def unregister():
    pass


if __name__ == "__main__":
    register()
