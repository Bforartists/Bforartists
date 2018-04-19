import os
from docjson import make_json

ops_path = os.path.join(os.getcwd(), '../', 'operators')
output_path = os.path.join(os.getcwd(), 'info.json')

make_json(ops_path, output_path=output_path)
