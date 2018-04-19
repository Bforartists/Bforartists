def get_operator_tag(file, target):
    """
    Gets a string tag item. For example, give it the filepath to 
    add_crossfade.py and "bl_idname" as the target
    and it will return "power_sequencer.add_crossfade"
    """
    with open(file, 'r') as f:
        text = f.read()
        
    label = ""
    lines = text.split('\n')
    for line in lines:
        if line.lstrip().startswith(target):
            if line.strip().startswith(target + ' ='):
                label = line.replace(target + ' =', '').strip()
            elif line.strip().startswith(target + '='):
                label = line.replace(target + '=', '').strip()
                
            to_erase = "'"
            if label.startswith('"""'):
                to_erase = '"""'
            elif label.startswith("'''"):
                to_erase = "'''"
            elif label.startswith('"'):
                to_erase = '"'
            return label.replace(to_erase, "").strip()
    return label
