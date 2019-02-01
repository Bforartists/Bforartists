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

def operation_wrap(args):
    fn, text_operation = args
    with open(fn, "r", encoding="utf-8") as f:
        data_src = f.read()
        data_dst = text_operation(fn, data_src)

    if data_dst is None or (data_src == data_dst):
        return

    with open(fn, "w", encoding="utf-8") as f:
        f.write(data_dst)

def run(*,
        directories,
        is_text,
        text_operation,
        use_multiprocess,
):
    print(directories)

    import os

    def source_files(path):
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                ext = os.path.splitext(filename)[1]
                filepath = os.path.join(dirpath, filename)
                if is_text(filepath):
                    yield filepath


    if use_multiprocess:
        args = [
            (fn, text_operation) for directory in directories
            for fn in source_files(directory)
        ]
        import multiprocessing
        job_total = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=job_total * 2)
        pool.map(operation_wrap, args)
    else:
        for directory in directories:
            for fn in source_files(directory):
                operation_wrap((fn, text_operation))
