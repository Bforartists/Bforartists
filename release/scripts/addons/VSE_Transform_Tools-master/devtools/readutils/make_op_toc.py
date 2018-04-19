import math

def reflow_paragraph(text, space, leading_space=''):
    '''
    Reflow a flattened paragraph so it fits inside horizontal
    space
    '''
    words = text.split(' ')
    growing_string = leading_space
    output_list = []

    while len(words) > 0:
        if growing_string == leading_space:
            growing_string += words[0]
            words.pop(0)
        elif len(growing_string + ' ' + words[0]) <= space:
            growing_string += ' ' + words[0]
            words.pop(0)
        else:
            output_list.append(growing_string + '\n')
            growing_string = leading_space
    output_list.append(growing_string)
    return ''.join(output_list)


def make_toc_label(label, description):
    description = reflow_paragraph(description, 31)
    
    hla = label.replace(' ', '_')
    html_link = ''.join([
        '<a name="top_', hla, '" href="#', hla, '" title="' + description + '">',
        label, '</a>'])
    return html_link

def make_op_toc(json):
    """
    Build a Table of links 
    """
    toc = ['<table>']
    
    labels = []
    
    for key in json.keys():
        label = json[key]['label']
        description = json[key]['description']
        labels.append(make_toc_label(label, description))
    
    columns = [[], [], [], []]
    row_count = math.ceil(len(labels) / len(columns))
    
    i = 0
    col = 0
    while i < len(labels):
        for x in range(row_count):
            try:
                columns[col].append(labels[i])
                i += 1
            except IndexError:
                break
        col += 1
    
    dead_column = False
    column_width = str(int((1 / len(columns)) * 888)) + 'px'
    for row in range(row_count):
        toc.append('    <tr>')
        
        for col in range(len(columns)):
            try:
                toc.append('        <td width=' + column_width + '>' + columns[col][row] + '</td>')
            except IndexError:
                if dead_column == False:
                    remaining_rows = row_count - row
                    toc.append('        <td width=' + column_width + ' rowspan="' + str(remaining_rows) + '"></td>')
                    dead_column = True
        toc.append('    </tr>')
    toc.append('</table>')
    
    return '\n'.join(toc)
    
