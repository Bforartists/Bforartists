# Copyright 2015 Théo Friberg under GNU GPL 3

import json

def readNodes(file):
    with open(file, "r") as data_file:
        return json.load(data_file)

def inflateFile(mat, fileToInflate, x=0, y=0):

    """
This method sets up a material saved to a JSON file. It returns a dictionary of
nodes with their labels as keys. The nodes are added to the specified material.

_Usage_: inflateFile(<reference to material the nodes are added to>,
<path of the file to load>, [optional <translation of the final node setup on the x axis>, <translation of the final node setup on the y axis>])

The syntax of the JSON file must be as follows:

1. Opening declaration (this may later be extended to create operators automatically and contain operator metadata):

{
"NodeSetup":[

2. Nodes as follows

{
    "label": "<label for the node>", - the node's mandatory identifier
    "type": "<the type of the node>, - the node's type (mandatory)
    "location": [<x>, <y>], - the node's mandatory location
    "in": [
              [<node>, <output>, (mandatoy) <input>],
                              <etc.>
          ] - (optional) Links going in to the node. Parameters:

            * The node whose output we take
            * Which output we take (can either be the display name, or
              the index of the output. In the former case, must be written
              as such: "\"<name>\"". In the later case, can be written as
              either <index> or "<index>".)
            * (optional) The input the connection goes into. The syntax is
              as per above. If omitted, links go into inputs in numerical
              order from top to bottom.
},

<etc.>

Note: Nodes can be accessed in more depth. For accessing the blend_mode of
a MixRGB, for example, one would write eg. (python):

    <node>.blend_mode = "MULTIPLY"

From JSON, this can be written as:

    "blend_mode": "\"MULTIPLY\""

For setting default values of inputs, use the following syntaxes:

    "inputs[0].default_value": 1
or

    "inputs[\"Color\"].default_value": [0, 1, 0, 1]

3. Closing declaration as follows:

]
}

The file is read using Python's built-in JSON parser, so indentation or line breaks are optional."""

    # Variables for the parsed JSON array, the nodes added and all the
    # nodes in the material, respectively.

    nodes_JSON = readNodes(fileToInflate)
    nodes_dict = {}
    nodes = mat.node_tree.nodes

    # We iterate a first time to create the nodes with their settings

    for node in nodes_JSON["NodeSetup"]:
        technical_name = node["type"]
        location = node["location"]
        nodes_dict[node["label"]] = nodes.new(technical_name)
        nodes_dict[node["label"]].location = (node["location"][0]+x,
                                              node["location"][1]+y)
        nodes_dict[node["label"]].name = node["label"]
        nodes_dict[node["label"]].label = node["label"]

        # The nodes' parameters can be generic, runnable Python.
        # This requires us to actually execute part of the files.

        for attribute in node.keys():
            if attribute not in ("in", "label", "type", "location"):
                exec("nodes_dict[node[\"label\"]]."+ attribute + " = " +
                     str(node[attribute]))

    # We create the links between the nodes
    # The syntax in the json is the following
    # "in": [
# ["<what node is plugged in>", <which of the nodes outputs is used, can be
# either string, as in "\"Color\"" or number, eg. 0 for the first output.>,
# <what input is this plugged to. Can be omitted for sequentially filling all
# inputs. If this has a value, it works like the previous value.>],
# <next inputs etc.>
#               ]

    links = mat.node_tree.links

    for node in nodes_JSON["NodeSetup"]:
        if "in" in node.keys(): # Does the node have links?
            i = 0
            while i < len(node["in"]): # We iterate over the links

                # Is a specific input specified?

                if len(node["in"][i]) == 3:

                    # Contruct and execute the line adding a link

                    exec ("links.new(nodes_dict[\"" + node["in"][i][0] +
                          "\"].outputs[" + str(node["in"][i][1]) +
                          "], nodes_dict[\"" + node["label"] + "\"].inputs["
                          + str(node["in"][i][2]) + "])")
                else:

                    # We don't have a specific input to hook up to

                    exec ("links.new(nodes_dict[\"" + node["in"][i][0] +
                          "\"].outputs[" + str(node["in"][i][1]) +
                          "], nodes_dict[\"" + node["label"] + "\"].inputs["
                           + str(i) + "])")
                i += 1

    # We return the nodes for purposes of further access to them

    return nodes_dict
