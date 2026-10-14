from . import display_image
from . import id_panel
from . import node_stats
from . import normal_node
from . import simplify_nodes

def register():
    display_image.register()
    id_panel.register()
    node_stats.register()
    normal_node.register()
    simplify_nodes.register()

def unregister():
    simplify_nodes.unregister()
    node_stats.unregister()
    normal_node.unregister()
    id_panel.unregister()
    display_image.unregister()
