import bpy
from bpy.types import Operator
from bpy.props import (
    BoolProperty,
    StringProperty,
    IntProperty
    )

from .internals import *

class ExpandAllOperator(bpy.types.Operator):
    '''Expand/Collapse all collections'''
    bl_label = "Expand All Items"
    bl_idname = "view3d.expand_all_items"
    
    def execute(self, context):
        if len(expanded) > 0:
            expanded.clear()
        else:
            for laycol in layer_collections.values():
                if laycol["ptr"].children:
                    expanded.append(laycol["name"])
        
        # set selected row to the first row and update tree view
        context.scene.CMListIndex = 0
        update_property_group(context)
        
        return {'FINISHED'}


class ExpandSublevelOperator(bpy.types.Operator):
    '''Expand/Collapse sublevel. Shift-Click to expand/collapse all sublevels'''
    bl_label = "Expand Sublevel Items"
    bl_idname = "view3d.expand_sublevel"
    
    expand: BoolProperty()
    name: StringProperty()
    index: IntProperty()
    
    def invoke(self, context, event):
        if event.shift:
            # expand/collapse all subcollections
            expand = None
            
            # check whether to expand or collapse
            if self.name in expanded:
                expanded.remove(self.name)
                expand = False
            else:
                expanded.append(self.name)
                expand = True
            
            # do expanding/collapsing
            def loop(laycol):
                for item in laycol.children:
                    if expand:
                        if not item.name in expanded:
                            expanded.append(item.name)
                    else:
                        if item.name in expanded:
                            expanded.remove(item.name)
                        
                    if len(item.children) > 0:
                        loop(item)
            
            loop(layer_collections[self.name]["ptr"])
            
        else:
            # expand/collapse collection
            if self.expand:
                expanded.append(self.name)
            else:
                expanded.remove(self.name)
        
        
        # set selected row to the collection you're expanding/collapsing and update tree view
        context.scene.CMListIndex = self.index
        update_property_group(context)
        
        return {'FINISHED'}


class CMSetCollectionOperator(bpy.types.Operator):
    '''Click moves object to collection.  Shift-Click adds/removes from collection'''
    bl_label = "Set Collection"
    bl_idname = "view3d.set_collection"
    
    collection_index: IntProperty()
    collection_name: StringProperty()
    
    def invoke(self, context, event):
        collection = layer_collections[self.collection_name]["ptr"].collection
        
        if event.shift:
            # add object to collection
            
            # check if in collection
            in_collection = True
            
            for obj in context.selected_objects:
                if obj.name not in collection.objects:
                    in_collection = False
            
            if not in_collection:
                # add to collection
                bpy.ops.object.link_to_collection(collection_index=self.collection_index)
                
            else:
                # check and disallow removing from all collections
                for obj in context.selected_objects:
                    if len(obj.users_collection) == 1:
                        send_report("Error removing 1 or more objects from this collection.\nObjects would be left without a collection")
                        
                        return {'FINISHED'}
                
                # remove from collection
                bpy.ops.collection.objects_remove(collection=collection.name)
        
        else:
            # move object to collection
            bpy.ops.object.move_to_collection(collection_index=self.collection_index)
        
        return {'FINISHED'}


exclude_history = []
class CMExcludeOperator(bpy.types.Operator):
    '''Exclude collection. Shift-Click to isolate/restore collection'''
    bl_label = "Exclude Collection"
    bl_idname = "view3d.exclude_collection"
    
    name: StringProperty()
    
    def invoke(self, context, event):
        global exclude_history
        
        laycol_ptr = layer_collections[self.name]["ptr"]
        
        if event.shift:
            # isolate/de-isolate exclusion of collections
            
            # get active layer collections
            active_layer_collections = [x for x in layer_collections.values() \
                                          if x["ptr"].exclude == False]
            
            # check if collection isolated
            if len(active_layer_collections) == 1 and active_layer_collections[0]["name"] == self.name:
                if len(exclude_history) > 1:
                    # restore previous state
                    for x, item in enumerate(layer_collections.values()):
                        item["ptr"].exclude = exclude_history[x]
                
                else:
                    # enable all collections
                    for item in layer_collections.values():
                        item["ptr"].exclude = False
            
            else:
                # isolate collection
                
                # reset exclude history
                exclude_history.clear()
                
                # save state
                keep_history = -1
                for item in layer_collections.values():
                    exclude_history.append(item["ptr"].exclude)
                    if item["ptr"].exclude == False:
                        keep_history += 1
                
                if not keep_history:
                    exclude_history.clear()
                
                
                # isolate collection
                for item in layer_collections.values():
                    if item["name"] != laycol_ptr.name:
                        item["ptr"].exclude = True
                
                laycol_ptr.exclude = False
                
                # exclude all children
                laycol_iter_list = [laycol_ptr.children]
                while len(laycol_iter_list) > 0:
                    new_laycol_iter_list = []
                    for laycol_iter in laycol_iter_list:
                        for layer_collection in laycol_iter:
                            layer_collection.exclude = True
                            if len(layer_collection.children) > 0:
                                new_laycol_iter_list.append(layer_collection.children)
                    
                    laycol_iter_list = new_laycol_iter_list
                            
        
        else:
            # toggle exclusion
            
            # reset exclude history
            exclude_history.clear()
            
            
            # get current child exclusion state
            child_exclusion = []
            
            laycol_iter_list = [laycol_ptr.children]
            while len(laycol_iter_list) > 0:
                new_laycol_iter_list = []
                for laycol_iter in laycol_iter_list:
                    for layer_collection in laycol_iter:
                        child_exclusion.append([layer_collection, layer_collection.exclude])
                        if len(layer_collection.children) > 0:
                            new_laycol_iter_list.append(layer_collection.children)
                
                laycol_iter_list = new_laycol_iter_list
            
            
            # toggle exclusion of collection
            laycol_ptr.exclude = not laycol_ptr.exclude
            
            
            # set correct state for all children
            for laycol in child_exclusion:
                laycol[0].exclude = laycol[1]
            
        
        # reset exclude all history
        excludeall_history.clear()
        
        return {'FINISHED'}

excludeall_history = []
class CMUnExcludeAllOperator(bpy.types.Operator):
    '''Toggle excluded status of all collections'''
    bl_label = "Toggle Exclude Collections"
    bl_idname = "view3d.un_exclude_all_collections"
    
    def execute(self, context):
        global excludeall_history
        
        if len(excludeall_history) == 0 or len([l["ptr"].exclude for l in layer_collections.values() if l["ptr"].exclude == True]):
            excludeall_history.clear()
            keep_history = 0
            
            for item in reversed(list(layer_collections.values())):
                if item["ptr"].exclude:
                    keep_history += 1
                
                excludeall_history.append(item["ptr"].exclude)
                item["ptr"].exclude = False
            
            if not keep_history:
                excludeall_history.clear()
            
            excludeall_history.reverse()
        
        else:
            for x, item in enumerate(layer_collections.values()):
                item["ptr"].exclude = excludeall_history[x]
            
            excludeall_history.clear()
        
        return {'FINISHED'}


restrictselect_history = []
class CMRestrictSelectOperator(bpy.types.Operator):
    '''Change selectability. Shift-Click to isolate/restore selectability'''
    bl_label = "Change Collection Selectability"
    bl_idname = "view3d.restrict_select_collection"
    
    name: StringProperty()
    
    def invoke(self, context, event):
        global restrictselect_history
        
        laycol_ptr = layer_collections[self.name]["ptr"]
        
        if event.shift:
            # isolate/de-isolate selectability of collections
            active_layer_collections = [x for x in layer_collections.values() \
                                          if x["ptr"].collection.hide_select == False]
            
            # check if selectable isolated
            if len(active_layer_collections) == 1 and active_layer_collections[0]["name"] == self.name:
                if len(restrictselect_history) > 1:
                    # restore previous state
                    for item in restrictselect_history:
                        item["ptr"].collection.hide_select = False
                
                else:
                    # make all collections selectable
                    for item in layer_collections.values():
                        item["ptr"].collection.hide_select = False
            
            else:
                # save state
                restrictselect_history = active_layer_collections
                
                # isolate selectable collection
                for item in layer_collections.values():
                    if item["name"] != laycol_ptr.name:
                        item["ptr"].collection.hide_select = True
                
                laycol_ptr.collection.hide_select = False
                            
        
        else:
            # reset selectable history
            restrictselect_history.clear()
            
            # toggle selectability of collection
            laycol_ptr.collection.hide_select = not laycol_ptr.collection.hide_select
        
        
        # reset selectable all history
        restrictselectall_history.clear()
        
        return {'FINISHED'}


restrictselectall_history = []
class CMUnRestrictSelectAllOperator(bpy.types.Operator):
    '''Toggle selectable status of all collections'''
    bl_label = "Toggle Selectable Collections"
    bl_idname = "view3d.un_restrict_select_all_collections"
    
    def execute(self, context):
        global restrictselectall_history
        
        if len(restrictselectall_history) == 0 or len([l["ptr"].collection.hide_select for l in layer_collections.values() if l["ptr"].collection.hide_select == True]):
            restrictselectall_history.clear()
            keep_history = 0
            
            for item in layer_collections.values():
                if item["ptr"].collection.hide_select:
                    keep_history += 1
                    
                restrictselectall_history.append(item["ptr"].collection.hide_select)
                item["ptr"].collection.hide_select = False
            
            if not keep_history:
                restrictselectall_history.clear()
        
        else:
            for x, item in enumerate(layer_collections.values()):
                item["ptr"].collection.hide_select = restrictselectall_history[x]
            
            restrictselectall_history.clear()
        
        return {'FINISHED'}


hide_history = []
class CMHideOperator(bpy.types.Operator):
    '''Hide collection. Shift-Click to isolate/restore collection chain'''
    bl_label = "Hide Collection"
    bl_idname = "view3d.hide_collection"
    
    name: StringProperty()
    
    def invoke(self, context, event):
        global hide_history
        
        laycol_ptr = layer_collections[self.name]["ptr"]
        
        if event.shift:
            # isolate/de-isolate view of collections
            active_layer_collections = [x for x in layer_collections.values() \
                                          if x["ptr"].hide_viewport == False]
            
            layerchain = []
            laycol = layer_collections[self.name]
            
            # get chain of parents up to top level collection
            while laycol["id"] != 0:
                    layerchain.append(laycol)
                    laycol = laycol["parent"]
                    
            # check if reversed layerchain matches active collections
            if layerchain[::-1] == active_layer_collections:
                if len(hide_history) > 1:
                    # restore previous state
                    for item in hide_history:
                        item["ptr"].hide_viewport = False
                
                else:
                    # show all collections
                    for laycol in layer_collections.values():
                        laycol["ptr"].hide_viewport = False
                    
            else:
                 # save state
                hide_history = active_layer_collections
                
                # hide all collections
                for laycol in layer_collections.values():
                    laycol["ptr"].hide_viewport = True
                
                # show active collection plus parents
                laycol_ptr.hide_viewport = False
                
                laycol = layer_collections[self.name]
                while laycol["id"] != 0:
                    laycol["ptr"].hide_viewport = False
                    laycol = laycol["parent"]
        
        else:
            # reset hide history
            hide_history.clear()
            
            # toggle view of collection
            laycol_ptr.hide_viewport = not laycol_ptr.hide_viewport
        
        
        # reset hide all history
        hideall_history.clear()
        
        return {'FINISHED'}


hideall_history = []
class CMUnHideAllOperator(bpy.types.Operator):
    '''Toggle hidden status of all collections'''
    bl_label = "Toggle Hidden Collections"
    bl_idname = "view3d.un_hide_all_collections"
    
    def execute(self, context):
        global hideall_history
        
        if len(hideall_history) == 0 or len([l["ptr"].hide_viewport for l in layer_collections.values() if l["ptr"].hide_viewport == True]):
            hideall_history.clear()
            keep_history = 0
            
            for item in layer_collections.values():
                if item["ptr"].hide_viewport:
                    keep_history += 1
                    
                hideall_history.append(item["ptr"].hide_viewport)
                item["ptr"].hide_viewport = False
            
            if not keep_history:
                hideall_history.clear()
        
        else:
            for x, item in enumerate(layer_collections.values()):
                item["ptr"].hide_viewport = hideall_history[x]
            
            hideall_history.clear()
        
        return {'FINISHED'}


disableview_history = []
class CMDisableViewportOperator(bpy.types.Operator):
    '''Disable collection in viewport. Shift-Click to isolate/restore collection chain'''
    bl_label = "Disable Collection in Viewport"
    bl_idname = "view3d.disable_viewport_collection"
    
    name: StringProperty()
    
    def invoke(self, context, event):
        global disableview_history
        
        laycol_ptr = layer_collections[self.name]["ptr"]
        
        if event.shift:
            # isolate/de-isolate disablement of collections in viewport
            active_layer_collections = [x for x in layer_collections.values() \
                                          if x["ptr"].collection.hide_viewport == False]
            
            layerchain = []
            laycol = layer_collections[self.name]
            
            # get chain of parents up to top level collection
            while laycol["id"] != 0:
                    layerchain.append(laycol)
                    laycol = laycol["parent"]
                    
            # check if reversed layerchain matches active collections
            if layerchain[::-1] == active_layer_collections:
                if len(disableview_history) > 1:
                    # restore previous state
                    for item in disableview_history:
                        item["ptr"].collection.hide_viewport = False
                
                else:
                    # enable all collections in viewport
                    for laycol in layer_collections.values():
                        laycol["ptr"].collection.hide_viewport = False
                    
            else:
                 # save state
                disableview_history = active_layer_collections
                
                # disable all collections in viewport
                for laycol in layer_collections.values():
                    laycol["ptr"].collection.hide_viewport = True
                
                # enable active collection plus parents in viewport
                laycol_ptr.collection.hide_viewport = False
                
                laycol = layer_collections[self.name]
                while laycol["id"] != 0:
                    laycol["ptr"].collection.hide_viewport = False
                    laycol = laycol["parent"]
        
        else:
            # reset viewport history
            disableview_history.clear()
            
            # toggle disable of collection in viewport
            laycol_ptr.collection.hide_viewport = not laycol_ptr.collection.hide_viewport
        
        
        # reset viewport all history
        disableviewall_history.clear()
        
        return {'FINISHED'}


disableviewall_history = []
class CMUnDisableViewportAllOperator(bpy.types.Operator):
    '''Toggle viewport status of all collections'''
    bl_label = "Toggle Viewport Display of Collections"
    bl_idname = "view3d.un_disable_viewport_all_collections"
    
    def execute(self, context):
        global disableviewall_history
        
        if len(disableviewall_history) == 0 or len([l["ptr"].collection.hide_viewport for l in layer_collections.values() if l["ptr"].collection.hide_viewport == True]):
            disableviewall_history.clear()
            keep_history = 0
            
            for item in layer_collections.values():
                if item["ptr"].collection.hide_viewport:
                    keep_history += 1
                    
                disableviewall_history.append(item["ptr"].collection.hide_viewport)
                item["ptr"].collection.hide_viewport = False
            
            if not keep_history:
                disableviewall_history.clear()
        
        else:
            for x, item in enumerate(layer_collections.values()):
                item["ptr"].collection.hide_viewport = disableviewall_history[x]
            
            disableviewall_history.clear()
        
        return {'FINISHED'}


disablerender_history = []
class CMDisableRenderOperator(bpy.types.Operator):
    '''Disable collection in renders. Shift-Click to isolate/restore collection chain'''
    bl_label = "Disable Collection in Render"
    bl_idname = "view3d.disable_render_collection"
    
    name: StringProperty()
    
    def invoke(self, context, event):
        global disablerender_history
        
        laycol_ptr = layer_collections[self.name]["ptr"]
        
        if event.shift:
            # isolate/de-isolate render of collections
            active_layer_collections = [x for x in layer_collections.values() \
                                          if x["ptr"].collection.hide_render == False]
            
            layerchain = []
            laycol = layer_collections[self.name]
            
            # get chain of parents up to top level collection
            while laycol["id"] != 0:
                    layerchain.append(laycol)
                    laycol = laycol["parent"]
                    
            # check if reversed layerchain matches active collections
            if layerchain[::-1] == active_layer_collections:
                if len(disablerender_history) > 1:
                    # restore previous state
                    for item in disablerender_history:
                        item["ptr"].collection.hide_render = False
                
                else:
                    # allow render of all collections
                    for laycol in layer_collections.values():
                        laycol["ptr"].collection.hide_render = False
                    
            else:
                 # save state
                disablerender_history = active_layer_collections
                
                # disallow render of all collections
                for laycol in layer_collections.values():
                    laycol["ptr"].collection.hide_render = True
                
                # allow render of active collection plus parents
                laycol_ptr.collection.hide_render = False
                
                laycol = layer_collections[self.name]
                while laycol["id"] != 0:
                    laycol["ptr"].collection.hide_render = False
                    laycol = laycol["parent"]
        
        else:
            # reset render history
            disablerender_history.clear()
            
            # toggle renderability of collection
            laycol_ptr.collection.hide_render = not laycol_ptr.collection.hide_render
        
        
        # reset render all history
        disablerenderall_history.clear()
        
        return {'FINISHED'}


disablerenderall_history = []
class CMUnDisableRenderAllOperator(bpy.types.Operator):
    '''Toggle render status of all collections'''
    bl_label = "Toggle Render Display of Collections"
    bl_idname = "view3d.un_disable_render_all_collections"
    
    def execute(self, context):
        global disablerenderall_history
        
        if len(disablerenderall_history) == 0 or len([l["ptr"].collection.hide_render for l in layer_collections.values() if l["ptr"].collection.hide_render == True]):
            disablerenderall_history.clear()
            keep_history = 0
            
            for item in layer_collections.values():
                if item["ptr"].collection.hide_render:
                    keep_history += 1
                    
                disablerenderall_history.append(item["ptr"].collection.hide_render)
                item["ptr"].collection.hide_render = False
            
            if not keep_history:
                disablerenderall_history.clear()
        
        else:
            for x, item in enumerate(layer_collections.values()):
                item["ptr"].collection.hide_render = disablerenderall_history[x]
            
            disablerenderall_history.clear()
        
        return {'FINISHED'}


class CMRemoveCollectionOperator(bpy.types.Operator):
    '''Remove Collection'''
    bl_label = "Remove Collection"
    bl_idname = "view3d.remove_collection"
    
    collection_name: StringProperty()
    
    def execute(self, context):
        laycol = layer_collections[self.collection_name]
        collection = laycol["ptr"].collection
        laycol_parent = laycol["parent"]
        
        # save state and remove all hiding properties of parent collection
        orig_parent_hide_select = False
        orig_parent_exclude = False
        orig_parent_hide_viewport = False
        
        if laycol_parent["ptr"].collection.hide_select:
            orig_parent_hide_select = True
        
        if laycol_parent["ptr"].exclude:
            orig_parent_exclude = True
        
        if laycol_parent["ptr"].hide_viewport:
            orig_parent_hide_viewport = True
        
        laycol_parent["ptr"].collection.hide_select = False
        laycol_parent["ptr"].exclude = False
        laycol_parent["ptr"].hide_viewport = False
        
        
        # remove all hiding properties of this collection
        collection.hide_select = False
        laycol["ptr"].exclude = False
        laycol["ptr"].hide_viewport = False
        
        
        # shift all objects in this collection to the parent collection
        if collection.objects:
            orig_selected_objs = context.selected_objects
            orig_active_obj = context.active_object
        
            # select all objects in collection
            bpy.ops.object.select_same_collection(collection=collection.name)
            context.view_layer.objects.active = context.selected_objects[0]
            
            # remove any objects already in parent collection from selection
            for obj in context.selected_objects:
                if obj in laycol["parent"]["ptr"].collection.objects.values():
                    obj.select_set(False)
            
            # link selected objects to parent collection
            bpy.ops.object.link_to_collection(collection_index=laycol_parent["id"])
            
            # remove objects from collection
            bpy.ops.collection.objects_remove(collection=collection.name)
            
            # reset selection original values
            bpy.ops.object.select_all(action='DESELECT')
            
            for obj in orig_selected_objs:
                obj.select_set(True)
            context.view_layer.objects.active = orig_active_obj
        
        
        # shift all child collections to the parent collection
        if collection.children:
            for subcollection in collection.children:
                laycol_parent["ptr"].collection.children.link(subcollection)
        
        # reset hiding properties of parent collection
        laycol_parent["ptr"].collection.hide_select = orig_parent_hide_select
        laycol_parent["ptr"].exclude = orig_parent_exclude
        laycol_parent["ptr"].hide_viewport = orig_parent_hide_viewport
        
        
        # remove collection and update tree view
        bpy.data.collections.remove(collection)
        
        
        update_property_group(context)
        
        if len(context.scene.CMListCollection) == context.scene.CMListIndex:
            context.scene.CMListIndex = len(context.scene.CMListCollection) - 1
            update_property_group(context)
        
        
        # reset history
        exclude_history.clear()
        restrictselect_history.clear()
        hide_history.clear()
        disableview_history.clear()
        disablerender_history.clear()
        excludeall_history.clear()
        restrictselectall_history.clear()
        hideall_history.clear()
        disableviewall_history.clear()
        disablerenderall_history.clear()
        
        return {'FINISHED'}

rename = [False]
class CMNewCollectionOperator(bpy.types.Operator):
    '''Add New Collection'''
    bl_label = "Add New Collection"
    bl_idname = "view3d.add_collection"
    
    child: BoolProperty()
    
    def execute(self, context):
        new_collection = bpy.data.collections.new('Collection')
        scn = context.scene
        
        # if there are collections
        if len(scn.CMListCollection) > 0:
            # get selected collection
            laycol = layer_collections[scn.CMListCollection[scn.CMListIndex].name]
            
            # add new collection
            if self.child:
                laycol["ptr"].collection.children.link(new_collection)
                expanded.append(laycol["name"])
                
                # update tree view property
                update_property_group(context)
                
                scn.CMListIndex = layer_collections[new_collection.name]["row_index"]
                
            else:
                laycol["parent"]["ptr"].collection.children.link(new_collection)
                
                # update tree view property
                update_property_group(context)
                
                scn.CMListIndex = layer_collections[new_collection.name]["row_index"]
                
        # if no collections add top level collection and select it
        else:
            scn.collection.children.link(new_collection)
            
            # update tree view property
            update_property_group(context)
            
            scn.CMListIndex = 0
        
        global rename
        rename[0] = True
        
        # reset history
        exclude_history.clear()
        restrictselect_history.clear()
        hide_history.clear()
        disableview_history.clear()
        disablerender_history.clear()
        excludeall_history.clear()
        restrictselectall_history.clear()
        hideall_history.clear()
        disableviewall_history.clear()
        disablerenderall_history.clear()
        
        return {'FINISHED'}
