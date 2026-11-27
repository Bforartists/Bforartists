"""Native staged dialogs for toolbar presentation and tool-specific options."""
import copy
import json
import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty, IntProperty, BoolProperty, CollectionProperty
from . import timeline_config as model
from .timeline_catalog import ACTIONS, FAMILY, GROUPS

_editors={}
_tool_editors={}
_layout_editors={}
_layout_items={}

_MODES=(('HIDDEN','Hidden','Take this tool off the row; it stays in Find',0),
        ('BUTTON','Button','Invoke the existing action directly',1),
        ('POPOUT','Popout slider','Press and drag to reveal a temporary slider',2),
        ('INLINE','Inline slider','Keep the slider visible in the row',3))
_LABELS=(('LABEL','Label','Show the tool name'),('ICON','Icon','Show the tool\'s icon; hover for its name. Key types, nudges, Copy and Paste have icons'))


def _modes(self,context): return _MODES if self.action in model.SLIDERS else _MODES[:2]


# The row being edited (owner request 2026-10-18). Every row lists every tool,
# grouped by family; a stage starts from its home families' tools.
_FAMILY_LABELS={key:label for key,label,_a in GROUPS}
_ROWS=tuple((key,label,('The All row' if key=='ALL' else
             f'The {label} row; it starts with '+' and '.join(_FAMILY_LABELS[f] for f in families)+' tools'),
             model.STAGE_NUMBERS[key]) for key,label,families in model.STAGES)
_populating=False  # populate() sets values; their update callbacks must not write
# Family sections opened or closed while editing, per row, kept for this session.
_expanded={}


def _home(stage):
    return set(model.stage_families(stage)) if stage in model.STAGE_KEYS else set()


def _section_changed(self,context):
    if _populating: return
    current=editor(context)
    if current is not None: _expanded[(getattr(current,'_stage','ALL'),self.name)]=self.expanded


def _redraw_timelines(context):
    for window in getattr(context.window_manager,'windows',()):
        for area in window.screen.areas:
            if area.type=='DOPESHEET_EDITOR': area.tag_redraw()


def live_write(context,current=None):
    """Apply the dialog's rows to the Timeline now (owner request: changes show while you edit)."""
    current=current or editor(context)
    if current is None or _populating: return
    try:
        data=current.serialize(); write(context,data)
        current._record=copy.deepcopy(data); current._error=''
    except ValueError as exc:
        current._error=str(exc)
    _redraw_timelines(context)


def _entry_changed(self,context):
    live_write(context)


def _row_update(self,context):
    if _populating: return
    current=editor(context)
    workspace=getattr(context,'workspace',None)
    from .timeline_overlay import STAGE_PROPERTY
    if workspace is not None and hasattr(workspace,STAGE_PROPERTY):
        setattr(workspace,STAGE_PROPERTY,self.row)  # the Timeline row follows; on_stage_changed repopulates
    elif current is not None:
        current.switch_stage(self.row)


def record(context):
    from ..prefs import get_prefs,timeline_record
    return timeline_record(get_prefs(context))


def write(context,data):
    from ..prefs import get_prefs
    from ..operators.timeline_slider_ops import busy
    if busy(): raise ValueError('Finish or cancel the active slider first')
    prefs=get_prefs(context)
    if prefs is None: raise ValueError('Enable Anim Assist in preferences')
    prefs.timeline_layouts_json=model.encode(data,ACTIONS)


def editor(context): return _editors.get(context.window.as_pointer())


def staged_record(context):
    active=editor(context)
    return active.serialize() if active else record(context)


def sync_editor(context,data):
    """An edit made while Toolbar Settings is open applies at once and refreshes its rows."""
    active=editor(context)
    if active:
        write(context,data); active.populate(data); _redraw_timelines(context)


def _choices(self,context):
    data=getattr(self,'_record',None)
    if data is None: data=record(context)
    names=tuple((x['id'],x['name']) for x in data['saved'])
    if names not in _layout_items:
        _layout_items[names]=[('recommended','Recommended','Built-in two-slider layout',0)]+[
            (ident,name,'Load or manage '+name,index+1) for index,(ident,name) in enumerate(names)]
    return _layout_items[names]


class AA_ToolbarEntry(bpy.types.PropertyGroup):
    action: StringProperty(options={'HIDDEN'})
    family: StringProperty(options={'HIDDEN'})
    mode: EnumProperty(name='Display',description='How this tool appears in the Timeline row',items=_modes,default=1,update=_entry_changed)
    label_mode: EnumProperty(name='Label',description='Choose a name or compact tool glyph',items=_LABELS,default='LABEL',update=_entry_changed)
    width: FloatProperty(name='Slider Width',description='Track width in logical pixels',default=120,min=80,max=240,update=_entry_changed)


class AA_ToolbarSection(bpy.types.PropertyGroup):
    # name holds the family key.
    label: StringProperty(options={'HIDDEN'})
    expanded: BoolProperty(name='Show Tools',description='Show or hide this family\'s tools',default=False,
        update=_section_changed)


def _draw_entry(layout,entry):
    row=layout.row(align=True)
    split=row.split(factor=.4,align=True)
    split.label(text=entry.name)
    right=split.row(align=True)
    right.prop(entry,'mode',text='')
    cell=right.row(align=True)
    if model.has_icon(entry.action): cell.prop(entry,'label_mode',text='')
    elif entry.action in model.SLIDERS and entry.mode=='INLINE': cell.prop(entry,'width',text='Width')
    else: cell.label(text='')
    for direction,icon in ((-1,'TRIA_UP'),(1,'TRIA_DOWN')):
        op=right.operator('animassist.toolbar_reorder',text='',icon=icon); op.action=entry.action; op.direction=direction
    op=right.operator('animassist.tool_settings',text='',icon='PREFERENCES'); op.action=entry.action


def _draw_sections(self,layout,stage):
    """Family sections; a function so drawing works on stand-ins in checks."""
    layout.prop(self,'find',text='',icon='VIEWZOOM')
    text=getattr(self,'find','').strip().lower()
    home=_home(stage)
    column=layout.column(align=True)
    for section in getattr(self,'sections',()):
        tools=[e for e in getattr(self,'entries',()) if e.family==section.name]
        matches=[e for e in tools if not text or text in e.name.lower()]
        if not matches: continue
        shown=sum(e.mode!='HIDDEN' for e in tools)
        note=f'{shown} of {len(tools)} on the row'
        if section.name in home: note+=f' · a {model.stage_label(stage)} family'
        box=column.box()
        opened=section.expanded or bool(text)
        head=box.row(); head.alignment='LEFT'
        head.prop(section,'expanded',text=f'{section.label}    {note}',
                 icon='DOWNARROW_HLT' if opened else 'RIGHTARROW',emboss=False)
        if opened:
            for entry in matches: _draw_entry(box,entry)


class ANIMASSIST_OT_toolbar_settings(bpy.types.Operator):
    bl_idname='animassist.toolbar_settings'
    bl_label='Toolbar Settings'
    bl_description='Choose visible tools, inline or popout sliders, labels and order'
    row: EnumProperty(name='Row',description='Choose the Timeline row to configure; the Timeline shows it while you edit',
        items=_ROWS,update=_row_update)
    entries: CollectionProperty(type=AA_ToolbarEntry)
    sections: CollectionProperty(type=AA_ToolbarSection)
    find: StringProperty(name='Find Tool',description='Show only tools whose name contains this text',
        options={'TEXTEDIT_UPDATE','SKIP_SAVE'})
    active_index: IntProperty(default=0)
    layout_choice: EnumProperty(name='Saved Layout',description='Choose a saved layout to load or manage',items=_choices,default=0)

    def populate(self,data,stage=None):
        # Entries show one row's setup for every tool, grouped by family.
        global _populating
        _populating=True
        try:
            self._stage=stage or getattr(self,'_stage','ALL')
            self._record=copy.deepcopy(data)
            self.entries.clear()
            for row in model.stage_entries(data,self._stage,ACTIONS):
                entry=self.entries.add(); entry.name=ACTIONS[row['action']][2]; entry.action=row['action']
                entry.family=row['family']
                entry.mode=row['mode']; entry.label_mode=row['label_mode']; entry.width=row['width']
            self.sections.clear()
            home=_home(self._stage)
            for family in model.FAMILY_ORDER:
                if family not in _FAMILY_LABELS: continue
                section=self.sections.add(); section.name=family; section.label=_FAMILY_LABELS[family]
                # A stage opens on its home families; All opens closed.
                section.expanded=_expanded.get((self._stage,family),family in home)
            self.row=self._stage
            if not 0<=self.active_index<len(self.entries): self.active_index=0
            self.layout_choice=data['active_saved_id'] or 'recommended'
        finally:
            _populating=False

    def serialize(self):
        data=copy.deepcopy(self._record)
        model.apply_entries(data,getattr(self,'_stage','ALL'),
            [dict(action=e.action,family=e.family,mode=e.mode,label_mode=e.label_mode,width=e.width)
             for e in self.entries],ACTIONS)
        return model.validate(data,ACTIONS)

    def switch_stage(self,stage):
        # Keep this stage's unsaved edits in the staged record, then show the next.
        if stage!=getattr(self,'_stage','ALL'): self.populate(self.serialize(),stage)

    def invoke(self,context,event):
        from ..operators.timeline_slider_ops import busy
        if busy():
            self.report({'WARNING'},'Finish or cancel the active slider first'); return {'CANCELLED'}
        from .timeline_overlay import current_stage
        try: self.populate(record(context),current_stage(context))
        except ValueError as exc:
            if editor(context) is self: _editors.pop(context.window.as_pointer(),None)
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}
        self._original=copy.deepcopy(self._record); self._error=''
        _editors[context.window.as_pointer()]=self
        # A plain popup: changes apply live, so there is nothing to confirm or cancel.
        # It stays open while the pointer moves; a click outside or Esc closes it.
        # Bforartists checks the popup's originating region for 2D gizmos
        # before sending it mouse clicks. Use the header, which has no gizmos.
        header = next((region for region in getattr(context.area, 'regions', ())
                       if region.type == 'HEADER'), None)
        with context.temp_override(region=header):
            return context.window_manager.invoke_popup(self,width=640)

    def draw(self,context):
        layout=self.layout
        layout.label(text='Toolbar Settings',icon='PREFERENCES')
        layout.label(text='Layout: '+self._record['active']['name']+(' *' if model.modified(self.serialize(),ACTIONS) else ''))
        layout.prop(self,'layout_choice')
        row=layout.row(align=True)
        for operation,label in (('SAVE','Save As'),('LOAD','Load'),('UPDATE','Update Saved')):
            cell=row.row(align=True)
            cell.enabled=operation!='UPDATE' or self._record['active_saved_id'] not in {None,'recommended'}
            op=cell.operator('animassist.layout_action',text=label); op.operation=operation; op.target=self.layout_choice
        row=layout.row(align=True); row.enabled=self.layout_choice!='recommended'
        for operation,label in (('RENAME','Rename'),('DELETE','Delete')):
            op=row.operator('animassist.layout_action',text=label); op.operation=operation; op.target=self.layout_choice
        layout.separator()
        layout.prop(self,'row')
        stage=getattr(self,'_stage','ALL')
        layout.label(text='Any tool can go on any row. Tools are grouped by family; open one to add or remove its tools.')
        layout.label(text='Changes apply to the row right away.',icon='INFO')
        if getattr(self,'_error',''): layout.label(text=self._error,icon='ERROR')
        _draw_sections(self,layout,stage)
        if getattr(self,'_stage','ALL') in model.STAGE_KEYS:
            layout.operator('animassist.reset_stage_toolbar',text='Reset '+model.stage_label(self._stage)+' to Defaults')
        row=layout.row(align=True)
        row.operator('animassist.toolbar_revert',text='Revert Changes')
        row.operator('animassist.restore_toolbar',text='Restore Recommended Layout')
        layout.label(text='Hidden tools stay available in Find.')
        layout.label(text='Click outside or press Esc to close; your changes stay.')
        if not context.preferences.use_preferences_save:
            layout.label(text='Save Preferences to keep these changes after a restart.')
            layout.operator('wm.save_userpref',text='Save Preferences')

    def execute(self,context):
        try: write(context,self.serialize())
        except ValueError as exc:
            if editor(context) is self: _editors.pop(context.window.as_pointer(),None)
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}
        _editors.pop(context.window.as_pointer(),None)
        return {'FINISHED'}

    def cancel(self,context):
        # Changes were applied as they were made; closing keeps them (Revert Changes undoes).
        if editor(context) is self: _editors.pop(context.window.as_pointer(),None)


class ANIMASSIST_OT_toolbar_revert(bpy.types.Operator):
    bl_idname='animassist.toolbar_revert'
    bl_label='Revert Changes'
    bl_description='Put every row back as it was when Toolbar Settings opened'
    bl_options={'INTERNAL'}
    def execute(self,context):
        current=editor(context)
        if current is None or getattr(current,'_original',None) is None: return {'CANCELLED'}
        try:
            data=copy.deepcopy(current._original); write(context,data)
            current.populate(data,getattr(current,'_stage','ALL')); _redraw_timelines(context)
        except ValueError as exc:
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}


class ANIMASSIST_OT_toolbar_reorder(bpy.types.Operator):
    bl_idname='animassist.toolbar_reorder'
    bl_label='Move Toolbar Tool'
    bl_description='Move this tool earlier or later within its family on the row'
    bl_options={'INTERNAL'}
    action: StringProperty(options={'HIDDEN','SKIP_SAVE'})
    direction: IntProperty(options={'HIDDEN','SKIP_SAVE'})
    def execute(self,context):
        current=editor(context)
        if current is None: return {'CANCELLED'}
        index=next((i for i,e in enumerate(current.entries) if e.action==self.action),current.active_index)
        if 0<=index<len(current.entries):
            # Order is kept within a family (the row groups tools by family).
            family=current.entries[index].family
            indexes=[i for i,e in enumerate(current.entries) if e.family==family]
            target=indexes.index(index)+self.direction
            if 0<=target<len(indexes):
                current.entries.move(index,indexes[target]); current.active_index=indexes[target]
                live_write(context,current)
        return {'FINISHED'}


class ANIMASSIST_OT_restore_toolbar(bpy.types.Operator):
    bl_idname='animassist.restore_toolbar'
    bl_label='Restore Recommended Layout'
    bl_description='Restore the two-slider recommended layout; keep your saved layouts'
    def execute(self,context):
        data=staged_record(context); model.load(data,'recommended',ACTIONS)
        if editor(context): sync_editor(context,data)
        else: write(context,data)
        return {'FINISHED'}


class ANIMASSIST_OT_reset_stage_toolbar(bpy.types.Operator):
    bl_idname='animassist.reset_stage_toolbar'
    bl_label='Reset Stage to Defaults'
    bl_description='Restore this stage’s default tools, order and display modes; All and the other stages stay as they are'
    bl_options={'INTERNAL'}
    def execute(self,context):
        from .timeline_overlay import current_stage
        stage=current_stage(context)
        if stage not in model.STAGE_KEYS:
            self.report({'WARNING'},'Choose Block, Spline, Polish or Deliver first'); return {'CANCELLED'}
        try:
            data=staged_record(context); model.reset_stage(data,stage)
            if editor(context): sync_editor(context,data)
            else: write(context,data)
        except ValueError as exc:
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}


def on_stage_changed(workspace):
    """An open Toolbar Settings dialog follows its window's new row stage."""
    stage=getattr(workspace,'animassist_timeline_stage','ALL')
    manager=getattr(bpy.context,'window_manager',None)
    for window in getattr(manager,'windows',()):
        active=_editors.get(window.as_pointer())
        if active is not None and window.workspace==workspace:
            try: active.switch_stage(stage)
            except (ValueError,ReferenceError): _editors.pop(window.as_pointer(),None)


class ANIMASSIST_OT_tool_settings(bpy.types.Operator):
    bl_idname='animassist.tool_settings'
    bl_label='Animation Tool Settings'
    bl_description='Configure this tool’s display, slider range, defaults and drag behavior'
    action: StringProperty(options={'HIDDEN','SKIP_SAVE'})
    mode: EnumProperty(name='Display',description='How this tool appears in the row',items=_modes,default=1)
    label_mode: EnumProperty(name='Label',description='Choose name or compact glyph',items=_LABELS,default='LABEL')
    width: FloatProperty(name='Slider Width',description='Track width in logical pixels',default=120,min=80,max=240)
    range_min: FloatProperty(name='Minimum',description='Lower display and numeric adjustment bound')
    range_max: FloatProperty(name='Maximum',description='Upper display and numeric adjustment bound')
    default: FloatProperty(name='Default',description='Starting amount; changing it does not change animation')
    sensitivity: FloatProperty(name='Sensitivity',description='Pixels needed to traverse a popout slider range',default=200,min=10,max=2000)
    precision: IntProperty(name='Precision',description='Decimal places shown in slider readouts',default=1,min=0,max=4)
    snap_enabled: BoolProperty(name='Snap Amount',description='Round slider values to the configured step')
    snap_step: FloatProperty(name='Snap Step',description='Step in this tool’s displayed units',default=1,min=.0001)
    overshoot_enabled: BoolProperty(name='Custom Range / Overshoot',description='Use your configured range rather than the standard display range')
    ticks: BoolProperty(name='Presets as Ticks',description='Show presets as click ticks on the inline slider track instead of preset buttons',default=False)
    presets_text: StringProperty(name='Presets',description='Comma-separated amounts; at most 12, inside the configured range')

    def invoke(self,context,event):
        if self.action not in ACTIONS: return {'CANCELLED'}
        from ..operators.timeline_slider_ops import busy
        if busy():
            self.report({'WARNING'},'Finish or cancel the active slider first'); return {'CANCELLED'}
        from .timeline_overlay import current_stage
        staged=staged_record(context)
        self._tool=copy.deepcopy(staged['active']['tools'][self.action])
        # Display and label belong to the setup the row shows; numbers are shared.
        self._target=model.pin_target(current_stage(context),self.action)
        for field,value in self._tool.items():
            if field=='presets': self.presets_text=', '.join(f'{v:g}' for v in value)
            elif field!='action' and hasattr(self,field): setattr(self,field,value)
        if self._target in model.STAGE_KEYS:
            view=model.stage_view(staged['active'],self._target)[1][self.action]
            self.mode=view['mode']; self.label_mode=view['label_mode']
            if self.action in model.SLIDERS:
                self.ticks=bool(view.get('ticks',False)); self._shown_ticks=self.ticks
                self._shown_presets=[float(v) for v in view.get('presets',[])]
                self.presets_text=', '.join(f'{v:g}' for v in self._shown_presets)
        _tool_editors[context.window.as_pointer()]=self
        return context.window_manager.invoke_props_dialog(self,width=430)

    def draw(self,context):
        layout=self.layout
        layout.label(text=ACTIONS[self.action][2])
        target=getattr(self,'_target','ALL')
        if target in model.STAGE_KEYS:
            layout.label(text=f'Display, label and presets apply to the {model.stage_label(target)} stage; '
                              'other amounts are shared by every stage.')
        layout.prop(self,'mode')
        if model.has_icon(self.action): layout.prop(self,'label_mode')
        if self.action in model.SLIDERS:
            unit=model.SLIDERS[self.action][1]
            layout.prop(self,'width')
            layout.prop(self,'default',text=f'Default ({unit})')
            layout.prop(self,'overshoot_enabled')
            low,high=model.SLIDERS[self.action][3:5]
            layout.label(text=f'Standard range: {low:g} to {high:g}{unit}')
            row=layout.row(align=True); row.enabled=self.overshoot_enabled
            row.prop(self,'range_min',text=f'Min ({unit})'); row.prop(self,'range_max',text=f'Max ({unit})')
            layout.prop(self,'sensitivity'); layout.prop(self,'precision')
            layout.prop(self,'snap_enabled')
            row=layout.row(); row.enabled=self.snap_enabled; row.prop(self,'snap_step',text=f'Step ({unit})')
            layout.prop(self,'presets_text')
            layout.prop(self,'ticks')
        layout.separator()
        layout.label(text='Masks, targets and anchors are scene-specific.')
        op=layout.operator('wm.call_panel',text='Scene Tool Options')
        op.name='ANIMASSIST_PT_timeline_options_'+FAMILY[self.action][0]

    def execute(self,context):
        try:
            data=staged_record(context); tool=copy.deepcopy(self._tool)
            for field in tool:
                if field=='presets': tool[field]=[float(x.strip()) for x in self.presets_text.split(',') if x.strip()]
                elif field!='action' and hasattr(self,field): tool[field]=getattr(self,field)
            target=getattr(self,'_target','ALL')
            stage_presets=None
            if target in model.STAGE_KEYS:
                tool['mode'],tool['label_mode']=self._tool['mode'],self._tool['label_mode']
                if 'ticks' in self._tool: tool['ticks']=self._tool['ticks']  # All keeps its own; the stage gets self.ticks
                if self.action in model.SLIDERS:
                    # Store stage presets only when edited, so untouched stages keep following All.
                    if tool['presets']!=getattr(self,'_shown_presets',tool['presets']): stage_presets=tool['presets']
                    tool['presets']=list(self._tool['presets'])
            data['active']['tools'][self.action]=model.validate_tool(self.action,tool)
            if target in model.STAGE_KEYS:
                model.set_stage_tool(data,target,self.action,mode=self.mode,label_mode=self.label_mode,
                                     presets=stage_presets,
                                     # Store ticks only when changed, like presets.
                                     ticks=self.ticks if self.action in model.SLIDERS
                                     and self.ticks!=getattr(self,'_shown_ticks',self.ticks) else None)
                data=model.validate(data,ACTIONS)
            if editor(context): sync_editor(context,data)
            else: write(context,data)
            _tool_editors.pop(context.window.as_pointer(),None)
            return {'FINISHED'}
        except ValueError as exc:
            _tool_editors.pop(context.window.as_pointer(),None)
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}

    def cancel(self,context):
        if _tool_editors.get(context.window.as_pointer()) is self:
            _tool_editors.pop(context.window.as_pointer(),None)


class ANIMASSIST_OT_layout_action(bpy.types.Operator):
    bl_idname='animassist.layout_action'
    bl_label='Saved Toolbar Layout'
    bl_description='Save, load, rename or delete a named toolbar arrangement without changing animation'
    operation: StringProperty(options={'HIDDEN','SKIP_SAVE'})
    target: StringProperty(options={'HIDDEN','SKIP_SAVE'})
    layout_name: StringProperty(name='Layout Name',description='A unique user-entered name, at most 64 characters',maxlen=64)
    discard_changes: BoolProperty(name='Discard Unsaved Working Changes',description='Replace the current modified arrangement with the selected saved layout')

    def invoke(self,context,event):
        from ..operators.timeline_slider_ops import busy
        if busy():
            self.report({'WARNING'},'Finish or cancel the active slider first'); return {'CANCELLED'}
        data=staged_record(context)
        self._item=next((item for item in data['saved'] if item['id']==self.target),None)
        if self.operation=='RENAME' and self._item: self.layout_name=self._item['name']
        needs_dialog=self.operation in {'SAVE','RENAME','DELETE'} or (self.operation=='LOAD' and model.modified(data,ACTIONS))
        if needs_dialog:
            _layout_editors[context.window.as_pointer()]=self
            return context.window_manager.invoke_props_dialog(self,width=430)
        return self.execute(context)

    def draw(self,context):
        if self.operation in {'SAVE','RENAME'}:
            self.layout.label(text='Save your arrangement' if self.operation=='SAVE' else 'Rename saved layout')
            self.layout.prop(self,'layout_name')
        elif self.operation=='DELETE':
            self.layout.label(text='Delete '+(self._item['name'] if self._item else 'this layout')+'?')
            self.layout.label(text='The current working arrangement stays available.')
        elif self.operation=='LOAD':
            self.layout.label(text='The current arrangement has unsaved changes.')
            op=self.layout.operator('animassist.layout_action',text='Save As First'); op.operation='SAVE'
            self.layout.prop(self,'discard_changes')

    def execute(self,context):
        try:
            data=staged_record(context)
            if self.operation=='SAVE': model.save_as(data,self.layout_name)
            elif self.operation=='UPDATE': model.update_saved(data)
            elif self.operation=='RENAME': model.rename(data,self.target,self.layout_name)
            elif self.operation=='DELETE': model.delete(data,self.target)
            elif self.operation=='LOAD':
                if model.modified(data,ACTIONS) and not self.discard_changes:
                    raise ValueError('Save As first or explicitly discard the working changes')
                model.load(data,self.target,ACTIONS)
            else: raise ValueError('Choose a known layout operation')
            write(context,data); sync_editor(context,data)
            _layout_editors.pop(context.window.as_pointer(),None)
            return {'FINISHED'}
        except ValueError as exc:
            _layout_editors.pop(context.window.as_pointer(),None)
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}

    def cancel(self,context):
        if _layout_editors.get(context.window.as_pointer()) is self:
            _layout_editors.pop(context.window.as_pointer(),None)


CLASSES=(AA_ToolbarEntry,AA_ToolbarSection,ANIMASSIST_OT_toolbar_settings,
         ANIMASSIST_OT_toolbar_reorder,ANIMASSIST_OT_toolbar_revert,ANIMASSIST_OT_restore_toolbar,ANIMASSIST_OT_reset_stage_toolbar,
         ANIMASSIST_OT_tool_settings,
         ANIMASSIST_OT_layout_action)


def register():
    from ..core import explainers
    for cls in CLASSES: explainers.register_class(cls)
    bpy.app.handlers.load_pre.append(clear_dialogs)


@bpy.app.handlers.persistent
def clear_dialogs(_unused=None):
    _editors.clear(); _tool_editors.clear(); _layout_editors.clear()


def unregister():
    _editors.clear()
    _tool_editors.clear()
    _layout_editors.clear()
    _layout_items.clear()
    if clear_dialogs in bpy.app.handlers.load_pre: bpy.app.handlers.load_pre.remove(clear_dialogs)
    for cls in reversed(CLASSES):
        if cls.is_registered: bpy.utils.unregister_class(cls)
