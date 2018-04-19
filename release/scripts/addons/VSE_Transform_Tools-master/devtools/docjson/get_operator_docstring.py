def get_operator_docstring(file):
    """
    Get the first string inside a triple quote in the file
    """
    with open(file, 'r') as f:
        text = f.read()
    try:
        docstring = text.split('"""')[1].split('"""')[0]
    except IndexError:
        return ""
    
    lines = docstring.split('\n')
    for i in range(len(lines)):
        lines[i] = lines[i].lstrip()
    return '\n'.join(lines).strip()
