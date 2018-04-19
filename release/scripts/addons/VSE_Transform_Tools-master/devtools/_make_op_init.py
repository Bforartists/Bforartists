import os

def capitalize(word):
    if len(word) > 1:
        word = word[0].upper() + word[1::]
        return word
    else:
        return word.upper()

files = []
for file in os.listdir(os.getcwd()):
    if file.endswith('.py') and not file in ['_make_op_init.py', '_op_consistency_checker.py', '__init__.py']:

        fname = os.path.splitext(file)[0]
        expected_classname_split = fname.split('_')
        for i in range(len(expected_classname_split)):
            expected_classname_split[i] = capitalize(expected_classname_split[i])

        expected_classname = ''.join(expected_classname_split)

        files.append('from .' + fname + ' import ' + expected_classname)

f = open('__init__.py', 'w')
f.write('\n'.join(sorted(files)))
f.close()
