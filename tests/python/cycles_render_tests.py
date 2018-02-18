#!/usr/bin/env python3
# Apache License, Version 2.0

import argparse
import os
import shlex
import shutil
import subprocess
import sys


def render_file(filepath, output_filepath):
    dirname = os.path.dirname(filepath)
    basedir = os.path.dirname(dirname)
    subject = os.path.basename(dirname)

    custom_args = os.getenv('CYCLESTEST_ARGS')
    custom_args = shlex.split(custom_args) if custom_args else []

    # OSL and GPU examples
    # custom_args += ["--python-expr", "import bpy; bpy.context.scene.cycles.shading_system = True"]
    # custom_args += ["--python-expr", "import bpy; bpy.context.scene.cycles.device = 'GPU'"]

    frame_filepath = output_filepath + '0001.png'

    if subject == 'opengl':
        command = [
            BLENDER,
            "--window-geometry", "0", "0", "1", "1",
            "-noaudio",
            "--factory-startup",
            "--enable-autoexec",
            filepath,
            "-E", "CYCLES"]
        command += custom_args
        command += [
            "-o", output_filepath,
            "-F", "PNG",
            '--python', os.path.join(basedir,
                                     "util",
                                     "render_opengl.py")]
    elif subject == 'bake':
        command = [
            BLENDER,
            "-b",
            "-noaudio",
            "--factory-startup",
            "--enable-autoexec",
            filepath,
            "-E", "CYCLES"]
        command += custom_args
        command += [
            "-o", output_filepath,
            "-F", "PNG",
            '--python', os.path.join(basedir,
                                     "util",
                                     "render_bake.py")]
    else:
        command = [
            BLENDER,
            "--background",
            "-noaudio",
            "--factory-startup",
            "--enable-autoexec",
            filepath,
            "-E", "CYCLES"]
        command += custom_args
        command += [
            "-o", output_filepath,
            "-F", "PNG",
            "-f", "1"]

    try:
        # Success
        output = subprocess.check_output(command)
        if os.path.exists(frame_filepath):
            shutil.copy(frame_filepath, output_filepath)
            os.remove(frame_filepath)
        if VERBOSE:
            print(output.decode("utf-8"))
        return None
    except subprocess.CalledProcessError as e:
        # Error
        if os.path.exists(frame_filepath):
            os.remove(frame_filepath)
        if VERBOSE:
            print(e.output.decode("utf-8"))
        if b"Error: engine not found" in e.output:
            return "NO_ENGINE"
        elif b"blender probably wont start" in e.output:
            return "NO_START"
        return "CRASH"
    except BaseException as e:
        # Crash
        if os.path.exists(frame_filepath):
            os.remove(frame_filepath)
        if VERBOSE:
            print(e)
        return "CRASH"


def create_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-blender", nargs="+")
    parser.add_argument("-testdir", nargs=1)
    parser.add_argument("-outdir", nargs=1)
    parser.add_argument("-idiff", nargs=1)
    return parser


def main():
    parser = create_argparse()
    args = parser.parse_args()

    global BLENDER, VERBOSE

    BLENDER = args.blender[0]
    VERBOSE = os.environ.get("BLENDER_VERBOSE") is not None

    test_dir = args.testdir[0]
    idiff = args.idiff[0]
    output_dir = args.outdir[0]

    from modules import render_report
    report = render_report.Report("Cycles Test Report", output_dir, idiff)
    report.set_pixelated(True)
    ok = report.run(test_dir, render_file)

    sys.exit(not ok)


if __name__ == "__main__":
    main()
