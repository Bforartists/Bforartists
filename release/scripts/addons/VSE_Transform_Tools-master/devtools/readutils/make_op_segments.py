from markdown2 import markdown

def make_seg_label(label):
    hla = label.replace(' ', '_')
    seg_label = ''.join([
        '    ', '<h3>', '<a name="', hla, '" href="#top_', hla, '">',
        label, '</a>', '</h3>'])
    return seg_label


def extract_demo_images(docstring):
    images = []
    lines = docstring.split('\n')
    for line in lines:
        if len(images) > 0 and not line.strip() == '':
            break
        if line.lstrip().startswith('![Demo]'):
            image = markdown(line.strip()).strip()
            image = image.replace('<p>', '')
            image = image.replace('</p>', '')
            image = image.replace(' />', '>')

            images.append(image)
    return images


def make_shortcuts_table(shortcuts, label, demo_images):
    hotkeys = []
    functions = []
    for key in shortcuts.keys():
        hotkeys.append(shortcuts[key].replace('keys=', '').split(';')[0].split(' '))
        
        if "function=" in shortcuts[key]:
            functions.append(shortcuts[key].split(';')[-1].replace('function=', '').strip())
        
        else:
            functions.append(label)
    
    for i in range(len(hotkeys)):
        for x in range(len(hotkeys[i])):
            hotkeys[i][x] = '<img src="https://cdn.rawgit.com/doakey3/Keyboard-SVGs/master/images/' + hotkeys[i][x].upper() + '.png" alt="' + hotkeys[i][x] + '">'
    
    hotkeys_width = str(int((888 - 256) * 0.33)) + 'px'
    function_width = str(int((888 - 256) * 0.66)) + 'px'
    table = ['<table>']
    table.append('    <tr>')
    table.append('        <th width=' + hotkeys_width + '>Shortcut</th>')
    if len(functions) > 0:
        table.append('        <th width=' + function_width + '>Function</th>')
    if len(demo_images) > 0:
        table.append('        <th width=' + str(len(demo_images) * 256) + 'px>Demo</th>')
        
    for i in range(len(hotkeys)):
        table.append('    <tr>')
        
        table.append('        <td align="center">' + ''.join(hotkeys[i]) + '</td>')
        if len(functions) > 0:
            table.append('        <td>' + functions[i] + '</td>')
        
        if i == 0 and len(demo_images) > 0:
            table.append('        <td align="center" rowspan="' + str(len(hotkeys)) + '">' + ''.join(demo_images) + '</td>')
            
        table.append('    </tr>')
    table.append('</table>')
    return '\n'.join(table)


def make_shortcut_table(info):
    """
    Make the table containing hotkey info
    """

    demo_images = extract_demo_images(info['docstring'])
    label = info['label']
    table = make_shortcuts_table(info['shortcuts'], label, demo_images)

    lines = table.split('\n')
    for i in range(len(lines)):
        lines[i] = '    ' + lines[i]
    
    return '\n'.join(lines)


def make_op_segments(json):
    """
    Make all the operator segments in the README
    """
    segments = []
    for key in json.keys():
        label = make_seg_label(json[key]['label'])
        shortcut_table = make_shortcut_table(json[key])
        
        docstring = json[key]['docstring']
        lines = docstring.split('\n')
        i = 0
        while i < len(lines):
            if lines[i].lstrip().startswith('![Demo]'):
                lines.pop(i)
            else:
                i += 1
        docstring = markdown('\n'.join(lines))
        
        segments.append('\n'.join([label, docstring, shortcut_table]))
    
    return '\n'.join(segments)
            
