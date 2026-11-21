"""Absolute preview transactions using existing animation math."""
import math


class Transaction:
    def __init__(self, restore, apply, valid=lambda: True, *, refresh=lambda: None):
        self.restore, self.apply, self.valid = restore, apply, valid
        self.refresh = refresh
        self.closed = False
        self._previewed_value = None

    def preview(self, value):
        if self.closed or not self.valid(): raise ValueError('The original animation target is no longer available')
        if not math.isfinite(value): raise ValueError('Enter a finite slider value')
        if value == self._previewed_value:
            return
        self._previewed_value = None
        self.restore()
        try:
            self.apply(value)
            self.refresh()
        except Exception:
            self.restore()
            self.refresh()
            raise
        self._previewed_value = value

    def cancel(self):
        if not self.closed:
            self.restore()
            self.refresh()
            self.closed = True

    def commit(self):
        if self.closed or not self.valid(): raise ValueError('The original animation target is no longer available')
        self.closed = True


KEY_FIELDS=('handle_left_type','handle_right_type','interpolation','type','easing',
            'amplitude','back','period','select_control_point','select_left_handle','select_right_handle')


def snapshot(curves):
    return [(fc, [dict(co=tuple(k.co),left=tuple(k.handle_left),right=tuple(k.handle_right),
                    **{field:getattr(k,field) for field in KEY_FIELDS})
                 for k in fc.keyframe_points]) for fc in curves]


def restore_snapshot(saved):
    for fc, rows in saved:
        points=fc.keyframe_points
        if len(points)!=len(rows):
            # Key count changed (Reduce removes keys): rebuild the curve's keys in one
            # step rather than inserting one by one, which crashed on cancel.
            try: points.clear()
            except AttributeError:
                while len(points): points.remove(points[0],fast=True)
            points.add(len(rows))
        for k,row in zip(points,rows):
            for field in KEY_FIELDS: setattr(k,field,row[field])
            k.co=row['co']; k.handle_left=row['left']; k.handle_right=row['right']
        fc.update()


def _reduce(curves,tolerance):
    """Remove keys whose deletion keeps each curve within *tolerance* (same rule as Reduce Keys)."""
    from .p7_proxy_math import reduce_keys, KeySample
    for fc in curves:
        points=fc.keyframe_points
        if len(points)<=2: continue
        keep={s.frame for s in reduce_keys([KeySample(frame=k.co.x,value=k.co.y) for k in points],tolerance)}
        for index in reversed([i for i,k in enumerate(points) if k.co.x not in keep]):
            points.remove(points[index])
        fc.update()


def capture(context,action):
    from .fcurve_compat import get_fcurves
    from . import curve_tools as math_tools, p6_retime_math as retime, breakdown_core as breakdown
    from ..operators import curve_tool_ops as curves_ops
    from ..operators.p3_breakdown_ops import _resolve_target, _options_from_scene
    obj=context.active_object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        raise ValueError('Select an object with editable animation')
    data=obj.animation_data; native_action=data.action; scene=context.scene
    if obj.library and not obj.override_library or native_action.library and not native_action.override_library:
        raise ValueError('Use local or overridden animation data')
    frame=scene.frame_current_final
    base_frame=math.floor(frame)
    options=None; bones=None; curve_data=[]; pivot=frame; snap=False
    if action=='DRAG':
        obj,bones=_resolve_target(context)
        options=_options_from_scene(context,target_frame=frame)
        curves=breakdown.iter_target_fcurves(obj,bones,options.mask,options.exclusion)
    elif action in {'SCALE_DRAG','OFFSET_DRAG'}:
        curves=[fc for fc in get_fcurves(native_action,anim_data=data) if not fc.lock and not fc.hide]
        p6=scene.anim_assist_p6
        pivot=retime.resolve_pivot(p6.anchor_mode,retime.collect_key_frames(curves),frame,custom_frame=p6.pivot_frame)
        snap=p6.modal_snap
    elif action=='RIPPLE':
        # Keys after the playhead, as Ripple Forward moves them.
        curves=[fc for fc in get_fcurves(native_action,anim_data=data) if not fc.lock and not fc.hide
                and any(k.co.x>scene.frame_current for k in fc.keyframe_points)]
        snap=scene.anim_assist_p6.modal_snap
        after=[k.co.x for fc in curves for k in fc.keyframe_points if k.co.x>scene.frame_current]
        # Moving earlier stops one frame after the playhead so keys never land on or before it.
        earliest=-(min(after)-scene.frame_current-1.) if after else 0.
    elif action=='REDUCE':
        curves=[fc for fc in get_fcurves(native_action,anim_data=data) if not fc.lock and not fc.hide
                and len(fc.keyframe_points)>2]
    else:
        curves=[fc for fc in curves_ops._editable_fcurves(context) if not fc.lock and not fc.hide]
        ref_frame=scene.anim_assist.reference_frame or frame
        for fc in curves:
            keys=curves_ops._snapshot_keys(fc)
            selected=[i for i,k in enumerate(keys) if k.selected]
            if not selected or (action=='EASE' and len(selected)<2): continue
            curve_data.append((fc,keys,selected,fc.evaluate(ref_frame)))
        curves=[row[0] for row in curve_data]
    if not curves: raise ValueError('Select editable keys that match the tool mask')
    saved=snapshot(curves)

    def refresh():
        # Keep the playhead fixed and evaluate the updated pose, including bones.
        scene.frame_set(base_frame,subframe=frame-base_frame)

    def restore():
        restore_snapshot(saved)

    def valid():
        try:
            return obj.animation_data.action==native_action and context.scene==scene
        except (ReferenceError, AttributeError): return False

    def apply(value):
        factor=value/100.
        if action=='DRAG':
            options.factor=factor
            # Visual Breakdown samples the evaluated pose from the restored keys.
            if options.visual_transform:
                refresh()
            breakdown.apply_breakdown(context,obj,bones,options)
        elif action=='SCALE_DRAG': retime.apply_scale(curves,pivot,factor,snap=snap)
        elif action=='OFFSET_DRAG': retime.apply_offset(curves,value,snap=snap)
        elif action=='RIPPLE':
            delta=max(value,min(0.,earliest))
            if delta: retime.apply_ripple(curves,float(base_frame),delta,direction='FORWARD',snap=snap)
        elif action=='REDUCE':
            if value>0: _reduce(curves,value)
        else:
            for fc,keys,selected,reference in curve_data:
                chosen=[keys[i] for i in selected]
                if action=='SMOOTH': values=math_tools.smooth_keys(keys,selected,factor)
                elif action=='NEIGHBORS': values=math_tools.blend_to_neighbor(keys,selected,factor)
                elif action=='FRAME': values=math_tools.blend_toward_value(chosen,reference,factor)
                elif action=='AMPLIFY': values=math_tools.push_pull(chosen,reference,factor)
                elif action=='EASE': values=math_tools.ease_to_ease(chosen,factor)
                else: raise ValueError('Unknown scalar tool')
                if not all(math.isfinite(v) for v in values): raise ValueError('Adjustment produced an invalid value')
                curves_ops._write_values(fc,selected,values)
    return Transaction(restore,apply,valid,refresh=refresh)
