##
##
## Customized makefreeze for NaN
##
##
## 1.11.2001, strubi@blender.nl
##
##
import marshal
import string
import bkfile


# Write a file containing frozen code for the modules in the dictionary.

header = """
#include "Python.h"

static struct _frozen _PyImport_FrozenModules[] = {
"""
trailer = """\
    {0, 0, 0} /* sentinel */
};
"""

# if __debug__ == 0 (i.e. -O option given), set Py_OptimizeFlag in frozen app.
main_entry_point = """
int
main(argc, argv)
    int argc;
    char **argv;
{
	extern int Py_FrozenMain(int, char **);
        init_frozen_modules();
        return Py_FrozenMain(argc, argv);
}

"""

default_entry_point = """
void
init_frozenmodules(void)
{
""" + ((not __debug__ and """
        Py_OptimizeFlag++;
""") or "")  + """
        PyImport_FrozenModules = _PyImport_FrozenModules;
}
"""

HEADER = """
/* This is a generated file, containing frozen bytecode.
 * Check $(HOME)/develop/intern/python/freeze/README for more information.
 */

"""

def makefreeze(base, dict, debug=0, entry_point = None, exclude_main = 0):
    if entry_point is None: entry_point = default_entry_point
    done = []
    files = []
    mods = dict.keys()
    if exclude_main:
	    mods.remove("__main__")
    mods.sort()
    for mod in mods:
        m = dict[mod]
        mangled = string.join(string.split(mod, "."), "__")
        if m.__code__:
            file = 'M_' + mangled + '.c'
            outfp = bkfile.open(base + file, 'w')
            outfp.write(HEADER)
            files.append(file)
            if debug:
                print "freezing", mod, "..."
            str = marshal.dumps(m.__code__)
            size = len(str)
            if m.__path__:
                # Indicate package by negative size
                size = -size
            done.append((mod, mangled, size))
            writecode(outfp, mangled, str)
            outfp.close()
    if debug:
        print "generating table of frozen modules"
    outfp = bkfile.open(base + 'frozen.c', 'w')
    for mod, mangled, size in done:
        outfp.write('extern unsigned char M_%s[];\n' % mangled)
    outfp.write(header)
    for mod, mangled, size in done:
        outfp.write('\t{"%s", M_%s, %d},\n' % (mod, mangled, size))
    outfp.write(trailer)
    outfp.write(entry_point)
    outfp.close()
    #outfp = bkfile.open(base + 'main.c', 'w')
    #outfp.write(main_entry_point)
    #outfp.close()
    return files



# Write a C initializer for a module containing the frozen python code.
# The array is called M_<mod>.

def writecode(outfp, mod, str):
    outfp.write('unsigned char M_%s[] = {' % mod)
    for i in range(0, len(str), 16):
        outfp.write('\n\t')
        for c in str[i:i+16]:
            outfp.write('%d,' % ord(c))
    outfp.write('\n};\n')

## def writecode(outfp, mod, str):
##     outfp.write('unsigned char M_%s[%d] = "%s";\n' % (mod, len(str),
##     string.join(map(lambda s: `s`[1:-1], string.split(str, '"')), '\\"')))
