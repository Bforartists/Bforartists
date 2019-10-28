from bpy.types import PropertyGroup
from bpy.props import StringProperty

layer_collections = {}

collection_tree = []

expanded = []

max_lvl = 0

def get_max_lvl():
    return max_lvl

class CMListCollection(PropertyGroup):
    name: StringProperty()


def update_collection_tree(context):
    global max_lvl
    collection_tree.clear()
    layer_collections.clear()
    max_lvl = 0
    
    init_laycol_list = context.view_layer.layer_collection.children
    
    master_laycol = {"id": 0,
                     "name": context.view_layer.layer_collection.name,
                     "lvl": -1,
                     "visible": True,
                     "has_children": True,
                     "expanded": True,
                     "parent": None,
                     "children": [],
                     "ptr": context.view_layer.layer_collection
                     }
    
    get_all_collections(context, init_laycol_list, master_laycol, collection_tree, visible=True)


def get_all_collections(context, collections, parent, tree, level=0, visible=False):
    for item in collections:
        laycol = {"id": len(layer_collections) +1,
                  "name": item.name,
                  "lvl": level,
                  "visible":  visible,
                  "has_children": False,
                  "expanded": False,
                  "parent": parent,
                  "children": [],
                  "ptr": item
                  }
        
        layer_collections[item.name] = laycol
        tree.append(laycol)
        
        if len(item.children) > 0:
            global max_lvl
            max_lvl += 1
            laycol["has_children"] = True
            
            if item.name in expanded and laycol["visible"]:
                laycol["expanded"] = True
                get_all_collections(context, item.children, laycol, laycol["children"], level+1, visible=True)
                
            else:
                get_all_collections(context, item.children, laycol, laycol["children"], level+1)


def update_property_group(context):
    update_collection_tree(context)
    context.scene.CMListCollection.clear()
    create_property_group(context, collection_tree)


def create_property_group(context, tree):
    global in_filter
    
    for laycol in tree:
        new_cm_listitem = context.scene.CMListCollection.add()
        new_cm_listitem.name = laycol["name"]
    
        if laycol["has_children"]:
            create_property_group(context, laycol["children"])
