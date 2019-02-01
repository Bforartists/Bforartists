#!/usr/bin/env python3
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

"""
Example:
  ./source/tools/utils/header_clean.py /src/cmake_debug --match ".*/editmesh_.*"

Note: currently this is limited to paths in "source/blender",
we could change this if it's needed.

Ensures headers are NOT removed:

- They aren't used in the current build configuration.
- They are needed but happen to be indirectly included by another header.
- They use '#include <...>', instead of quotes (keep system headers).
"""

import os
import sys
import subprocess
import re

# Copied form elsewhere...


def cmake_cache_var(cmake_dir, var):
    cache_file = open(os.path.join(cmake_dir, "CMakeCache.txt"), encoding='utf-8')
    lines = [l_strip for l in cache_file for l_strip in (l.strip(),)
             if l_strip if not l_strip.startswith("//") if not l_strip.startswith("#")]
    cache_file.close()

    for l in lines:
        if l.split(":")[0] == var:
            return l.split("=", 1)[-1]
    return None


# RE_CFILE_SEARCH = re.search('<title>(.*)</title>', html, re.IGNORECASE)
RE_CFILE_SEARCH = re.compile(r"\s\-c\s([\S]+)")


def process_commands(cmake_dir, data):
    compiler = cmake_cache_var(cmake_dir, "CMAKE_C_COMPILER")  # could do CXX too
    file_args = []

    for l in data:
        if compiler in l:
            # extract -c FILE
            # c_file = l.split(" -c ", 1)[1].split()[0]
            c_file_search = re.search(RE_CFILE_SEARCH, l)
            if c_file_search is not None:
                c_file = c_file_search.group(1)
                file_args.append((c_file, l))
            else:
                # could print, NO C FILE FOUND?
                pass

            print(c_file)

    file_args.sort()

    return file_args


def find_build_args_ninja(build_dir):
    cmake_dir = build_dir
    make_exe = "ninja"
    process = subprocess.Popen(
        [make_exe, "-t", "commands"],
        stdout=subprocess.PIPE,
        cwd=build_dir,
    )
    while process.poll():
        time.sleep(1)

    out = process.stdout.read()
    process.stdout.close()
    # print("done!", len(out), "bytes")
    data = out.decode("utf-8", errors="ignore").split("\n")
    return process_commands(cmake_dir, data)


def find_build_args_make(build_dir):
    make_exe = "make"
    process = subprocess.Popen(
        [make_exe, "--always-make", "--dry-run", "--keep-going", "VERBOSE=1"],
        stdout=subprocess.PIPE,
        cwd=build_dir,
    )
    while process.poll():
        time.sleep(1)

    out = process.stdout.read()
    process.stdout.close()

    # print("done!", len(out), "bytes")
    data = out.decode("utf-8", errors="ignore").split("\n")
    return process_commands(cmake_dir, data)


def wash_source_const(pair):
    (source, build_args) = pair
    # Here is where the fun happens, try make changes and see what happens
    # 'char *' -> 'const char *'
    lines = open(source, 'r', encoding='utf-8').read().split("\n")

    def write_lines(lines):
        with open(source, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    re_c = re.compile(r"([\s|, |\(])(\b[A-Za-z0-9_]+)(\s+[a-zA-Z0-9_]+\[\d+\])")

    for i, l in enumerate(lines):
        l_strip = l.strip()
        if len(l_strip) == len(l):
            continue

        # -------- HACKY but works OK
        if ";" in l_strip:
            continue
        '''
        a = l_strip.find("=")
        if a == -1:
            a = 10000
        b = l_strip.find(";")
        if b == -1:
            b == 10000
        if " *" not in l_strip[:min(a, b)]:
            continue
        '''

        # for t in ("bool", "char", "short", "int", "long", "float", "double"):
        # if t in l_strip:
        changed = True
        while changed:
            changed = False
            l_prev = l
            t = r"[A-Za-z0-9_]+"
            l_new = re.sub(re_c, r"\1const \2\3", l, 1)

            if l_new == l_prev:
                break
            if "const const" in l_new:
                break

            l_test = re.sub(re_c, r"\1TESTME \2\3", l, 1)
            # l = l.replace(" %s *" % t, " const %s *" % t, 1)
            # l_test = l.replace(" %s " % t, "TESTME", 1)

            print(source, i + 1, l)
            # first check this is even getting compiled
            lines[i] = l_test
            write_lines(lines)

            # ensure this fails!, else we may be in an `#if 0` block
            ret = os.system(build_args)
            if ret != 0:
                lines[i] = l_new
                write_lines(lines)
                ret = os.system(build_args)
                if ret != 0:
                    lines[i] = l_prev
                    write_lines(lines)
                else:
                    print("success!")
                    l = l_new
                    changed = True
            else:
                lines[i] = l_prev
                write_lines(lines)

    # print("building:", c)


def wash_source_replace(pair):
    (source, build_args) = pair
    # Here is where the fun happens, try make changes and see what happens
    # 'char *' -> 'const char *'
    lines = open(source, 'r', encoding='utf-8').read().split("\n")

    def write_lines(lines):
        with open(source, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    str_src = "CTX_wm_screen(C)"
    str_dst = "sc"

    for i, l in enumerate(lines):

        if str_src not in l:
            continue

        l_prev = l
        l_new = l_prev.replace(str_src, str_dst)

        if l_new == l_prev:
            continue
        # avoid 'scene = scene'
        if (str_dst + "=" + str_dst) in l_new.replace(" ", ""):
            continue

        l_test = l_prev.replace(str_src, "TESTME")

        print(source, i + 1, l)
        # first check this is even getting compiled
        lines[i] = l_test
        write_lines(lines)

        # ensure this fails!, else we may be in an `#if 0` block
        ret = os.system(build_args)
        if ret != 0:
            lines[i] = l_new
            write_lines(lines)
            ret = os.system(build_args)
            if ret != 0:
                lines[i] = l_prev
                write_lines(lines)
            else:
                print("success!")
                l = l_new
                changed = True
        else:
            lines[i] = l_prev
            write_lines(lines)


# Never remove these headers
HEADER_BLACKLIST = {
    "BLI_strict_flags.h",
    "BLI_utildefines.h",
}


def wash_source_include(pair):
    (source, build_args) = pair
    # Here is where the fun happens, try make changes and see what happens
    # 'char *' -> 'const char *'
    lines = open(source, 'r', encoding='utf-8').read().split("\n")

    def write_lines(lines):
        with open(source, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    re_c = re.compile(r"\s*#\s*include\s+\"([a-zA-Z0-9_\-\.]+)\"")

    i = 0
    while i < len(lines):
        l = lines[i]

        # if "\"BKE_" not in l:
        #    i += 1
        #    continue
        m = re.match(re_c, l)
        if m is None:
            i += 1
            continue
        l_header = m.group(1)
        del m

        if l_header in HEADER_BLACKLIST:
            i += 1
            continue

        l_prev = l
        l_new = ""

        # this must fail!, else if '#if 0' or commented
        l_test = "#include <THISISMISSING>"

        print(source, i + 1, l)
        # first check this is even getting compiled
        lines[i] = l_test
        write_lines(lines)

        # ensure this fails!, else we may be in an `#if 0` block
        ret = os.system(build_args)
        if ret != 0:
            lines[i] = l_new

            # redefine to cause error
            # if we're already including indirectly
            l_guard = l_header.upper().replace(".", "_").replace("-", "_")
            l_bad_guard = "#define __%s__" % l_guard
            del l_guard

            # add, remove bad definition of include guard
            # we the include is indirect, this will fail.
            lines.insert(0, l_bad_guard)  # add guard
            write_lines(lines)
            lines.pop(0)  # remove guard

            del l_bad_guard

            ret = os.system(build_args + " -Wno-unused-macros -Werror=missing-prototypes")
            if ret != 0:
                lines[i] = l_prev
                write_lines(lines)
            else:
                print("success!")
                l = l_new
                changed = True

                del lines[i]

                write_lines(lines)

                i -= 1
        else:
            lines[i] = l_prev
            write_lines(lines)
        i += 1


def header_clean_all(build_dir, regex_list):
    # currently only supports ninja or makefiles
    build_file_ninja = os.path.join(build_dir, "build.ninja")
    build_file_make = os.path.join(build_dir, "Makefile")
    if os.path.exists(build_file_ninja):
        print("Using Ninja")
        args = find_build_args_ninja(build_dir)
    elif os.path.exists(build_file_make):
        print("Using Make")
        args = find_build_args_make(build_dir)
    else:
        sys.stderr.write(
            "Can't find Ninja or Makefile (%r or %r), aborting" %
            (build_file_ninja, build_file_make)
        )
        return
    # needed for when arguments are referenced relatively
    os.chdir(build_dir)

    # Weak, but we probably don't want to handle extern.
    # this limit could be removed.
    source_path = os.path.join("blender", "source")

    def test_path(c):
        index = c.rfind(source_path)
        if index == -1:
            return False
        # Remove first part of the path, we don't want to match
        # against paths in Blender's repo.
        c_strip = c[index:]
        for regex in regex_list:
            if regex.match(c_strip) is not None:
                return True
        return False

    if 1:
        args = [(c, build_args) for (c, build_args) in args if test_path(c)]

        import multiprocessing
        job_total = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=job_total * 2)
        pool.map(wash_source_include, args)
    else:
        # now we have commands
        for i, (c, build_args) in enumerate(args):
            if (source_path in c) and ("rna_" not in c):
                wash_source_include((c, build_args))


def create_parser():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "build_dir",
        help="list of files or directories to check",
    )
    parser.add_argument(
        "--match",
        nargs='+',
        required=True,
        metavar="REGEX",
        help="Match file paths against this expression",
    )
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    build_dir = args.build_dir
    regex_list = []

    for i, expr in enumerate(args.match):
        try:
            regex_list.append(re.compile(expr))
        except Exception as ex:
            print(f"Error in expression: {expr}\n  {ex}")
            return 1

    return header_clean_all(build_dir, regex_list)


if __name__ == "__main__":
    sys.exit(main())
