"""Undoable direct-drag tools; preview state is never stored in preferences."""
import math
import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty
from ..core.timeline_slider_session import capture

_active={}
_last_values={}


def _model():
    from ..ui import timeline_config
    return timeline_config


def busy(): return bool(_active)


def feedback(window,area):
    op=_active.get(window.as_pointer())
    return op if op and op._area==area else None


def last_value(window,area,action,default):
    return _last_values.get((window.as_pointer(),area.as_pointer(),action),default)


@bpy.app.handlers.persistent
def cancel_active(_unused=None, *, finalize=False):
    for op in list(_active.values()):
        op.abort()
        # Unregister removes the native modal operator before its next timer
        # callback. Dispose that timer while the operator RNA is still alive.
        if finalize: op._cleanup()
    _last_values.clear()


class ANIMASSIST_OT_timeline_slider(bpy.types.Operator):
    bl_idname='animassist.timeline_slider'
    bl_label='Adjust Animation'
    bl_description='Drag to preview; release to commit; Esc or right-click restores the original animation'
    bl_options={'REGISTER','UNDO','BLOCKING'}
    action: StringProperty(options={'HIDDEN','SKIP_SAVE'})
    mode: StringProperty(default='POPOUT',options={'HIDDEN','SKIP_SAVE'})
    track_x: FloatProperty(options={'HIDDEN','SKIP_SAVE'})
    track_y: FloatProperty(options={'HIDDEN','SKIP_SAVE'})
    track_width: FloatProperty(default=120,options={'HIDDEN','SKIP_SAVE'})
    value: FloatProperty(name='Amount',description='Adjustment amount in the tool’s displayed units')
    apply_value: BoolProperty(default=False,options={'HIDDEN','SKIP_SAVE'})
    preset: BoolProperty(default=False,options={'HIDDEN','SKIP_SAVE'})
    _aborted=False

    @classmethod
    def poll(cls,context):
        from ..ui.timeline_strip import is_timeline
        if not is_timeline(context.area):
            cls.poll_message_set('Use this adjustment from a Timeline')
            return False
        return True

    def invoke(self,context,event):
        model=_model()
        from ..prefs import get_prefs,timeline_record
        from ..ui.timeline_strip import _unavailable
        if busy():
            self.report({'WARNING'},'Finish or cancel the active slider first')
            return {'CANCELLED'}
        try:
            if self.action not in model.SLIDERS: raise ValueError('Choose a supported numeric animation tool')
            reason=_unavailable(context,context.area,self.action)
            if reason: raise ValueError(reason)
            record=timeline_record(get_prefs(context))
            from ..ui.timeline_overlay import current_stage
            # The stage the row shows decides presets and ticks; amounts stay shared.
            shown=model.stage_view(record['active'],current_stage(context))[1][self.action]
            self._tool=model.effective_tool(self.action,shown)
            self._lo,self._hi=model.track_range(self._tool)
            self._area=context.area; self._window=context.window; self._manager=context.window_manager
            self._window_id=context.window.as_pointer(); self._area_id=context.area.as_pointer()
            self._scene=context.scene
            self._region=context.region
            self._area_size=(context.area.width,context.area.height)
            self._session=capture(context,self.action)
            self._start_x=event.mouse_x
            self._start=min(self._hi,max(self._lo,
                last_value(context.window,context.area,self.action,self._tool['default'])))
            self.value=self.value if self.apply_value else self._start
            self._moved=False; self._numeric=''; self._aborted=False
            if self.apply_value:
                self._preview(self.value)
                self._session.commit()
                self._remember()
                return {'FINISHED'}
            _active[context.window.as_pointer()]=self
            self._timer=context.window_manager.event_timer_add(.15,window=context.window)
            context.window_manager.modal_handler_add(self)
            if self.mode=='INLINE':
                self._moved=True
                self._inline_origin=self._track_value(event.mouse_region_x)
                self._preview(self._track_value(event.mouse_region_x))
            self._status(context)
            return {'RUNNING_MODAL'}
        except Exception as exc:
            if hasattr(self,'_session'): self.abort()
            self.report({'WARNING'},str(exc))
            return {'CANCELLED'}

    def _track_value(self,x):
        fraction=min(1.,max(0.,(x-self.track_x)/max(1.,self.track_width)))
        value=self._lo+fraction*(self._hi-self._lo)
        return _model().snap_to_tick(self._tool,value)

    def _preview(self,value):
        if not self._lo<=value<=self._hi:
            raise ValueError('Enter a value inside the configured slider range')
        self._session.preview(value)
        self.value=value
        self._area.tag_redraw()

    def _remember(self):
        _last_values[(self._window.as_pointer(),self._area.as_pointer(),self.action)]=self.value

    def _status(self,context):
        model=_model()
        label,unit,*_=model.SLIDERS[self.action]
        if getattr(self,'_sticky',False):
            context.workspace.status_text_set(f'{label}: {self.value:.{self._tool["precision"]}f}{unit} | Drag on the popout: adjust | Double-click or click away: apply | Esc: cancel | Type: value')
            return
        context.workspace.status_text_set(f'{label}: {self.value:.{self._tool["precision"]}f}{unit} | Release: apply | Esc: cancel | Shift: precise | Type: value')

    def _stick(self):
        """A click without dragging keeps the popout open (owner request 2026-10-18)."""
        from ..ui import timeline_overlay as overlay
        region=self._region
        with bpy.context.temp_override(window=self._window,area=self._area,region=region):
            band=overlay._items(bpy.context)[1]
            scale=bpy.context.preferences.system.ui_scale
        self._pop_box,self._pop_track=overlay.popout_geometry(region.width,region.height,band,self.track_x,scale,14*scale)
        self._sticky=True; self._moved=True; self._dragging=False
        self._area.tag_redraw()

    def _pop_value(self,x):
        tx,_ty,tw,_th=self._pop_track
        fraction=min(1.,max(0.,(x-tx)/max(1.,tw)))
        return _model().snap_to_tick(self._tool,self._lo+fraction*(self._hi-self._lo))

    def _sticky_event(self,event):
        """Pointer handling while a clicked popout stays open; None = not handled here."""
        x,y=event.mouse_region_x,event.mouse_region_y
        bx,by,bw,bh=self._pop_box
        inside=bx<=x<bx+bw and by<=y<by+bh
        if event.type=='LEFTMOUSE' and event.value=='DOUBLE_CLICK' and inside:
            return 'APPLY'
        if event.type=='LEFTMOUSE' and event.value in {'PRESS','DOUBLE_CLICK'}:
            if not inside:
                return 'APPLY'  # click away applies the adjustment
            self._dragging=True
            self._preview(self._pop_value(x))
            return 'KEEP'
        if event.type=='LEFTMOUSE' and event.value=='RELEASE':
            self._dragging=False
            return 'KEEP'
        if event.type=='MOUSEMOVE':
            if self._dragging and not self._numeric:
                self._preview(self._pop_value(x))
            return 'KEEP'
        return None

    def _cleanup(self):
        _active.pop(self._window_id,None)
        if getattr(self,'_timer',None):
            try: self._manager.event_timer_remove(self._timer)
            except (ReferenceError, RuntimeError): pass
            self._timer=None
        try:
            self._window.workspace.status_text_set(None)
            self._area.tag_redraw()
        except ReferenceError: pass

    def abort(self):
        self._aborted=True
        try: self._session.cancel()
        except (ReferenceError, RuntimeError): pass
        _active.pop(self._window_id,None)
        # Keep the timer until modal() returns CANCELLED and removes its handler.

    def modal(self,context,event):
        model=_model()
        from ..ui.timeline_strip import _module_reason
        try:
            if self._aborted or context.scene!=self._scene or not self._session.valid() or _module_reason(context,self.action) or not any(a==self._area for a in self._window.screen.areas) or (self._area.width,self._area.height)!=self._area_size:
                self.abort(); self._cleanup(); return {'CANCELLED'}
            if event.type in {'ESC','RIGHTMOUSE','WINDOW_DEACTIVATE'}:
                self.abort(); self._cleanup(); return {'CANCELLED'}
            if event.type in {'RET','NUMPAD_ENTER'} and event.value=='PRESS':
                if self._numeric: self._preview(float(self._numeric))
                self._session.commit(); self._remember(); self._cleanup(); return {'FINISHED'}
            if getattr(self,'_sticky',False):
                outcome=self._sticky_event(event)
                if outcome=='APPLY':
                    if self._numeric: self._preview(float(self._numeric))
                    self._session.commit(); self._remember(); self._cleanup(); return {'FINISHED'}
                if outcome=='KEEP':
                    self._status(context)
                    return {'RUNNING_MODAL'}
            if event.type=='LEFTMOUSE' and event.value=='RELEASE':
                if not self._moved:
                    if self.mode=='POPOUT':
                        self._stick(); self._status(context)
                        return {'RUNNING_MODAL'}
                    self.abort(); self._cleanup()
                    self.report({'INFO'},'Press and drag this tool to adjust it')
                    return {'CANCELLED'}
                self._session.commit(); self._remember(); self._cleanup(); return {'FINISHED'}
            if event.type=='BACK_SPACE' and event.value=='PRESS':
                self._numeric=self._numeric[:-1]
            elif event.value=='PRESS' and getattr(event,'unicode','') and event.unicode in '0123456789.-':
                self._numeric+=event.unicode
                try: self._preview(float(self._numeric))
                except ValueError: pass
            elif event.type=='MOUSEMOVE' and not self._numeric:
                delta=event.mouse_x-self._start_x
                if abs(delta)>=3 or self.mode=='INLINE':
                    self._moved=True
                    value=self._track_value(event.mouse_region_x) if self.mode=='INLINE' else model.value_from_pointer(
                        self._tool,self._start,delta,precise=event.shift,snap=event.ctrl)
                    if self.mode=='INLINE' and event.shift:
                        value=self._inline_origin+delta/max(1.,self.track_width)*(self._hi-self._lo)*.1
                    if self.mode=='INLINE' and (self._tool['snap_enabled'] or event.ctrl):
                        step=self._tool['snap_step']; value=round(value/step)*step
                    self._preview(min(self._hi,max(self._lo,value)))
            self._status(context)
            return {'RUNNING_MODAL'}
        except Exception as exc:
            self.abort(); self._cleanup(); self.report({'WARNING'},str(exc)); return {'CANCELLED'}

    def cancel(self,context):
        self.abort(); self._cleanup()

    def execute(self,context):
        from ..prefs import get_prefs,timeline_record
        try:
            if self.action not in _model().SLIDERS: raise ValueError('Choose a numeric animation tool')
            tool=_model().effective_tool(self.action,timeline_record(get_prefs(context))['active']['tools'][self.action])
            low,high=_model().preset_bounds(self.action) if getattr(self,'preset',False) else (tool['range_min'],tool['range_max'])
            if not low<=self.value<=high: raise ValueError('Use a value inside the configured slider range')
            session=capture(context,self.action)
            session.preview(self.value); session.commit()
            _last_values[(context.window.as_pointer(),context.area.as_pointer(),self.action)]=self.value
            context.area.tag_redraw()
            return {'FINISHED'}
        except Exception as exc:
            self.report({'WARNING'},str(exc)); return {'CANCELLED'}


class ANIMASSIST_OT_slider_value(bpy.types.Operator):
    bl_idname='animassist.slider_value'
    bl_label='Set Slider Amount'
    bl_description='Enter an exact adjustment amount; accept applies one undoable adjustment'
    bl_options={'REGISTER','UNDO'}
    action: StringProperty(options={'HIDDEN','SKIP_SAVE'})
    value: FloatProperty(name='Amount',description='Amount in this tool’s displayed units')
    def invoke(self,context,event): return context.window_manager.invoke_props_dialog(self,width=300)
    def draw(self,context):
        label,unit,*_=_model().SLIDERS[self.action]
        self.layout.label(text=label)
        self.layout.prop(self,'value',text=f'Amount ({unit})')
    def execute(self,context):
        return ANIMASSIST_OT_timeline_slider.execute(self,context)


CLASSES=(ANIMASSIST_OT_timeline_slider,ANIMASSIST_OT_slider_value)
