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

'''
Define the command 'print_struct_c99' for gdb,
useful for creating a literal for a nested runtime struct.

Example use:

   (gdb) source source/tools/utils/gdb_struct_repr_c99.py
   (gdb) print_struct_c99 scene->toolsettings
'''

class PrintStructC99(gdb.Command):
    def __init__(self):
        super(PrintStructC99, self).__init__(
            "print_struct_c99",
            gdb.COMMAND_USER,
        )

    def get_count_heading(self, string):
        for i, s in enumerate(string):
            if s != ' ':
                break
        return i

    def extract_typename(self, string):
        first_line = string.split('\n')[0]
        return first_line.split('=')[1][:-1].strip()

    def invoke(self, arg, from_tty):
        ret_ptype = gdb.execute('ptype {}'.format(arg), to_string=True)
        tname = self.extract_typename(ret_ptype)
        print('{} {} = {{'.format(tname, arg))
        r = gdb.execute('p {}'.format(arg), to_string=True)
        r = r.split('\n')
        for rr in r[1:]:
            if '=' not in rr:
                print(rr)
                continue
            hs = self.get_count_heading(rr)
            rr_s = rr.strip().split('=', 1)
            rr_rval = rr_s[1].strip()
            print(' ' * hs + '.' + rr_s[0] + '= ' + rr_rval)


print('Running GDB from: %s\n' % (gdb.PYTHONDIR))
gdb.execute("set print pretty")
gdb.execute('set pagination off')
gdb.execute('set print repeats 0')
gdb.execute('set print elements unlimited')
# instantiate
PrintStructC99()
