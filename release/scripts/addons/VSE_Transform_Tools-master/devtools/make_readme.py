import os
from markdown2 import markdown

from readutils.make_op_segments import make_op_segments
from readutils.make_op_toc import make_op_toc
from docjson import make_json

def make_toc_labels(labels):
    for i in range(len(labels)):
        hla = labels[i].replace(' ', '_')
        labels[i] = '<a name="top_' + hla + '" href="#' + hla + '">' + labels[i] + '</a>'
    return labels

ops_path = os.path.join(os.getcwd(), '../', 'operators')
info = make_json(ops_path)

title = '<h1 align="center">VSE_Transform_Tools</h1>'

installation = markdown("""
## Installation ##

1. Download the repository. Go to [Releases](https://github.com/doakey3/VSE_Transform_Tools/releases) for a stable version, or click the green button above to get the most recent (and potentially unstable) version.
2. Open Blender
3. Go to File > User Preferences > Addons
4. Click "Install From File" and navigate to the downloaded .zip file and install
5. Check the box next to "VSE_Transform_Tools"
6. Save User Settings so the addon remains active every time you open Blender
""".strip())

op_toc = make_op_toc(info)
op_segments = make_op_segments(info)

readme = '\n'.join([title, installation, "<h2>Operators</h2>", op_toc, op_segments])
lines = readme.split('\n')

for i in range(len(lines)):
    lines[i] = '    ' + lines[i]

readme = '.. raw:: html\n\n' + '\n'.join(lines)

with open('/home/doakey/Sync/Programming/VSE_Transform_Tools/README.rst', 'w') as f:
    f.write(readme)


