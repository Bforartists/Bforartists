import os

files = []
for file in os.listdir(os.getcwd()):
    if file.endswith('.py') and not file in ['_make_util_init.py', '__init__.py']:
        
        fname = os.path.splitext(file)[0]
        
        files.append('from .' + fname + ' import ' + fname)

f = open('__init__.py', 'w')
f.write('\n'.join(sorted(files)))
f.close()
        
