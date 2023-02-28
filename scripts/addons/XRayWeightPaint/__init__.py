

bl_info = {
    "name": "X Ray Weight Paint",
    "author": "BlenderBoi",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D View",
    "description": "Add Weight Paint Button in a More Convinient Place",
    "warning": "",
    "doc_url": "",
    "category": "Utility",
}



from . import WeightPaintBrush_Menu


modules =  [WeightPaintBrush_Menu] 

def register():


    for module in modules:
        module.register()

def unregister():

    for module in modules:
        module.unregister()

if __name__ == "__main__":
    register()
