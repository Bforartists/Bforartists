# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .utils.global_settings import SequenceTypes
from .utils.doc import doc_name, doc_idname, doc_brief, doc_description


class POWER_SEQUENCER_OT_select_related_strips(bpy.types.Operator):
    """
    *brief* Find and select all strips related to the selection


    Find and select effects related to the selection, but also inputs of selected effects.
    This helps to then copy or duplicate strips with all attached effects.
    """

    doc = {
        "name": doc_name(__qualname__),
        "demo": "",
        "description": doc_description(__doc__),
        "shortcuts": [],
        "keymap": "Sequencer",
    }
    bl_idname = doc_idname(__qualname__)
    bl_label = doc["name"]
    bl_description = doc_brief(doc["description"])
    bl_options = {"REGISTER", "UNDO"}

    find_all: bpy.props.BoolProperty(
        name="Find All",
        description=(
            "Find all related strips recursively so that you can copy the selection"
            " without getting an error from Blender"
        ),
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_sequences

    def execute(self, context):
        if self.find_all:
            related_strips = set()
            for s in context.selected_sequences:
                self.find_neighbours_recursive(related_strips, s, context)
        else:
            related_strips = []
            # Only select direct neighbours and attached effects
            effects = [s for s in context.sequences if s.type in SequenceTypes.EFFECT]
            found_effects = self.find_related_effects(context.selected_sequences, effects)
            related_strips.extend(found_effects)
            while len(found_effects) > 0:
                found_effects = self.find_related_effects(found_effects, effects)
                related_strips.extend(found_effects)
        for s in related_strips:
            s.select = True
        return {"FINISHED"}

    def find_neighbours_recursive(self, visited, strip, context):
        """
        Performs a depth first search traversal to the graph of strips, to find
        all related strips.
        Args:
        - visited: A set with all the strips that have been visited.
        - strip: The strip to start the search from.
        """
        visited.add(strip)
        neighbours = self.find_neighbours(strip, context)
        for s in neighbours:
            if s not in visited:
                self.find_neighbours_recursive(visited, s, context)

    def find_neighbours(self, strip, context):
        """
        Strips and their effect strips define a graph, where each node is a
        strip and edges are their connections. It finds all the neighbours of a
        strip in the graph, and *sometimes neighbours of neighbours and so on*.
        *In order to find the neighbours of a strip the
        bpy.ops.transform.seq_slide operator is used, and usually finds many
        levels of neighbours, but always finds the first level, which is needed,
        the other levels are redundant, but are included for brevity reasons.
        Args:
        - strip: The strip to find all its neighbours.
        Returns: A list with all the neighbours of the strip and sometimes
                 neighbours of neighbours and so on.
        """
        # Respects initial selection
        init_selected_strips = [s for s in context.selected_sequences]

        neighbours = []
        bpy.ops.sequencer.select_all(action="DESELECT")
        strip.select = True
        bpy.ops.transform.seq_slide(value=(0, 0))
        strip.select = False
        for s in context.selected_sequences:
            neighbours.append(s)

        try:
            neighbours.append(strip.input_1)
            neighbours.append(strip.input_2)
        except Exception:
            pass

        bpy.ops.sequencer.select_all(action="DESELECT")
        for s in init_selected_strips:
            s.select = True

        return neighbours

    def find_related_effects(self, sequences, effects):
        found = []
        for s in sequences:
            for e in effects:
                try:
                    if e.input_1 == s:
                        found.append(e)
                except Exception:
                    continue
                try:
                    if e.input_2 == s:
                        found.append(e)
                except Exception:
                    continue
        return found
