"""Pure presentation model; layouts contain no scene or gesture state."""
import copy
import json
import math
import uuid

FAMILY_ORDER = ('tween', 'timing', 'curves', 'keys', 'pose', 'bake', 'motion')
# One table drives the stage dropdown. Each stage's families are its home families:
# its defaults come from them and its row always shows their menus. Any row may
# also hold tools from other families (owner request 2026-10-18).
STAGES = (
    ('ALL', 'All', None),
    ('BLOCK', 'Block', ('tween', 'keys')),
    ('SPLINE', 'Spline', ('curves', 'motion')),
    ('POLISH', 'Polish', ('timing', 'pose')),
    ('DELIVER', 'Deliver', ('bake',)),
)
STAGE_IDS = tuple(key for key, _label, _families in STAGES)
# Saved enum numbers; never renumber an existing stage.
STAGE_NUMBERS = {'ALL': 0, 'BLOCK': 1, 'SPLINE': 2, 'POLISH': 3, 'DELIVER': 4}
STAGE_KEYS = tuple(key for key, _label, families in STAGES if families)
SCHEMA_VERSION = 2
# Stage setups add about 40% to each layout; keep room for 100 saved layouts with margin.
RECORD_LIMIT = 2_000_000
# Logical pixels reserved for the dropdown arrow on the compact stage button.
STAGE_ARROW = 10
MODES = ('HIDDEN', 'BUTTON', 'POPOUT', 'INLINE')
# Tools with a distinct row icon. Only these can show as an icon; any other tool
# asked to (older records) shows its name.
KEY_TYPE_ICONS = ('TYPE_KEYFRAME', 'TYPE_BREAKDOWN', 'TYPE_EXTREME', 'TYPE_HOLD', 'TYPE_JITTER')
HANDLE_ICONS = ('HANDLE_AUTO', 'HANDLE_CLAMPED', 'HANDLE_VECTOR', 'HANDLE_ALIGNED', 'HANDLE_FREE')
ICON_ACTIONS = frozenset(KEY_TYPE_ICONS + HANDLE_ICONS + (
    'NUDGE_LEFT', 'NUDGE_RIGHT', 'COPY_KEYS', 'PASTE_KEYS', 'GROW_LEFT', 'GROW_RIGHT', 'GROW_BOTH',
    'TO_SPLINE', 'TO_STEPPED', 'TRAIL_TOGGLE', 'INBETWEEN', 'INBETWEENS', 'REFERENCE',
    'OPPOSITE', 'MIRROR_SELECTED', 'MIRROR_ACTIVE', 'SWAP', 'BAKE_STEP',
    'PROXY_TRANSLATION', 'PROXY_ORIENTATION', 'PROXY_WORLD', 'PROXY_PARENT'))
# Stage tools that start as icons (owner decisions 2026-10-18: key types, then version B).
STAGE_ICON_DEFAULTS = {
    'BLOCK': frozenset(KEY_TYPE_ICONS + ('GROW_LEFT', 'GROW_RIGHT', 'COPY_KEYS', 'PASTE_KEYS',
                                         'INBETWEEN', 'INBETWEENS')),
    'SPLINE': frozenset(('TO_SPLINE', 'REFERENCE', 'HANDLE_CLAMPED', 'HANDLE_VECTOR', 'HANDLE_FREE',
                         'TRAIL_TOGGLE')),
    'POLISH': frozenset(('NUDGE_LEFT', 'NUDGE_RIGHT', 'OPPOSITE', 'MIRROR_SELECTED', 'MIRROR_ACTIVE', 'SWAP')),
    'DELIVER': frozenset(('BAKE_STEP', 'PROXY_TRANSLATION', 'PROXY_ORIENTATION', 'PROXY_WORLD',
                          'PROXY_PARENT')),
}
# Compact rows (owner decision 2026-10-18): these stage sliders draw their presets as
# click ticks on a wider track instead of preset buttons.
STAGE_TICK_DEFAULTS = {'BLOCK': {'DRAG'}, 'POLISH': {'SCALE_DRAG', 'RIPPLE'}, 'DELIVER': {'REDUCE'}}
TICK_TRACK = 140  # logical px of a tick track at full size
# Stage slider presets (version B): percentage buttons become one-click points on the
# slider. Breakdown -25/125 match Push Prev/Next and 25/75 Pull Prev/Next at the default
# Push/Pull Strength. All keeps the tool's own presets, so its row is unchanged.
STAGE_PRESET_DEFAULTS = {
    'BLOCK': {'DRAG': (-25., 25., 50., 75., 125.)},
    'POLISH': {'SCALE_DRAG': (80., 90., 110., 120.), 'RIPPLE': (-1., 1.)},
    # 0.01 is the existing Reduce/Smart Bake tolerance, so that preset equals the old button.
    'DELIVER': {'REDUCE': (.001, .01, .05)},
}
_B, _P, _I = 'BUTTON', 'POPOUT', 'INLINE'
# Fixed default toolsets, left to right in workflow order (owner decision:
# defaults never derive from a layout's All tools). Unlisted tools start Hidden.
STAGE_DEFAULTS = {
    'BLOCK': (('DRAG', _I), ('INBETWEEN', _B), ('INBETWEENS', _B),
              ('RANGE', _B), ('ALL', _B), ('ENDS', _B), ('GROW_LEFT', _B), ('GROW_RIGHT', _B),
              ('TYPE_KEYFRAME', _B), ('TYPE_BREAKDOWN', _B), ('TYPE_EXTREME', _B), ('TYPE_HOLD', _B),
              ('COPY_KEYS', _B), ('PASTE_KEYS', _B)),
    'SPLINE': (('TO_SPLINE', _B), ('NEIGHBORS', _I), ('EASE', _I), ('SMOOTH', _I),
               ('REFERENCE', _B), ('FRAME', _I), ('AMPLIFY', _I),
               ('HANDLE_CLAMPED', _B), ('HANDLE_VECTOR', _B), ('HANDLE_FREE', _B),
               ('TRAIL_TOGGLE', _B)),
    'POLISH': (('NUDGE_LEFT', _B), ('NUDGE_RIGHT', _B), ('SCALE_DRAG', _I),
               ('OFFSET_DRAG', _I), ('RIPPLE', _I), ('SNAP', _B),
               ('OPPOSITE', _B), ('MIRROR_SELECTED', _B), ('MIRROR_ACTIVE', _B), ('SWAP', _B)),
    'DELIVER': (('BAKE_STEP', _B), ('BAKE_PREVIEW', _B), ('SMART_BAKE', _B), ('REDUCE', _I), ('BAKE_INTEGER', _B),
                ('PROXY_BAKE', _B), ('PROXY_TRANSLATION', _B), ('PROXY_ORIENTATION', _B), ('PROXY_WORLD', _B),
                ('PROXY_PARENT', _B), ('BAKE_CLEANUP', _B), ('CLEANUP_ALL', _B)),
}
# Action -> family, registered by timeline_catalog (keeps this module bpy- and catalogue-free).
_FAMILY = {}


def register_families(groups):
    _FAMILY.clear()
    _FAMILY.update({action: key for key, _label, actions in groups for action in actions if action})


def family_of(action):
    if not _FAMILY: raise ValueError('Toolbar families are not registered')
    return _FAMILY.get(action)


def stage_default(stage):
    pairs = STAGE_DEFAULTS[stage]
    icons = STAGE_ICON_DEFAULTS.get(stage, ())
    presets = STAGE_PRESET_DEFAULTS.get(stage, {})
    ticks = STAGE_TICK_DEFAULTS.get(stage, set())
    tools = {}
    for a, m in pairs:
        tools[a] = dict(mode=m, label_mode='ICON' if a in icons else 'LABEL')
        if a in presets: tools[a]['presets'] = list(presets[a])
        if a in ticks: tools[a]['ticks'] = True
    return dict(order=[a for a, _m in pairs], tools=tools)


def preset_bounds(action):
    """Stage presets may go past a slider's display range, up to the tool's hard limits."""
    _label, _unit, _default, low, high, hard_min, hard_max = SLIDERS[action]
    return (hard_min if hard_min is not None else min(low, -1e8),
            hard_max if hard_max is not None else max(high, 1e8))


def tick_values(tool):
    """Presets drawn as ticks on this slider's track (empty when shown as buttons)."""
    return list(tool.get('presets', [])) if tool.get('ticks') else []


def track_range(tool):
    """Track span: the tool range, stretched to include any tick presets."""
    ticks = tick_values(tool)
    return min([tool['range_min'], *ticks]), max([tool['range_max'], *ticks])


def snap_to_tick(tool, value, fraction=.03):
    """A value within *fraction* of the track span of a tick lands exactly on it."""
    low, high = track_range(tool)
    near = [t for t in tick_values(tool) if abs(t - value) <= fraction * (high - low)]
    return min(near, key=lambda t: abs(t - value)) if near else value


def stage_presets(action, raw):
    if action not in SLIDERS: raise ValueError('Only numeric tools have presets')
    if not isinstance(raw, (list, tuple)) or len(raw) > 12: raise ValueError('Use at most 12 numeric presets')
    values = [finite(v, 'Preset') for v in raw]
    low, high = preset_bounds(action)
    if any(not low <= v <= high for v in values): raise ValueError('Presets must be inside the tool limits')
    return values


def has_icon(action):
    return action in ICON_ACTIONS


def shown_label_mode(action, label_mode):
    """Icon only for a tool that has one; otherwise its name."""
    return 'ICON' if label_mode == 'ICON' and has_icon(action) else 'LABEL'


def _check_mode(action, mode, label_mode):
    if mode not in MODES or (action not in SLIDERS and mode in {'POPOUT', 'INLINE'}):
        raise ValueError('This tool does not support the selected display mode')
    if label_mode not in {'LABEL', 'ICON'}: raise ValueError('Choose Label or Icon')


def validate_stage(stage, raw, actions):
    """Sparse stage setup: visible tools only, in order; Hidden entries dropped."""
    if not isinstance(raw, dict): raise ValueError('Stage setup must be an object')
    order, tools_raw = raw.get('order', []), raw.get('tools', {})
    if not isinstance(order, list) or not isinstance(tools_raw, dict):
        raise ValueError('Stage setup must contain an order and tools')
    if any(not isinstance(k, str) for k in order) or len(set(order)) != len(order):
        raise ValueError('Stage tool order must contain unique action IDs')
    if any(k in actions and k not in order for k in tools_raw):
        raise ValueError('Every stage tool must appear in its order')
    result = dict(order=[], tools={})
    for action in order:
        entry = tools_raw.get(action, {})
        if action not in actions:  # Forward compatibility: keep unknown tools intact.
            if not isinstance(entry, dict): raise ValueError('Stage tool settings must be an object')
            result['order'].append(action); result['tools'][action] = copy.deepcopy(entry); continue
        if not isinstance(entry, dict): raise ValueError('Stage tool settings must be an object')
        mode, label_mode = entry.get('mode', 'BUTTON'), entry.get('label_mode', 'LABEL')
        _check_mode(action, mode, label_mode)
        if mode == 'HIDDEN': continue
        result['order'].append(action)
        result['tools'][action] = dict(mode=mode, label_mode=shown_label_mode(action, label_mode))
        if 'presets' in entry and action in SLIDERS:
            result['tools'][action]['presets'] = stage_presets(action, entry['presets'])
        if 'ticks' in entry and action in SLIDERS:
            if type(entry['ticks']) is not bool: raise ValueError('Ticks must be on or off')
            result['tools'][action]['ticks'] = entry['ticks']
    for key, value in tools_raw.items():
        if key not in actions and key not in result['tools']:
            if not isinstance(value, dict): raise ValueError('Stage tool settings must be an object')
            result['tools'][key] = copy.deepcopy(value)
    return result
# (label, unit, neutral/default, display minimum, display maximum, hard minimum, hard maximum)
SLIDERS = {
    'DRAG': ('Breakdown', '%', 50., 0., 100., -100., 200.),
    'SMOOTH': ('Smooth', '%', 0., 0., 100., None, None),
    'NEIGHBORS': ('Neighbors', '%', 0., 0., 100., None, None),
    'FRAME': ('To Reference', '%', 0., 0., 100., None, None),
    'EASE': ('Ease', '%', 0., 0., 100., None, None),
    'AMPLIFY': ('Amplify', '%', 0., -100., 200., None, None),
    'SCALE_DRAG': ('Timing Scale', '%', 100., 50., 200., 1., None),
    'OFFSET_DRAG': ('Timing Offset', 'f', 0., -10., 10., None, None),
    # Ripple: frames to shift keys after the playhead; Reduce: key-reduction tolerance.
    'RIPPLE': ('Ripple', 'f', 0., -10., 10., -500., 500.),
    'REDUCE': ('Reduce', '', 0., 0., .1, 0., 1.),
}
SLIDER_PRECISION = {'REDUCE': 3}
# Recommended All row, compact (owner pick "A · Compact match", 2026-10-18): the same
# everyday tools as 12.9, with 25/50/75 as ticks on Breakdown and the small tools as icons.
RECOMMENDED_BUTTONS = {'NUDGE_LEFT', 'NUDGE_RIGHT', 'COPY_KEYS', 'PASTE_KEYS', 'MIRROR_SELECTED',
                       'BAKE_STEP', 'TRAIL_TOGGLE'}
RECOMMENDED_ICONS = RECOMMENDED_BUTTONS
RECOMMENDED_TICKS = {'DRAG': (25., 50., 75.)}


def tool_default(action):
    entry = dict(action=action, mode='HIDDEN', label_mode='LABEL', width=120.)
    if action in SLIDERS:
        label, unit, default, low, high, _min, _max = SLIDERS[action]
        entry.update(range_min=low, range_max=high, default=default, sensitivity=200.,
                     precision=SLIDER_PRECISION.get(action, 1), snap_enabled=False,
                     snap_step=.001 if action == 'REDUCE' else 1., presets=[],
                     overshoot_enabled=False, ticks=False)
    return entry


def recommended(actions):
    tools = {action: tool_default(action) for action in actions}
    for action in RECOMMENDED_BUTTONS & tools.keys(): tools[action]['mode'] = 'BUTTON'
    for action in RECOMMENDED_ICONS & tools.keys(): tools[action]['label_mode'] = 'ICON'
    for action, presets in RECOMMENDED_TICKS.items():
        if action in tools: tools[action].update(presets=list(presets), ticks=True)
    for action in ('DRAG', 'SMOOTH'):
        if action in tools: tools[action]['mode'] = 'INLINE'
    if 'SCALE_DRAG' in tools: tools['SCALE_DRAG']['mode'] = 'POPOUT'
    layout = dict(id='recommended', name='Recommended', order=list(actions), tools=tools,
                  stages={stage: stage_default(stage) for stage in STAGE_KEYS})
    return dict(schema_version=SCHEMA_VERSION, active=layout, active_saved_id='recommended', saved=[])


def finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(label+' must be a finite number')
    if abs(value) > 1e8: raise ValueError(label+' is outside the numeric display limit')
    return float(value)


def validate_tool(action, raw):
    if not isinstance(raw, dict): raise ValueError('Tool settings must be an object')
    result = tool_default(action)
    result.update({k: copy.deepcopy(v) for k, v in raw.items() if k in result})
    result['action'] = action
    if result['mode'] not in MODES or (action not in SLIDERS and result['mode'] in {'POPOUT','INLINE'}):
        raise ValueError('This tool does not support the selected display mode')
    if result['label_mode'] not in {'LABEL','ICON'}: raise ValueError('Choose Label or Icon')
    result['label_mode'] = shown_label_mode(action, result['label_mode'])
    result['width'] = finite(result['width'], 'Slider width')
    if not 80 <= result['width'] <= 240: raise ValueError('Slider width must be 80–240')
    if action not in SLIDERS: return result
    for name in ('range_min','range_max','default','sensitivity','snap_step'):
        result[name] = finite(result[name], name)
    low, high = result['range_min'], result['range_max']
    if low >= high: raise ValueError('Minimum must be below maximum')
    if not low <= result['default'] <= high: raise ValueError('Default must be inside the slider range')
    hard_min, hard_max = SLIDERS[action][-2:]
    if hard_min is not None and low < hard_min: raise ValueError('Minimum is below the tool limit')
    if hard_max is not None and high > hard_max: raise ValueError('Maximum exceeds the tool limit')
    if not 10 <= result['sensitivity'] <= 2000: raise ValueError('Sensitivity must be 10–2000 pixels')
    if result['snap_step'] <= 0: raise ValueError('Snap step must be positive')
    if type(result['precision']) is not int or not 0 <= result['precision'] <= 4:
        raise ValueError('Precision must be 0–4 decimal places')
    for name in ('snap_enabled','overshoot_enabled','ticks'):
        if type(result[name]) is not bool: raise ValueError(name+' must be a checkbox')
    if not isinstance(result['presets'], list) or len(result['presets']) > 12:
        raise ValueError('Use at most 12 numeric presets')
    result['presets'] = [finite(v,'Preset') for v in result['presets']]
    if any(not low <= v <= high for v in result['presets']): raise ValueError('Presets must be inside the range')
    if not result['overshoot_enabled']:
        standard_min,standard_max=SLIDERS[action][3:5]
        if any(not standard_min<=v<=standard_max for v in [result['default'],*result['presets']]):
            raise ValueError('Enable Custom Range / Overshoot for these amounts')
    return result


def validate_layout(raw, actions):
    if not isinstance(raw, dict) or not isinstance(raw.get('tools'), dict):
        raise ValueError('Layout must contain tool settings')
    if not isinstance(raw.get('id'), str) or not raw['id']: raise ValueError('Layout identity is missing')
    name = validate_name(raw.get('name',''), allow_recommended=True)
    order = raw.get('order', [])
    if not isinstance(order,list) or any(not isinstance(k,str) for k in order) or len(set(order)) != len(order):
        raise ValueError('Tool order must contain unique action IDs')
    tools = {k: validate_tool(k, raw['tools'].get(k,{})) for k in actions}
    # Keep unknown tool records intact, hidden from current UI, for forward compatibility.
    unknown = {k: copy.deepcopy(v) for k,v in raw['tools'].items() if k not in actions}
    tools.update(unknown)
    order = order + [k for k in tools if k not in order]
    # Schema 1 layouts have no stages: they get the fixed defaults (migration).
    stages_raw = raw.get('stages', {})
    if not isinstance(stages_raw, dict): raise ValueError('Stage setups must be an object')
    stages = {stage: validate_stage(stage, stages_raw[stage], actions) if stage in stages_raw
              else stage_default(stage) for stage in STAGE_KEYS}
    stages.update({k: copy.deepcopy(v) for k, v in stages_raw.items() if k not in STAGE_KEYS})
    return dict(id=raw['id'], name=name, order=order, tools=tools, stages=stages)


def validate(record, actions):
    if (not isinstance(record,dict) or type(record.get('schema_version')) is not int
            or record['schema_version'] not in (1, SCHEMA_VERSION)):
        raise ValueError('Unsupported toolbar layout version; keep the original settings file')
    saved = record.get('saved')
    if not isinstance(saved,list) or len(saved) > 100: raise ValueError('Layout library must have at most 100 entries')
    active = validate_layout(record.get('active'),actions)
    items = [validate_layout(item,actions) for item in saved]
    identities = [x['id'] for x in items]
    names = [x['name'].casefold() for x in items]
    if len(set(identities)) != len(items) or len(set(names)) != len(items):
        raise ValueError('Saved layouts need unique names and identities')
    if 'recommended' in identities or 'recommended' in names:
        raise ValueError('Recommended is a protected built-in layout')
    selected = record.get('active_saved_id')
    if selected is not None and selected not in ['recommended',*identities]: selected = None
    return dict(schema_version=SCHEMA_VERSION,active=active,active_saved_id=selected,saved=items)


def decode(raw, actions):
    if not isinstance(raw,str) or len(raw) > RECORD_LIMIT: raise ValueError('Toolbar settings record is too large')
    try: record = json.loads(raw)
    except (ValueError, TypeError) as exc: raise ValueError('Toolbar settings are not valid JSON') from exc
    return validate(record,actions)


def encode(record, actions):
    raw=json.dumps(validate(record,actions),ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False)
    if len(raw)>RECORD_LIMIT: raise ValueError('Layout library is too large; remove unused layouts')
    return raw


def from_legacy(actions, selected):
    result = recommended(actions)
    result['active_saved_id'] = None
    result['active'].update(id='custom',name='Custom')
    for key, tool in result['active']['tools'].items():
        tool['mode'] = ('POPOUT' if key in SLIDERS else 'BUTTON') if key in selected else 'HIDDEN'
    return result


def validate_name(name, allow_recommended=False):
    if not isinstance(name,str): raise ValueError('Enter a layout name')
    name = name.strip()
    if not name or len(name)>64: raise ValueError('Use a name with 1–64 characters')
    if not allow_recommended and name.casefold()=='recommended': raise ValueError('Recommended is reserved')
    return name


def save_as(record,name):
    name=validate_name(name)
    if any(x['name'].casefold()==name.casefold() for x in record['saved']):
        raise ValueError('That name already exists; choose another name or Update Saved Layout')
    item=copy.deepcopy(record['active']); item.update(id=uuid.uuid4().hex,name=name)
    record['saved'].append(item)
    record['active']=copy.deepcopy(item); record['active_saved_id']=item['id']


def load(record,ident,actions):
    item=recommended(actions)['active'] if ident=='recommended' else next((x for x in record['saved'] if x['id']==ident),None)
    if item is None: raise ValueError('Choose an existing saved layout')
    record['active']=copy.deepcopy(item); record['active_saved_id']=ident


def update_saved(record):
    ident=record['active_saved_id']
    if ident in {None,'recommended'}: raise ValueError('Use Save As to create your own layout')
    index=next((i for i,x in enumerate(record['saved']) if x['id']==ident),None)
    if index is None: raise ValueError('Saved layout no longer exists')
    record['saved'][index]=copy.deepcopy(record['active'])


def rename(record,ident,name):
    name=validate_name(name)
    if ident=='recommended': raise ValueError('Recommended cannot be renamed')
    if any(x['id']!=ident and x['name'].casefold()==name.casefold() for x in record['saved']):
        raise ValueError('That layout name already exists')
    item=next((x for x in record['saved'] if x['id']==ident),None)
    if item is None: raise ValueError('Choose an existing saved layout')
    item['name']=name
    if record['active_saved_id']==ident: record['active']['name']=name


def delete(record,ident):
    if ident=='recommended': raise ValueError('Recommended cannot be deleted')
    if not any(x['id']==ident for x in record['saved']): raise ValueError('Choose an existing saved layout')
    record['saved']=[x for x in record['saved'] if x['id']!=ident]
    if record['active_saved_id']==ident:
        record['active_saved_id']=None
        record['active'].update(id='custom',name='Custom')


def modified(record,actions):
    ident=record['active_saved_id']
    if ident is None: return True
    original=recommended(actions)['active'] if ident=='recommended' else next(x for x in record['saved'] if x['id']==ident)
    return record['active'] != original


def value_from_pointer(tool,start_value,delta,precise=False,snap=False):
    scale=(tool['range_max']-tool['range_min'])/tool['sensitivity']
    value=start_value+delta*scale*(.1 if precise else 1.)
    if tool['snap_enabled'] or snap: value=round(value/tool['snap_step'])*tool['snap_step']
    return min(tool['range_max'],max(tool['range_min'],value))


def effective_tool(action,tool):
    result=copy.deepcopy(tool)
    if action in SLIDERS and not tool['overshoot_enabled']:
        result['range_min'],result['range_max']=SLIDERS[action][3:5]
        result['default']=min(result['range_max'],max(result['range_min'],result['default']))
    return result


def stage_label(stage):
    return next((label for key,label,_ in STAGES if key==stage),'All')


def stage_families(stage):
    """Families a stage shows, in permanent order; unknown stages show all."""
    families=next((f for key,_,f in STAGES if key==stage),None)
    return FAMILY_ORDER if families is None else tuple(f for f in FAMILY_ORDER if f in families)


def row_families(layout, stage, *, view=None):
    """Families a row shows, in permanent order: All shows every family; a stage
    shows its home families plus any family it holds a visible tool from."""
    if stage not in STAGE_KEYS: return FAMILY_ORDER
    home = set(stage_families(stage))
    order, tools = stage_view(layout, stage) if view is None else view
    held = {family_of(a) for a in order
            if isinstance(tools.get(a), dict) and tools[a].get('mode', 'HIDDEN') != 'HIDDEN'}
    return tuple(f for f in FAMILY_ORDER if f in home or f in held)


def stage_for_family(family):
    """The single stage that shows a family; All when no stage lists it."""
    return next((key for key,_,families in STAGES if families and family in families),'ALL')


def hidden_family_note(stage,family,family_label,families=None):
    """Explain why a configured family is absent from the row, or ''.
    families: what the row shows (row_families); its home families by default."""
    if family in (stage_families(stage) if families is None else families): return ''
    return (f'The {stage_label(stage)} row has no {family_label} tools; add them in Toolbar Settings, '
            f'or choose All or {stage_label(stage_for_family(family))}.')


def next_stage(stage,step):
    index=STAGE_IDS.index(stage) if stage in STAGE_IDS else 0
    return STAGE_IDS[(index+step)%len(STAGE_IDS)]


def wrap_to_width(text, max_width, measure):
    """Greedy word wrap by measured width; a word wider than the line is split.
    Never drops text: joining the lines with spaces gives the words back."""
    lines, line = [], ''
    for word in text.split():
        while measure(word) > max_width and len(word) > 1:
            cut = max(1, next((i for i in range(len(word), 0, -1) if measure(word[:i]) <= max_width), 1))
            if line: lines.append(line); line = ''
            lines.append(word[:cut]); word = word[cut:]
        candidate = f'{line} {word}' if line else word
        if line and measure(candidate) > max_width:
            lines.append(line); line = word
        else:
            line = candidate
    if line: lines.append(line)
    return lines


def fit_tooltip(paragraphs, region_w, region_h, measure, scale, line_h, pad, preferred_w):
    """Wrap (text, role) paragraphs into (lines, width, height) for the region.
    Starts at the preferred width and widens up to the region before giving up;
    when even the full width is too short, DETAIL lines go first (last first)."""
    widest = max(1, region_w - 2 * pad)
    width = min(preferred_w, widest)
    kept = list(paragraphs)
    while True:
        lines = [(line, role) for text, role in kept for line in wrap_to_width(text, width - 2 * pad, measure)]
        height = len(lines) * line_h + 2 * pad
        if height <= region_h or (width >= widest and not any(r == 'DETAIL' for _, r in kept)):
            break
        if width < widest:
            width = min(widest, width * 1.5)
            continue
        index = max(i for i, (_, r) in enumerate(kept) if r == 'DETAIL')
        kept.pop(index)
    used = max((measure(line) for line, _ in lines), default=0) + 2 * pad
    return lines, min(width, used), height


def _stage_setup(layout, stage):
    return layout.setdefault('stages', {}).setdefault(stage, stage_default(stage))


def stage_view(layout, stage):
    """(order, tools) a stage shows: per-stage mode/label over shared tool settings."""
    if stage not in STAGE_KEYS: return layout['order'], layout['tools']
    setup = layout.get('stages', {}).get(stage) or stage_default(stage)
    tools = {k: dict(v, mode='HIDDEN') if isinstance(v, dict) else v for k, v in layout['tools'].items()}
    for action in setup['order']:
        if isinstance(layout['tools'].get(action), dict) and isinstance(setup['tools'].get(action), dict):
            tools[action] = dict(layout['tools'][action], **setup['tools'][action])
    return list(setup['order']) + [k for k in layout['order'] if k not in setup['order']], tools


def reset_stage(record, stage):
    record['active'].setdefault('stages', {})[stage] = stage_default(stage)


def pin_target(stage, action):
    """The setup a pin changes: the row shown. Any row may hold any tool."""
    return stage if stage in STAGE_KEYS else 'ALL'


def set_stage_tool(record, stage, action, mode=None, label_mode=None, presets=None, ticks=None):
    """Change one tool's mode/label in All or a stage; showing a stage tool
    places it after the last visible tool of its family."""
    layout = record['active']
    if stage not in STAGE_KEYS:
        tool = layout['tools'][action]
        if mode is not None: tool['mode'] = mode
        if label_mode is not None: tool['label_mode'] = shown_label_mode(action, label_mode)
        if ticks is not None and action in SLIDERS: tool['ticks'] = bool(ticks)
        return
    setup = _stage_setup(layout, stage)
    current = setup['tools'].get(action)
    mode = mode or (current['mode'] if current else 'HIDDEN')
    label_mode = shown_label_mode(action, label_mode or (current['label_mode'] if current else 'LABEL'))
    if mode == 'HIDDEN':
        if action in setup['order']: setup['order'].remove(action)
        setup['tools'].pop(action, None)
        return
    if action not in setup['order']:
        family = family_of(action)
        same = [i for i, a in enumerate(setup['order']) if family_of(a) == family]
        later = [i for i, a in enumerate(setup['order'])
                 if family_of(a) in FAMILY_ORDER and family in FAMILY_ORDER
                 and FAMILY_ORDER.index(family_of(a)) > FAMILY_ORDER.index(family)]
        index = same[-1] + 1 if same else (later[0] if later else len(setup['order']))
        setup['order'].insert(index, action)
    entry = dict(mode=mode, label_mode=label_mode)
    if presets is not None and action in SLIDERS: entry['presets'] = stage_presets(action, presets)
    elif current and 'presets' in current: entry['presets'] = list(current['presets'])
    if ticks is not None and action in SLIDERS: entry['ticks'] = bool(ticks)
    elif current and 'ticks' in current: entry['ticks'] = current['ticks']
    setup['tools'][action] = entry


def stage_entries(record, stage, actions):
    """Settings rows for a setup: every tool, grouped by family in permanent order;
    within a family, the row's order (visible tools first in a stage)."""
    layout = record['active']
    order, tools = stage_view(layout, stage)
    rank = {f: i for i, f in enumerate(FAMILY_ORDER)}
    listed = [a for a in order if a in actions]
    listed.sort(key=lambda a: rank.get(family_of(a), len(rank)))  # stable: keeps order within a family
    return [dict(action=a, family=family_of(a), mode=tools[a]['mode'],
                 label_mode=tools[a]['label_mode'], width=tools[a]['width']) for a in listed]


def apply_entries(record, stage, entries, actions):
    """Store settings rows back; widths are shared by All and every stage."""
    layout = record['active']
    for entry in entries:
        layout['tools'][entry['action']]['width'] = entry['width']
    listed = [e['action'] for e in entries]
    if stage not in STAGE_KEYS:
        layout['order'] = listed + [k for k in layout['order'] if k not in listed]
        for entry in entries:
            layout['tools'][entry['action']].update(mode=entry['mode'], label_mode=entry['label_mode'])
        return
    old = _stage_setup(layout, stage)
    visible = [e for e in entries if e['mode'] != 'HIDDEN']
    setup = dict(order=[e['action'] for e in visible],
                 tools={e['action']: dict(mode=e['mode'], label_mode=shown_label_mode(e['action'], e['label_mode']))
                        for e in visible})
    for action, tool in setup['tools'].items():
        if 'presets' in old['tools'].get(action, {}): tool['presets'] = list(old['tools'][action]['presets'])
        if 'ticks' in old['tools'].get(action, {}): tool['ticks'] = old['tools'][action]['ticks']
    for key in old['order']:
        if key not in actions and key not in setup['tools']:
            setup['order'].append(key); setup['tools'][key] = copy.deepcopy(old['tools'].get(key, {}))
    for key, value in old['tools'].items():
        if key not in actions and key not in setup['tools']: setup['tools'][key] = copy.deepcopy(value)
    layout['stages'][stage] = setup


def toolbar_layout(width,height,row_height,at_top,record,groups,labels,measure,stage='ALL',*,view=None):
    """Bounded presentation only; never modify the saved layout on overflow."""
    scale=row_height/28.
    gap=3*scale; pad=5*scale
    y=max(0,height-row_height) if at_top else 0
    h=max(1,min(height,row_height)-4*scale)
    families={key:(label,{a for a in actions if a is not None}) for key,label,actions in groups}
    # Each utility has one job (owner pick "C", 2026-10-18): Find is a magnifier icon
    # that reaches every tool; More appears only when tools did not fit, as "+N".
    settings_label='Settings'
    utility_widths=[24*scale,max(24*scale,measure(settings_label)+2*pad)]
    if sum(utility_widths)+3*gap>width:
        settings_label=''; utility_widths=[24*scale,24*scale]
    more_w=max(24*scale,measure('+99')+2*pad)
    full_budget=max(0,width-sum(utility_widths)-3*gap)
    budget=full_budget
    label=stage_label(stage)
    if measure(label)+2*pad+STAGE_ARROW*scale>budget*.5: label=label[0]
    # The compact stage button opens a dropdown; leave room for its arrow.
    cycle_w=max(24*scale,measure(label)+2*pad+STAGE_ARROW*scale)
    if gap+cycle_w>budget: cycle_w=max(24*scale,measure(label)+2*pad)  # extreme width: no arrow
    cycle=[('STAGE_CYCLE','CYCLE',label,cycle_w)]

    active = record['active']
    order, tools = stage_view(active, stage) if view is None else view
    row_groups = row_families(active, stage, view=(order, tools))

    def compose(compact=False,demote=False,no_families=False,named=False):
        specs=[]
        for family in row_groups:
            label,known=families[family]
            selected=[a for a in order if a in known and tools[a]['mode']!='HIDDEN']
            if not no_families:
                specs.append(('MENU',family,label,measure(label)+(6 if compact else 10)*scale))
            for action in selected:
                tool=tools[action]; mode=tool['mode']
                label=SLIDERS[action][0] if action in SLIDERS else labels.get(action,action.replace('_',' ').title())
                icon=shown_label_mode(action,tool['label_mode'])=='ICON'
                ticked=bool(tick_values(tool)) and mode=='INLINE' and not demote
                if mode=='INLINE' and not demote:
                    # named: compact track that keeps the slider's name (before names are dropped).
                    label='' if compact and not named else label
                    track=(64 if named else 80) if compact else tool['width']
                    if ticked: track=max(track, TICK_TRACK*(.7 if compact else 1))
                    w=track*scale+measure(label)+(46 if compact else 54)*scale
                    kind='SLIDER'
                else:
                    kind='POPOUT' if mode in {'POPOUT','INLINE'} else 'ACTION'
                    if icon: label=''
                    w=max(24*scale,measure(label)+2*pad)
                specs.append((kind,action,label,w))
                if action in SLIDERS and not ticked:
                    for value in tool['presets']:
                        text=f'{value:g}'
                        specs.append(('PRESET',action+':'+text,text,max(24*scale,measure(text)+2*pad)))
        return specs

    fits=lambda specs,room=None:sum(i[3]+gap for i in specs)<=(budget if room is None else room)
    # The stage is always one dropdown button (owner request 2026-10-18: the five
    # stages as dropdown options, not side by side), at every width and stage.
    lead=cycle
    variants = ({}, {'compact': True, 'named': True}, {'compact': True},
                {'compact': True, 'demote': True},
                {'compact': True, 'demote': True, 'no_families': True})
    candidates = []
    tool_kinds={'ACTION','SLIDER','POPOUT'}

    def place(room):
        for index, variant in enumerate(variants):
            if index == len(candidates):
                candidates.append(lead + compose(**variant))
            specs = candidates[index]
            if fits(specs, room):
                break
        placed=[]; x=gap
        for kind,key,label,w in specs:
            if x+w>room: continue
            placed.append((kind,key,label,(x,y+2*scale,w,h)))
            x+=w+gap
        shown={key for kind,key,_l,_r in placed if kind in tool_kinds}
        hidden=[key for kind,key,_l,_w in specs if kind in tool_kinds and key not in shown]
        return placed,x,hidden

    controls,x,hidden=place(full_budget)
    if hidden:
        # Some tools did not fit: make room for the "+N" button and place again.
        # The stage control always stays; on a very narrow row Settings drops its
        # name before the stage control would be squeezed out.
        lead_w=sum(i[3]+gap for i in lead)
        if settings_label and full_budget-more_w-gap<lead_w:
            settings_label=''; utility_widths=[24*scale,24*scale]
            full_budget=max(0,width-sum(utility_widths)-3*gap)
        controls,x,hidden=place(max(lead_w,full_budget-more_w-gap))
    utilities=([('MORE','',f'+{len(hidden)}')] if hidden else [])+[('SEARCH','',''),('SETTINGS','',settings_label)]
    widths=([more_w] if hidden else [])+utility_widths
    if hidden and x+sum(widths)+len(widths)*gap>width:
        utilities,widths=utilities[1:],widths[1:]  # extreme width: Find still reaches every tool
    x=max(x,width-sum(widths)-(len(widths)-1)*gap-gap)
    for (kind,key,label),w in zip(utilities,widths):
        if x+w<=width:
            controls.append((kind,key,label,(x,y+2*scale,w,h)))
        x+=w+gap
    return controls


def slider_parts(rect,label,measure,scale):
    x,y,w,h=rect
    label_width=measure(label)+4*scale if label else 0
    reset=(x+w-18*scale,y,18*scale,h)
    value=(reset[0]-34*scale,y,34*scale,h)
    track=(x+label_width+3*scale,y+3*scale,max(1,value[0]-x-label_width-6*scale),h-6*scale)
    return track,value,reset
