# SPDX-License-Identifier: GPL-2.0-or-later

from collections import defaultdict
from dataclasses import dataclass, field, replace
from itertools import chain, combinations, groupby, pairwise
from operator import gt, itemgetter, lt
from statistics import fmean

import bpy
from bpy.types import NodeFrame, Operator
from bl_math import clamp
from mathutils import Vector
from mathutils.geometry import interpolate_bezier

# -------------------------------------------------------------------

MAX_LOC = 100_000
HIDE_OFFSET = 10
HIDDEN_NODE_FLAT_WIDTH = 116
BOTTOM_OFFSET = 14.85
TOP_OFFSET = 35
VISIBLE_PBSDF_SOCKETS = 5
SOCKET_SPACING_MULTIPLIER = 22
FRAME_PADDING = 29.8
COMPACT_HEIGHT = 450
EPS = 65
MIN_ADJ_COLS = 2
DISPERSE_MULT = 4
TARGET_NODE_TYPES = {'ShaderNodeBsdfPrincipled', 'ShaderNodeDisplacement'}

# -------------------------------------------------------------------
#   Parents and children
# -------------------------------------------------------------------


def get_parents(node):
    if parent := node.parent:
        yield parent
        yield from get_parents(parent)


def get_nested_children(frame):
    try:
        yield from Maps.used_children[frame]
    except KeyError:
        return

    for node in Maps.selected:
        if node.bl_idname == 'NodeFrame' and node.parent == frame:
            yield from get_nested_children(node)


def is_parented(a, b):
    if not isinstance(a, NodeFrame) or not isinstance(b, NodeFrame):
        return False

    return b in get_parents(a) or a in get_parents(b)


# -------------------------------------------------------------------
#   Flatten links
# -------------------------------------------------------------------


def get_input_nodes(*nodes):
    from_nodes = []
    for node in nodes:
        from_nodes.extend(chain(*[Maps.links[i] for i in node.inputs]))

    return from_nodes


def get_output_nodes(*nodes):
    to_nodes = []
    for node in nodes:
        to_nodes.extend(chain(*[Maps.links[o] for o in node.outputs]))

    return to_nodes


# -------------------------------------------------------------------
#   Locations
# -------------------------------------------------------------------


def abs_loc(node):
    loc = node.location.copy()
    for parent in get_parents(node):
        loc += parent.location

    return loc


def get_right(node):
    return abs_loc(node).x + node.dimensions.x / 2


def get_top(node, y_loc=None):
    if y_loc is None:
        y_loc = abs_loc(node).y

    return (y_loc + node.dimensions.y / 4) - HIDE_OFFSET if node.hide else y_loc


def get_bottom(node, y_loc=None):
    if y_loc is None:
        y_loc = abs_loc(node).y

    dim_y = node.dimensions.y / 2
    bottom = y_loc - dim_y
    return bottom + dim_y / 2 - HIDE_OFFSET if node.hide else bottom


def get_hidden_socket_y(socket):
    node = socket.node
    x, y = abs_loc(node)

    top = get_top(node, y)
    bottom = get_bottom(node, y)

    cap_width = (node.dimensions.x / 2 - HIDDEN_NODE_FLAT_WIDTH) / 2
    inner = x + cap_width
    outer = x - cap_width / 3

    raw_sockets = node.outputs if socket.is_output else node.inputs
    sockets = [s for s in raw_sockets if not s.is_unavailable]

    vectors = map(Vector, ((inner, top), (outer, top), (inner, bottom), (outer, bottom)))
    points = interpolate_bezier(*vectors, len(sockets) + 2)[1:-1]

    return points[sockets.index(socket)].y


def get_input_y(input, accurate=True):
    node = input.node

    if not accurate or node.bl_idname == 'NodeReroute':
        return get_top(node)

    if node.hide:
        return get_hidden_socket_y(input)

    y = get_top(node)

    inputs = [i for i in node.inputs if not i.is_unavailable]
    if node.bl_idname != 'ShaderNodeBsdfPrincipled':
        # Start from the bottom socket to avoid any node properties
        y -= node.dimensions.y / 2 - BOTTOM_OFFSET
        inputs.reverse()
        idx = inputs.index(input)

        for i in inputs[:idx + 1]:
            if i.type in {'VECTOR', 'ROTATION', 'MATRIX'} and not i.hide_value and not i.is_linked:
                y += (SOCKET_SPACING_MULTIPLIER * 0.909) * len(i.default_value)
    else:
        y -= 56.5
        idx = -inputs.index(input)
        if idx < -VISIBLE_PBSDF_SOCKETS:
            panels = ('Subsurface', 'Specular', 'Transmission', 'Coat', 'Sheen', 'Emission')
            idx = -(VISIBLE_PBSDF_SOCKETS + 0.5 + panels.index(input.name.split()[0]))

    return y + idx * SOCKET_SPACING_MULTIPLIER


def get_output_y(output, accurate=True):
    node = output.node

    if not accurate or node.bl_idname == 'NodeReroute':
        return get_top(node)

    if node.hide:
        return get_hidden_socket_y(output)

    y = get_top(node) - TOP_OFFSET
    outputs = [o for o in node.outputs if not o.is_unavailable]
    return y - outputs.index(output) * SOCKET_SPACING_MULTIPLIER


def corrected_y(node, target_y):
    y = abs_loc(node).y
    return target_y + (y - get_top(node)) if y != target_y else y


# -------------------------------------------------------------------
#   Boxes
# -------------------------------------------------------------------


# This descriptor is meant to solve most floating point comparison issues
class Side(object):

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, val):
        instance.__dict__[self.name] = round(val, 2)


@dataclass(slots=True)
class Box:
    left: float = field(default=Side())
    bottom: float = field(default=Side())
    right: float = field(default=Side())
    top: float = field(default=Side())

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.top - self.bottom

    @property
    def center(self):
        return Vector((self.left + self.right, self.bottom + self.top)) / 2

    def line_x(self):
        return [self.left, self.right]

    def line_y(self):
        return [self.bottom, self.top]

    def expand(self, x=0, y=0):
        self.left -= x
        self.right += x

        self.bottom -= y
        self.top += y

    def move(self, *, x=0, y=0):
        self.left += x
        self.right += x

        self.bottom += y
        self.top += y

    def overlaps(self, other, offset=0.01):
        # yapf: disable
        return not (
          self.right - offset < other.left + offset
          or self.left + offset > other.right - offset
          or self.top - offset < other.bottom + offset
          or self.bottom + offset > other.top - offset)
        # yapf: enable

    def leftwards(self, boxes):
        try:
            return next(k for k, b in reversed(boxes.items()) if b.right <= self.left)
        except StopIteration:
            return None

    def rightwards(self, boxes):
        try:
            return next(k for k, b in boxes.items() if b.left >= self.right)
        except StopIteration:
            return None


def get_box(nodes):
    x_vals = []
    y_vals = []
    for node in nodes:
        x, y = abs_loc(node)
        x_vals.extend((x, x + node.dimensions.x / 2))
        y_vals.extend((get_top(node, y), get_bottom(node, y)))

    return Box(min(x_vals), min(y_vals), max(x_vals), max(y_vals))


def get_frame_box(frame, expand=True):
    # `frame.width` and `frame.height` can't be used here: since they only
    # get evaluated on UI redraw, they'll be incorrect if the rearrangement of
    # the frame's children changed the frame's size.

    children = tuple(get_nested_children(frame))
    box = get_box(children)

    box.expand(FRAME_PADDING, FRAME_PADDING)
    if frame.label:
        box.top -= (FRAME_PADDING / 2) - frame.label_size * 1.25

    if expand:
        if len(children) == 1:
            box.expand(y=MARGIN.y / 4)
        else:
            box.expand(*MARGIN / 2)

    return box


def get_col_boxes(columns):
    subcolumns = []
    for col in columns:
        if len(col) == 1:
            subcolumns.append(col)
            continue

        col.sort(key=get_top, reverse=True)
        curr_idx = 0
        for i, j in pairwise(range(len(col))):
            if get_bottom(col[i]) - get_top(col[j]) > MARGIN.y:
                subcolumns.append(col[curr_idx:i + 1])
                curr_idx = j

        subcolumns.append(col[curr_idx:j + 1])

    col_boxes = {
      tuple(c): get_box(c)
      for c in subcolumns
      if not all(n.bl_idname == 'NodeReroute' for n in c)}

    for box in col_boxes.values():
        box.expand(*MARGIN / 2)

    return col_boxes


def sorted_boxes(boxes):
    return dict(sorted(boxes.items(), key=lambda kb: kb[1].left))


def get_box_rows(boxes):
    tops = {k: b.top for k, b in boxes.items()}
    boxes_ascending = sorted(boxes, key=tops.get)

    prev_key = boxes_ascending[0]
    row = [prev_key]
    rows = []
    for key in boxes_ascending[1:]:
        if tops[key] <= tops[prev_key] + EPS:
            row.append(key)
        else:
            rows.append(row)
            row = [key]

        prev_key = key

    rows.append(row)

    for row in rows:
        row.sort(key=lambda k: boxes[k].left)

    return rows


def lines_overlap(line1, line2, offset=0.01):
    b1, a1 = line1
    b2, a2 = line2

    a1 -= offset
    b1 += offset
    a2 -= offset
    b2 += offset

    # yapf: disable
    return (
      (b1 <= a2 <= a1)
      or (b1 <= b2 <= a1)
      or (a2 < a1 and b1 < b2)
      or (a1 < a2 and b2 < b1))
    # yapf: enable


# -------------------------------------------------------------------
#   Update locations
# -------------------------------------------------------------------


def move(node, *, x=0, y=0):
    if x == 0 and y == 0:
        return

    # If the (absolute) value of a node's X/Y axis exceeds 100k,
    # `node.location` can't be affected directly. (This often happens with
    # frames since their locations are relative.)

    loc = node.location
    if abs(loc.x + x) <= MAX_LOC and abs(loc.y + y) <= MAX_LOC:
        loc += Vector((x, y))
        return

    for n in Maps.selected:
        n.select = n == node

    bpy.ops.transform.translate(value=[v * 2 for v in (x, y, 0)])

    for n in Maps.selected:
        n.select = True


def move_to(node, *, x=None, y=None):
    loc = abs_loc(node)
    if x is not None and y is None:
        move(node, x=x - loc.x)
    elif y is not None and x is None:
        move(node, y=y - loc.y)
    else:
        move(node, x=x - loc.x, y=y - loc.y)


def move_nodes(nodes, *, x=0, y=0):
    for node in {n.parent or n for n in nodes}:
        if node.bl_idname != 'NodeFrame' or not node.parent:
            move(node, x=x, y=y)


# -------------------------------------------------------------------
#   Generate maps
# -------------------------------------------------------------------


def get_links(ntree):
    # Precompute links to:
    # 1. Avoid `O(len(ntree.links))` time
    # 2. Ignore invalid/hidden links
    # 3. Ignore links to unused nodes
    # 4. Ignore links to/from unselected nodes

    links = Maps.links
    sockets = Maps.sockets

    for link in ntree.links:
        if link.is_hidden:
            continue

        links[link.to_socket].append(link.from_node)
        sockets[link.to_socket].append(link.from_socket)

        links[link.from_socket].append(link.to_node)
        sockets[link.from_socket].append(link.to_socket)


def get_columns(output_nodes):
    columns = [output_nodes]
    idx = 0
    while columns[idx]:
        columns.append(tuple(dict.fromkeys(get_input_nodes(*columns[idx]))))
        idx += 1

    del columns[idx]

    for col1 in reversed(columns):
        for i, col2 in enumerate(columns):
            if col1 != col2:
                columns[i] = [n for n in col2 if n not in col1]

    return [sc for uc in columns if (sc := [n for n in uc if n.select])]


def min_col_idx(item):
    universal_columns = Maps.universal_columns
    idxs = []
    for col in item[1]:
        idxs.append(next(i for i, c in enumerate(universal_columns) if any(n in c for n in col)))

    return min(idxs)


def get_frame_columns():
    frame_columns = {}
    for frame, children in Maps.all_children.items():
        columns = [fc for c in Maps.universal_columns if (fc := [n for n in c if n in children])]
        if any(columns):
            frame_columns[frame] = columns

    Maps.frame_columns.update(sorted(frame_columns.items(), key=min_col_idx))
    Maps.used_children.update({f: tuple(chain(*c)) for f, c in Maps.frame_columns.items()})


# -------------------------------------------------------------------
#   Base arrange
# -------------------------------------------------------------------


def get_arranged(columns):
    arranged = {}
    for i, col in enumerate(columns):
        if i != 0:
            max_width = max([n.dimensions.x / 2 for n in col])
            x = prev_x - (max_width + MARGIN.x)
        else:
            x = 0

        prev_x = x

        y = 0
        for node in col:
            y = corrected_y(node, y)
            arranged[node] = Vector((x, y))
            y = get_bottom(node, y) - MARGIN.y

    return arranged


def arrange_frame_columns():
    universal_arranged = get_arranged(Maps.universal_columns)
    for frame, columns in Maps.frame_columns.items():
        arranged = get_arranged(columns)

        if frame:
            virtual_x, virtual_y = zip(*[universal_arranged[n] for n in chain(*columns)])
            avg_universal_loc = Vector((fmean(virtual_x), fmean(virtual_y)))
            for node, vec in arranged.items():
                vec += avg_universal_loc

        for node, (x, y) in arranged.items():
            move_to(node, x=x, y=y)


# -------------------------------------------------------------------
#   Link lengths
# -------------------------------------------------------------------


def link_stretch(nodes, movement=0):
    stretch = 0
    for node in nodes:
        x = abs_loc(node).x + movement
        right = x + node.dimensions.x / 2
        for socket in chain(node.inputs, node.outputs):
            for linked in Maps.links[socket]:
                if linked in nodes:
                    continue

                dist = abs_loc(linked).x - right if socket.is_output else x - get_right(linked)
                if dist < 0:
                    stretch -= dist

    return stretch


def get_input_lengths(nodes):
    lengths = {}
    for node in nodes:
        input_x = abs_loc(node).x
        for from_node in get_input_nodes(node):
            if from_node in nodes:
                continue

            dist = input_x - get_right(from_node)
            if from_node not in lengths or lengths[from_node] > dist:
                lengths[from_node] = dist

    return lengths


def get_output_lengths(nodes):
    lengths = {}
    for node in nodes:
        output_x = get_right(node)
        for to_node in get_output_nodes(node):
            if to_node in nodes:
                continue

            dist = abs_loc(to_node).x - output_x
            if to_node not in lengths or lengths[to_node] > dist:
                lengths[to_node] = dist

    return lengths


# -------------------------------------------------------------------
#   Make space for stretched
# -------------------------------------------------------------------


def get_successors(nodes, seen=None):
    if seen is None:
        seen = set()

    for node in nodes:
        if node in seen:
            continue

        yield node
        seen.add(node)

        queue = set(get_output_nodes(node))
        parent = node.parent

        if parent:
            queue.update(Maps.used_children[parent])

        columns = Maps.frame_columns[parent]
        try:
            idx = next(i for i, c in enumerate(columns) if node in c)
        except StopIteration:
            pass
        else:
            queue.update(chain(*columns[:idx + 1]))

        yield from get_successors(queue, seen)


def get_predecessors(nodes, seen=None):
    if seen is None:
        seen = set()

    for node in nodes:
        if node in seen:
            continue

        yield node
        seen.add(node)

        for input in node.inputs:
            yield from get_predecessors(Maps.links[input], seen)


def ideal_x_movement(nodes, line_x):
    from_x = []
    to_x = []
    for node in nodes:
        input_x = abs_loc(node).x
        output_x = get_right(node)
        to_x.extend([(abs_loc(n).x, output_x) for n in get_output_nodes(node) if n not in nodes])
        from_x.extend([(get_right(n), input_x) for n in get_input_nodes(node) if n not in nodes])

    dist_to_x = lambda io: io[0] - io[1]
    dist_from_x = lambda oi: oi[1] - oi[0]

    if from_x and to_x:
        nright, right = min(to_x, key=dist_to_x)
        nleft, left = min(from_x, key=dist_from_x)

        movement = (nleft + nright - left - right) / 2

        if stretch := link_stretch(nodes, movement):
            try:
                nleft, left = next(oi for oi in sorted(from_x, key=dist_from_x) if oi[0] < nright)
            except StopIteration:
                return movement

            new_movement = (nleft + nright - left - right) / 2
            if stretch > link_stretch(nodes, new_movement):
                return new_movement

        return movement

    left, right = line_x

    if from_x:
        target_x, left = min(from_x, key=dist_from_x)
        target_x += (right - left)
    elif to_x:
        target_x, right = min(to_x, key=dist_to_x)
        target_x -= (right - left)
    else:
        return 0

    return target_x - (left + right) / 2


def ideal_frame_x_movement(frame):
    children = Maps.used_children[frame]
    return ideal_x_movement(children, get_box(children).line_x())


def resolved_with_min_movement(children):
    # Move the children's immediate successor rightwards, then move the
    # children's frame rightwards, and see if it's resolved.

    frame = children[0].parent
    from_node, from_dist = min(get_input_lengths(children).items(), key=itemgetter(1))
    to_node, to_dist = min(get_output_lengths(children).items(), key=itemgetter(1))

    if frame in chain(get_parents(to_node), get_parents(from_node)):
        return False

    if from_dist < 0:
        from_frame = from_node.parent
        from_nodes = Maps.used_children[from_frame] if from_frame else [from_node]
        from_movement = from_dist - MARGIN.x * 2

        if link_stretch(from_nodes, from_movement):
            return False

    if to_dist < 0:
        to_frame = to_node.parent
        to_movement = abs(to_dist) + MARGIN.x * 2
        if to_frame:
            if link_stretch(Maps.used_children[to_frame], to_movement):
                return False

            move(to_frame, x=to_movement)
        else:
            if link_stretch([to_node], to_movement):
                return False

            move(to_node, x=to_movement)

    if from_dist < 0:
        node = to_frame if from_frame else from_node
        move(node, x=from_movement)

    movement = ideal_frame_x_movement(frame)

    if link_stretch(children, movement):
        return False

    move(frame, x=movement)
    return True


def make_space_for_stretched(frame):
    if not frame:
        return

    children = Maps.used_children[frame]

    to_move = set(get_successors(get_output_nodes(*children)))
    to_move -= set(get_predecessors(get_input_nodes(*children))) | set(children)

    Maps.frame_successors[frame] = to_move

    move(frame, x=ideal_frame_x_movement(frame))

    from_stretch = []
    to_stretch = []
    for node in children:
        from_stretch.extend([d for d in get_input_lengths([node]).values() if d < 0])
        to_stretch.extend([d for d in get_output_lengths([node]).values() if d < 0])

    movement = 0

    if from_stretch:
        movement += abs(min(from_stretch)) + MARGIN.x * 2

    if to_stretch:
        movement += abs(min(to_stretch)) + MARGIN.x * 2

    if movement != 0 and not resolved_with_min_movement(children):
        move_nodes(to_move, x=movement)
        move(frame, x=ideal_frame_x_movement(frame))


# -------------------------------------------------------------------
#   Regenerate columns
# -------------------------------------------------------------------


def move_outlier(node):
    try:
        input_dist = min(get_input_lengths([node]).values())
        output_dist = min(get_output_lengths([node]).values())
    except ValueError:
        return

    if input_dist >= 0:
        return

    if output_dist < 0 or output_dist < abs(input_dist):
        return

    line_x = (abs_loc(node).x, get_right(node))
    movement = ideal_x_movement([node], line_x)
    if link_stretch([node]) >= link_stretch([node], movement):
        move(node, x=movement)


def get_new_columns(frame):
    sorted_nodes = sorted(Maps.used_children[frame], key=lambda n: abs_loc(n).x)
    col = [sorted_nodes[0]]
    columns = []
    for node in sorted_nodes[1:]:
        max_right = max([abs_loc(n).x + n.dimensions.x / 4 for n in col])
        if abs_loc(node).x <= max_right:
            col.append(node)
        else:
            columns.append(col)
            col = [node]

    columns.append(col)

    return columns


def align_columns(columns):
    for col in columns:
        col.sort(key=lambda n: n.dimensions.x, reverse=True)

    for i, col in enumerate(columns):
        x = abs_loc(col[0]).x

        for node in col:
            move_to(node, x=x)

        if i == 0:
            continue

        prev = columns[i - 1][0]
        movement = -x + get_right(prev) + MARGIN.x

        if movement <= 0:
            continue

        to_move = [f for f in Maps.frame_columns if f and get_frame_box(f, False).left > x]
        to_move.extend(chain(*columns[i:]))
        move_nodes(to_move, x=movement)


def line_overlap_vector(target, lines):
    l1 = lines[target]
    center = sum(l1) / 2

    y = [sum(l2) / 2 - center for n, l2 in lines.items() if target != n and lines_overlap(l1, l2)]

    if not y:
        return 0

    return clamp(-fmean(y), -1, 1) if any(y) else 1


def disperse_nodes_y(col):
    margin = MARGIN.y / 2
    lines = {n: [get_bottom(n) - margin, get_top(n) + margin] for n in col}

    pairs = [(lines[n1], lines[n2]) for n1, n2 in combinations(lines, 2)]
    while any(lines_overlap(l1, l2) for l1, l2 in pairs):
        for node, line in lines.items():
            movement = line_overlap_vector(node, lines)
            line[0] += movement
            line[1] += movement

    for node, line in lines.items():
        move_to(node, y=corrected_y(node, line[1] - margin))


def regenerate_columns(frame):
    for node in Maps.used_children[frame]:
        move_outlier(node)

    new_columns = get_new_columns(frame)
    align_columns(new_columns)

    for col in new_columns:
        disperse_nodes_y(col)
        col.sort(key=lambda n: abs_loc(n).y)

    new_columns.reverse()
    Maps.frame_columns[frame] = new_columns


# -------------------------------------------------------------------
#   Arrange principled
# -------------------------------------------------------------------


def get_successors_simple(nodes):
    for node in nodes:
        yield node
        for output in node.outputs:
            yield from get_successors_simple(Maps.links[output])


def arrange_principled():
    for col in Maps.universal_columns:
        if target_nodes := [n for n in col if n.bl_idname in TARGET_NODE_TYPES]:
            break
    else:
        return

    all_image_nodes = [
      n for n in get_predecessors(target_nodes) if n.bl_idname == 'ShaderNodeTexImage']

    if not all_image_nodes:
        return

    groups = defaultdict(list)
    for node in all_image_nodes:
        groups[node.parent].append(node)

    image_nodes = max(groups.values(), key=len)
    leftmost = min(image_nodes, key=lambda n: abs_loc(n).x)
    leftmost_row = tuple(get_successors_simple([leftmost]))

    for image_node in image_nodes:
        row = tuple(get_successors_simple([image_node]))

        for node1, node2 in zip(leftmost_row, row):
            movement = abs_loc(node1).x - abs_loc(node2).x

            if link_stretch([node2], movement) != 0:
                break

            move(node2, x=movement)
            col1 = next(c for c in chain(*Maps.frame_columns.values()) if node1 in c)
            ranked = sorted(col1 + [node2], key=get_right, reverse=True)

            if ranked[0] != node2:
                continue

            right = get_right(node2)
            to_move = [n for n in chain(*Maps.universal_columns) if get_right(n) <= right]
            move_nodes(to_move + [node2], x=get_right(ranked[1]) - right)

        if any(n.bl_idname == 'ShaderNodeDisplacement' for n in row):
            move(image_node, y=-1)

    if frame := leftmost.parent:
        regenerate_columns(frame)


# -------------------------------------------------------------------
#   Move to linked Y
# -------------------------------------------------------------------


def get_real_sockets(socket):
    node = socket.node
    if node.bl_idname == 'NodeReroute':
        new_socket = node.inputs[0] if socket.is_output else node.outputs[0]
        for linked_socket in Maps.sockets[new_socket]:
            yield from get_real_sockets(linked_socket)
    else:
        yield socket


def get_linked_y_locs(node):
    y_locs = []
    is_reroute = node.bl_idname == 'NodeReroute'

    for socket in chain(node.inputs, node.outputs):
        if not socket.is_linked or socket.is_unavailable:
            continue

        if socket.is_output:
            get_socket_y = get_output_y
            get_linked_socket_y = get_input_y
        else:
            get_socket_y = get_input_y
            get_linked_socket_y = get_output_y

        socket_y = get_socket_y(socket, not is_reroute)
        for linked_socket in chain(*[get_real_sockets(s) for s in Maps.sockets[socket]]):
            linked_y = get_linked_socket_y(linked_socket, is_reroute)

            if linked_socket.node.bl_idname == 'NodeReroute':
                linked_y += abs_loc(node).y - socket_y

            y_locs.append((linked_socket.node, corrected_y(node, linked_y)))

    return y_locs


def move_frames_to_linked_y():
    for frame, children in Maps.used_children.items():
        if not frame:
            continue

        linked_y_locs = [
          y for c in children for n, y in get_linked_y_locs(c) if c.parent != n.parent]

        if not linked_y_locs:
            continue

        movement = fmean(linked_y_locs) - fmean([abs_loc(n).y for n in children])
        for node in children:
            move(node, y=movement)


def get_ideal_y(node, subrows, line_y):
    y = abs_loc(node).y
    parent = node.parent

    exclusive = node.bl_idname != 'NodeReroute' or parent
    y_locs = [y for n, y in get_linked_y_locs(node) if not exclusive or n.parent == parent]

    if not y_locs:
        return y

    rows = [r for r in subrows if node in r]
    if rows and node not in {rows[0][0], rows[0][-1]}:
        return y

    if not parent:
        return fmean(y_locs)

    height = y - get_bottom(node)
    return clamp(fmean(y_locs), line_y[0] + height, line_y[1])


def get_overlapping_lines(lines):
    keys = tuple(lines)
    margin = MARGIN.y / 2

    overlapping = {}
    for pair in combinations(lines, 2):
        # Sort pairs so that if its nodes overlap, the node that moved the
        # most is added
        most_moved, other = sorted(pair, key=keys.index)

        if lines_overlap(lines[most_moved], lines[other]):
            overlapping[most_moved] = other

            # If just the other node is moved, and there's still overlap,
            # add them both
            real_top = abs_loc(most_moved).y + margin
            real_bottom = get_bottom(most_moved) - margin
            if lines_overlap((real_top, real_bottom), lines[other]):
                overlapping[other] = most_moved

    return overlapping


def limited_disperse_nodes_y(ideal_y_locs):
    margin = MARGIN.y / 2

    lines = {}
    most_moved = lambda ny: abs(abs_loc(ny[0]).y - ny[1])
    for node, y in sorted(ideal_y_locs.items(), key=most_moved, reverse=True):
        lines[node] = [get_bottom(node, y) - margin, get_top(node, y) + margin]

    while overlapping := get_overlapping_lines(lines):
        for node in overlapping:
            lines[node] = [get_bottom(node) - margin, abs_loc(node).y + margin]

    for node, line in lines.items():
        move_to(node, y=corrected_y(node, line[1] - margin))


def move_to_linked_y(columns):
    nodes = tuple(chain(*columns))
    reroutes = {n for n in nodes if n.bl_idname == 'NodeReroute'}

    subrows = []
    for key, row in groupby(sorted(nodes, key=get_top), get_top):
        row = [n for n in row if n not in reroutes]
        row_len = len(row)

        if row_len < 3:
            continue

        curr_idx = 0
        for i, j in pairwise(range(row_len)):
            if abs_loc(row[j]).x - get_right(row[i]) > MARGIN.x:
                subrows.append(row[curr_idx:i + 1])
                curr_idx = j

        subrows.append(row[curr_idx:j + 1])

    line_y = get_box(nodes).line_y()

    for col in columns:
        ideal_y_locs = {n: get_ideal_y(n, subrows, line_y) for n in col if n not in reroutes}
        limited_disperse_nodes_y(ideal_y_locs)

    for col in columns:
        ideal_y_locs = {n: get_ideal_y(n, subrows, line_y) for n in col if n in reroutes}
        limited_disperse_nodes_y(ideal_y_locs)


# -------------------------------------------------------------------
#   Disperse Y
# -------------------------------------------------------------------


def get_overlapping_x(real_boxes, boxes):
    seen = set()
    overlapping_x = defaultdict(list)
    for a, box1 in real_boxes.items():
        for b, box2 in boxes.items():
            if {a, b} in seen or a == b:
                continue

            if lines_overlap(box1.line_x(), box2.line_x()) and not is_parented(a, b):
                overlapping_x[a].append(b)
                if b in real_boxes:
                    overlapping_x[b].append(a)

            seen.add(frozenset((a, b)))

    return overlapping_x


def rect_overlap_vector(key1, overlapping_x, boxes):
    box1 = boxes[key1]
    center1 = box1.center

    vec = Vector((0, 0))
    overlapping_keys = []

    for key2 in overlapping_x[key1]:
        if box1.overlaps(boxes[key2]):
            vec += boxes[key2].center - center1
            overlapping_keys.append(key2)

    if not overlapping_keys:
        return (vec.y, overlapping_keys)

    vec /= len(overlapping_keys)
    vec.negate()
    vec.normalize()

    return (vec.y * DISPERSE_MULT, overlapping_keys)


def get_merged_lines(lines):
    lines.sort(key=itemgetter(0))
    merged = [lines[0]]
    for current in lines[1:]:
        previous = merged[-1]
        if current[0] <= previous[1]:
            previous[1] = max(previous[1], current[1])
        else:
            merged.append(current)

    return merged


def get_better_movement(box, lines_y, movement):
    center = box.center.y
    height = box.height

    upper_line = (center, center + height)
    upper_overlap = max([l[0] - center for l in lines_y if lines_overlap(upper_line, l)],
      default=0)

    lower_line = (center - height, center)
    lower_overlap = min([center - l[1] for l in lines_y if lines_overlap(lower_line, l)],
      default=0)

    if movement > 0:
        diff = upper_overlap - lower_overlap
        better_movement = -DISPERSE_MULT
    else:
        diff = lower_overlap - upper_overlap
        better_movement = DISPERSE_MULT

    return better_movement if diff > height / 2 else movement


def dispersed(frame_boxes, col_boxes):

    # Most code here is to solve three issues that arise when dispersing
    # rectangles while also disallowing some from moving:
    #
    # 1. Since `col_boxes` can't move, frames can get trapped between them.
    #    To avoid this, if a frame has switched directions, its movement is
    #    set to its previous movement.
    #
    # 2. If frames affect each other, and move in the same direction, they
    #    unnecessarily drag each other down. To avoid this, only the frame
    #    furthest in the movement direction is allowed to move.
    #
    # 3. If two frames' vertical centers are equal, then they can't disperse.
    #    To avoid this, frames are manually dispersed.

    old_tops = {f: b.top for f, b in frame_boxes.items()}

    boxes = frame_boxes | col_boxes
    overlapping_x = get_overlapping_x(frame_boxes, boxes)
    pairs = [(boxes[k1], boxes[k2]) for k1, v in overlapping_x.items() for k2 in v]

    prev_movements = {}
    frozen_competition = {}

    while any(b1.overlaps(b2) for b1, b2 in pairs):
        for frame1, box1 in frame_boxes.items():
            if frame1 in frozen_competition:
                if box1.overlaps(frozen_competition[frame1]):
                    continue
                else:
                    del frozen_competition[frame1]

            movement, overlapping_keys = rect_overlap_vector(frame1, overlapping_x, boxes)

            if not overlapping_keys:
                if frame1 in prev_movements:
                    del prev_movements[frame1]

                continue

            overlapping_frames = [k for k in overlapping_keys if k in frame_boxes]

            if round(movement, 1) == 0:
                nudge = DISPERSE_MULT
                if frame1 in prev_movements and prev_movements[frame1] < 0:
                    nudge *= -1

                box1.move(y=nudge)
                if overlapping_frames:
                    frame_boxes[overlapping_frames[0]].move(y=-nudge)

            competing = [
              f for f in overlapping_frames
              if f in prev_movements and (prev_movements[f] > 0) == (movement > 0)]
            if competing:
                competing.append(frame1)
                if movement > 0:
                    favoured = max(competing, key=lambda f: frame_boxes[f].bottom)
                else:
                    favoured = min(competing, key=lambda f: frame_boxes[f].top)

                competing.remove(favoured)
                for frame2 in competing:
                    if favoured not in frozen_competition:
                        frozen_competition[frame2] = frame_boxes[favoured]

                if frame1 in frozen_competition:
                    continue

            lines_y = [boxes[k].line_y() for k in overlapping_x[frame1]]
            movement = get_better_movement(box1, get_merged_lines(lines_y), movement)

            if frame1 in prev_movements and (prev_movements[frame1] > 0) != (movement > 0):
                movement = prev_movements[frame1]

            box1.move(y=movement)
            if round(movement, 1) != 0:
                prev_movements[frame1] = movement

    return {f: t - boxes[f].top for f, t in old_tops.items()}


# -------------------------------------------------------------------
#   Align discrete rows
# -------------------------------------------------------------------


def get_discrete_predecessors(node):
    if len(get_output_nodes(node)) > 1:
        return

    if node.bl_idname != 'NodeReroute':
        yield node

    from_nodes = get_input_nodes(node)
    linked_singly = len(from_nodes) == 1 and len(get_output_nodes(node)) == 1
    if linked_singly and from_nodes[0].parent == node.parent:
        yield from get_discrete_predecessors(from_nodes[0])


def get_discrete_rows(columns):
    rows = []
    for col in columns[:-1]:
        for node in col:
            if node in chain(*rows):
                continue

            row = list(get_discrete_predecessors(node))
            valid = len(row) > 2 or (len(row) == 2 and not row[-1].inputs)
            if valid and len({get_top(n) for n in row}) != 1:
                row.reverse()
                rows.append(row)

    return rows


def disperse_row_box(sub_boxes, col_boxes):
    bottom = min([b.bottom for b in sub_boxes])
    row_box = Box(sub_boxes[0].left, bottom, sub_boxes[-1].right, sub_boxes[0].top)

    prev_movement = 0
    while any(a.overlaps(b) for a in sub_boxes for b in col_boxes.values()):
        raw_movement = rect_overlap_vector(0, {0: col_boxes}, col_boxes | {0: row_box})[0]
        lines_y = get_merged_lines([b.line_y() for b in col_boxes.values()])
        movement = get_better_movement(row_box, lines_y, raw_movement)

        if prev_movement and (prev_movement > 0) != (movement > 0):
            movement = prev_movement
        else:
            prev_movement = movement

        for box in row_box, *sub_boxes:
            box.move(y=movement)


def align_row(row, rows):
    linked = get_input_nodes(row[0]) + get_output_nodes(row[-1])
    ideal_y = fmean(map(get_top, linked))

    sub_boxes = []
    for node in row:
        box = Box(abs_loc(node).x, get_bottom(node, ideal_y), get_right(node), ideal_y)
        box.expand(y=MARGIN.y / 2)
        sub_boxes.append(box)

    columns = []
    unfixed = set(chain(*rows[rows.index(row):]))
    for col in Maps.frame_columns[row[0].parent]:
        if any(n in col for n in row) and (new_col := [n for n in col if n not in unfixed]):
            columns.append(new_col)

    disperse_row_box(sub_boxes, get_col_boxes(columns))
    y = sub_boxes[0].top - MARGIN.y / 2
    for node in row:
        move_to(node, y=corrected_y(node, y))


def align_discrete_rows(frame):
    rows = get_discrete_rows(Maps.frame_columns[frame])
    for row in rows:
        align_row(row, rows)


# -------------------------------------------------------------------
#   Compact frames X
# -------------------------------------------------------------------


def get_line_overlap(line1, line2):
    bottoms, tops = zip(line1, line2)
    return -max(bottoms) + min(tops)


def saves_space(box1, box2, boxes):

    # If the height of the boxes within the overlap range is >=
    # `COMPACT_HEIGHT` (around three math nodes) + margin * 2, then compact
    # the frame. (This is a heuristic meant to approximate how much space
    # would be saved after dispersing the frames.)

    center2 = box2.center.y
    upper_overlap = get_line_overlap(box1.line_y(), (center2, box2.top))
    lower_overlap = get_line_overlap(box1.line_y(), (box2.bottom, center2))

    height = 0
    if upper_overlap > lower_overlap:
        condition = lambda b: b.bottom < box1.top
    else:
        condition = lambda b: b.top > box1.bottom

    y_locs = []
    for key3, box3 in boxes.items():
        if lines_overlap((box1.right, box2.left), box3.line_x()) and condition(box3):
            if isinstance(key3, NodeFrame):
                height += box3.height
            else:
                y_locs.extend(box3.line_y())

    if y_locs:
        height += max(y_locs) - min(y_locs)

    return height > COMPACT_HEIGHT + MARGIN.y * 2


def get_overlapping(to_move, boxes, key1, op):
    box1 = boxes[key1]
    frames_to_move = {n.parent for n in to_move}
    overlapping = []
    for key2, box2 in boxes.items():
        if op(box1.left, box2.left):
            continue

        if isinstance(key2, NodeFrame):
            valid = key2 in frames_to_move and not is_parented(key1, key2)
        else:
            valid = to_move.intersection(key2)

        if valid and box1.overlaps(box2) and saves_space(box1, box2, boxes):
            overlapping.append(key2)

    return overlapping


def add_children(nodes):
    for frame in {n.parent for n in nodes}:
        if frame:
            nodes.update(Maps.used_children[frame])


def update_boxes_by_nodes(nodes, boxes, movement):
    moved = set()
    for node in nodes:
        if frame := node.parent:
            if frame not in moved:
                boxes[frame].move(x=movement)
                moved.add(frame)
        elif node not in moved:
            try:
                key = next(k for k in boxes if isinstance(k, tuple) and node in k)
            except StopIteration:
                continue

            boxes[key].move(x=movement)
            moved.update(key)


def compact_frames_x(frame_boxes, col_boxes):
    boxes = sorted_boxes(frame_boxes | col_boxes)
    children = Maps.used_children

    for frame1, box1 in frame_boxes.items():
        nodes_right = Maps.frame_successors[frame1].copy()
        add_children(nodes_right)

        children1 = get_nested_children(frame1)
        center1 = box1.center.x

        nodes_left = set(chain(*children.values())) - nodes_right.union(children1)
        for frame2, box2 in frame_boxes.items():
            if box1.left == box2.left:
                nodes_left.difference_update(children[frame2])

        add_children(nodes_left)

        # -------------------------------------------------------------------

        for key2 in get_overlapping(nodes_right, boxes, frame1, gt):
            box2 = boxes[key2]

            if key2 in frame_boxes:
                if link_stretch(children1, center1 - box2.center.x) <= link_stretch(children1):
                    continue

            movement = box1.right - box2.left
            if link_stretch(nodes_right, movement) <= link_stretch(nodes_right):
                move_nodes(nodes_right, x=movement)
                update_boxes_by_nodes(nodes_right, boxes, movement)
                break

        # -------------------------------------------------------------------

        for key2 in get_overlapping(nodes_left, boxes, frame1, lt):
            box2 = boxes[key2]

            if key2 in frame_boxes:
                children2 = children[key2]
                if link_stretch(children2, box2.center.x - center1) <= link_stretch(children2):
                    continue

            movement = -box2.right + box1.left
            if link_stretch(nodes_left, movement) <= link_stretch(nodes_left):
                move_nodes(nodes_left, x=movement)
                update_boxes_by_nodes(nodes_left, boxes, movement)
                break


# -------------------------------------------------------------------
#   Center frames X
# -------------------------------------------------------------------


def space_to_move(frame):
    children = Maps.used_children[frame]
    lengths = chain(get_input_lengths(children).values(), get_output_lengths(children).values())
    return min(lengths, default=0)


def center_frames_x(frame_boxes):
    others = {f1: [f2 for f2 in frame_boxes if f1 != f2] for f1 in frame_boxes}

    def dist_to_x(frame):
        return abs(center2 - frame_boxes[frame].center.x)

    while True:
        has_moved = False
        for frame1 in sorted(frame_boxes, key=space_to_move):
            box1 = frame_boxes[frame1]
            center1 = box1.center.x

            for frame2 in others[frame1]:
                box2 = frame_boxes[frame2]
                center2 = box2.center.x

                if min(others[frame2], key=dist_to_x) != frame1:
                    continue

                movement = center1 - center2

                no_movement = round(movement, 1) == 0
                children = Maps.used_children[frame2]
                if no_movement or link_stretch(children) < link_stretch(children, movement):
                    continue

                centered = {f for f, b in frame_boxes.items() if int(b.center.x) == int(center1)}

                moved_box2 = replace(box2)
                moved_box2.move(x=movement)

                for frame3 in others[frame2]:
                    if frame3 in centered:
                        continue

                    box3 = frame_boxes[frame3]
                    if box2.overlaps(box3) != moved_box2.overlaps(box3):
                        break
                else:
                    move(frame2, x=movement)
                    frame_boxes[frame2] = moved_box2
                    has_moved = True

        if not has_moved:
            break


# -------------------------------------------------------------------
#   Unite box rows
# -------------------------------------------------------------------


def unite(row, boxes):
    if len(row) < 3:
        return

    for key in row:
        rightwards = boxes[key].rightwards(boxes)

        if rightwards is None or rightwards in row or isinstance(rightwards, tuple):
            continue

        box = boxes[rightwards]

        if box.rightwards(boxes) not in row:
            continue

        if any(box.overlaps(b) for b in boxes.values() if box != b):
            continue

        movement = boxes[key].top - box.top

        if isinstance(rightwards, tuple):
            for node in rightwards:
                move(node, y=movement)
        else:
            move(rightwards, y=movement)

        box.move(y=movement)


def unite_box_rows(frame_boxes, col_boxes):
    boxes = sorted_boxes(frame_boxes | col_boxes)
    for row in get_box_rows(boxes):
        unite(row, boxes)


# -------------------------------------------------------------------
#   Center and disperse frames Y
# -------------------------------------------------------------------


def get_nested_boxes(frame_boxes):
    for frame in frame_boxes:
        nested_frame_boxes = {f: b for f, b in frame_boxes.items() if f.parent == frame}

        if not nested_frame_boxes:
            continue

        nested_col_boxes = get_col_boxes(Maps.frame_columns[frame])
        yield (nested_frame_boxes, nested_col_boxes)

        yield from get_nested_boxes(nested_frame_boxes)


def disperse_frames(frame_boxes, col_boxes):
    movements = dispersed(frame_boxes, col_boxes)
    for frame, movement in movements.items():
        move(frame, y=-movement)


def center_frames_y(frame_boxes, nearest):
    frame_boxes = dict(reversed(frame_boxes.items()))

    x_locs = [abs_loc(c[0][0]).x for c in Maps.frame_columns.values()]
    ntree_span = max(x_locs) - min(x_locs)

    rows = []
    for frame1, box1 in frame_boxes.items():
        seen = set(chain(*rows))

        if frame1 in seen:
            continue

        row = [frame1]
        for frame2, box2 in frame_boxes.items():
            if frame2 in seen or frame1 == frame2 or frame1.parent != frame2.parent:
                continue

            if not lines_overlap(box1.line_y(), box2.line_y()):
                continue

            height1 = box1.height

            if box2.bottom > box1.bottom + height1 / 2:
                continue

            if frame2 not in nearest[row[-1]] and abs(box2.height - height1) > height1 / 2:
                continue

            movement = box1.center.y - box2.center.y

            if movement == 0:
                continue

            prev_left, prev_right = frame_boxes[row[-1]].line_x()
            curr_left, curr_right = box2.line_x()

            if prev_left > curr_left or curr_right < prev_right:
                break

            if prev_right * -2 + prev_left - curr_right + curr_left * 2 > ntree_span / 4:
                break

            move(frame2, y=movement)
            box2.move(y=movement)

            row.append(frame2)

        rows.append(row)

    return rows


def will_break_box_row(frame, row, boxes, line_x):
    row = [k for k in row if k == frame or not lines_overlap(line_x, boxes[k].line_x())]
    i = row.index(frame)
    leftwards = row[(i - MIN_ADJ_COLS):(i)]
    rightwards = row[(i + 1):(i + MIN_ADJ_COLS + 1)]
    return any(#
      isinstance(a, tuple) and isinstance(b, tuple)
      for a, b in pairwise(leftwards + rightwards))


def get_levelled_frames(row_items, boxes, movement):
    levelled = set()
    for frame, (overlapping_x, row) in row_items.items():
        box = replace(boxes[frame])
        box.move(y=-movement)

        will_overlap = any(box.overlaps(b) for b in overlapping_x)
        if will_overlap or abs(movement) > box.height / 2:
            continue

        if movement == 0 or not will_break_box_row(frame, row, boxes, box.line_x()):
            levelled.add(frame)

    return levelled


def center_and_disperse_frames_y(frame_boxes, col_boxes):
    nested_boxes = tuple(get_nested_boxes(frame_boxes))
    for nested_frame_boxes, nested_col_boxes in reversed(nested_boxes):
        disperse_frames(nested_frame_boxes, nested_col_boxes)
        parent = next(iter(nested_frame_boxes)).parent
        frame_boxes[parent] = get_frame_box(parent)

    boxes = sorted_boxes(frame_boxes | col_boxes)

    nearest = defaultdict(set)
    for frame1, box1 in frame_boxes.items():
        if rightwards := box1.rightwards(boxes):
            nearest[frame1].add(rightwards)

        if leftwards := box1.leftwards(boxes):
            nearest[frame1].add(leftwards)

    old_values = {f: (f.location.y, replace(b)) for f, b in frame_boxes.items()}
    frame_rows = center_frames_y(frame_boxes, nearest)

    dispersed_boxes = {f: replace(b) for f, b in frame_boxes.items()}
    movements = dispersed(dispersed_boxes, col_boxes)
    dispersed_boxes.update(col_boxes)

    overlapping_x = get_overlapping_x(frame_boxes, boxes)
    rows = get_box_rows(boxes)
    row_map = {f: next(r for r in rows if f in r) for f in frame_boxes}

    for row in frame_rows:
        row_items = {f: ([dispersed_boxes[k] for k in overlapping_x[f]], row_map[f]) for f in row}
        results = {}
        for frame in row:
            movement = movements[frame]
            results[movement] = get_levelled_frames(row_items, boxes, movement)

        counts = {m: sum(len(nearest[f] & l) + 1 for f in l) for m, l in results.items()}
        largest = max(counts.values())

        if largest < 2:
            for frame in row:
                old_y, old_box = old_values[frame]
                move(frame, y=old_y - frame.location.y)
                frame_boxes[frame] = old_box

            continue

        best_movement = min([m for m, l in counts.items() if l == largest], key=abs)
        levelled = results[best_movement]
        for frame in row:
            movement = best_movement if frame in levelled else movements[frame]
            move(frame, y=-movement)
            frame_boxes[frame].move(y=-movement)

    disperse_frames(frame_boxes, col_boxes)


# -------------------------------------------------------------------
#   Contract X
# -------------------------------------------------------------------


def get_beyond(box1, boxes):
    beyond = []
    distances = []
    for key2, box2 in boxes.items():
        is_nested = isinstance(key2, NodeFrame) and key2.parent
        if is_nested or box2.left <= box1.left or box2.right <= box1.right:
            continue

        if isinstance(key2, tuple):
            beyond.extend(key2)
        else:
            beyond.append(key2)

        distances.append(box2.left - box1.right)

    return beyond, distances


def has_closer(box1, boxes, movement):
    for box2 in boxes.values():
        if box2.left == box1.left and any(d < movement for d in get_beyond(box2, boxes)[1]):
            return True


def contract_x(frame_boxes, col_boxes):
    active_unframed = set(Maps.used_children.get(None, []))
    reroutes = active_unframed.difference(chain(*col_boxes))
    all_col_boxes = {tuple([r]): get_box([r]) for r in reroutes} | col_boxes
    boxes = sorted_boxes(frame_boxes | all_col_boxes)

    values = tuple(boxes.values())
    nodes = set(frame_boxes).union(chain(*all_col_boxes))

    prev_right1 = None
    for box1 in boxes.values():
        if prev_right1 is not None and prev_right1 >= box1.right:
            continue

        beyond, distances = get_beyond(box1, boxes)
        movement = min(distances, default=0)
        prev_right1 = box1.right

        if movement <= 0 or has_closer(box1, boxes, movement):
            continue

        # Optimization: minimize location updates
        total_center = (values[0].left + values[-1].right) / 2
        if box1.center.x - total_center < 0:
            beyond = nodes.difference(beyond)
            movement *= -1

        affected_keys = set()
        for node in beyond:
            move(node, x=-movement)
            if node in frame_boxes:
                affected_keys.add(node)
            else:
                affected_keys.add(next(k for k in all_col_boxes if node in k))

        for affected in affected_keys:
            boxes[affected].move(x=-movement)

        prev_right1 = box1.right


# -------------------------------------------------------------------
#   Arrange reroutes
# -------------------------------------------------------------------


def reroute_predecessors(node, reroutes, seen):
    if node not in reroutes:
        return

    yield node

    if node in seen:
        return

    linked = Maps.links[node.inputs[0]][0]
    yield from reroute_predecessors(linked, reroutes, seen)


def get_reroute_segments(children):
    reroutes = [#
      n for n in children
      if n.bl_idname == 'NodeReroute'
      and (Maps.links[n.inputs[0]] and Maps.links[n.outputs[0]])]

    segments = []
    for reroute in reroutes:
        seen = set(chain(*segments))
        if pred := tuple(reroute_predecessors(reroute, reroutes, seen)):
            segments.append(pred)

    segments.sort(key=len)
    for s1 in reversed(segments):
        for i, s2 in enumerate(segments):
            if s1 != s2:
                segments[i] = [n for n in s2 if n not in s1]

    segments = [tuple(reversed(s)) for s in segments if s]
    segments.sort(key=lambda s: abs_loc(s[0]).x)

    return segments


def arrange_framed_reroutes(segment, children):
    sockets = Maps.sockets

    end = segment[-1]
    linked = sockets[end.outputs[0]]
    to_socket = linked[0]
    if to_socket.node in children:
        move_to(end, y=get_input_y(to_socket))
        x = abs_loc(to_socket.node).x - MARGIN.x
        if link_stretch([end]) >= link_stretch([end], x - abs_loc(end).x):
            move_to(end, x=x)
    else:
        move_to(end, y=get_output_y(sockets[end.inputs[0]][0]))

    segment_rest = segment[:-1]

    if not segment_rest:
        return

    from_socket = sockets[segment[0].inputs[0]][0]
    if from_socket.node in children:
        output_y = get_output_y(from_socket)
        movement = abs_loc(segment_rest[0]).x - (get_right(from_socket.node) + MARGIN.x)
        for reroute in segment_rest:
            move(reroute, x=-movement)
    elif len(linked) == 1:
        output_y = get_input_y(linked[0])
    else:
        output_y = abs_loc(end).y

    for reroute in segment_rest:
        move_to(reroute, y=output_y)


def get_movement_x(reroute, box, boxes, movement):
    copied = replace(box)
    total_movement = 0
    while any(copied.overlaps(b) for b in boxes):
        total_movement += movement
        if link_stretch([reroute], total_movement):
            break

        copied.move(x=movement)
    else:
        return total_movement

    return None


def disperse_reroute_x(reroute, boxes):
    box = get_box([reroute])
    right = get_movement_x(reroute, box, boxes, 1)

    if right == 0:
        return

    left = get_movement_x(reroute, box, boxes, -1)

    if right is None and left is None:
        return

    if right is None:
        move(reroute, x=left)
    elif left is None:
        move(reroute, x=right)
    else:
        move(reroute, x=min(right, left, key=abs))


def disperse_reroutes_x(segments, boxes=None):
    try:
        reroute = segments[0][0]
    except IndexError:
        return

    if boxes is None:
        boxes = []

    margin = MARGIN / 2 - reroute.dimensions / 4
    for node in Maps.used_children[reroute.parent]:
        if node.bl_idname != 'NodeReroute':
            box = get_box([node])
            box.expand(*margin)
            boxes.append(box)

    for segm in segments:
        for reroute in reversed(segm):
            disperse_reroute_x(reroute, boxes)


def arrange_all_framed_reroutes(frame_boxes):
    while True:
        has_moved = False
        for frame, children in Maps.used_children.items():
            if not frame or len(children) == 1:
                continue

            segments = get_reroute_segments(children)

            if not segments:
                continue

            reroutes = tuple(chain(*segments))
            old_locs = [abs_loc(r) for r in reroutes]

            for segm in segments:
                arrange_framed_reroutes(segm, children)

            disperse_reroutes_x(segments)

            bottom, top = frame_boxes[frame].line_y()
            for reroute, old_loc in zip(reroutes, old_locs):
                loc = abs_loc(reroute)
                if loc.y > top or loc.y < bottom:
                    move_to(reroute, y=old_loc.y)
                elif any([round(a, 1) != 0 for a in loc - old_loc]):
                    has_moved = True

        if not has_moved:
            return


def arrange_unframed_reroutes(segment):
    output_y = get_output_y(Maps.sockets[segment[0].inputs[0]][0])
    for reroute in segment:
        move_to(reroute, y=output_y)

    if len(segment) == 1:
        return

    end = segment[-1]
    to_socket = Maps.sockets[end.outputs[0]][0]
    move_to(end, y=get_input_y(to_socket))

    x = abs_loc(to_socket.node).x - MARGIN.x
    if link_stretch([end]) >= link_stretch([end], x - end.location.x):
        move_to(end, x=x)


# -------------------------------------------------------------------
#   Move unused
# -------------------------------------------------------------------


def get_unused(frame):
    active_nodes = set(chain(*Maps.universal_columns))
    unused = []
    for node in Maps.all_children[frame]:
        if not node.select or node in Maps.used_children[frame]:
            continue

        if node.bl_idname == 'NodeFrame' and active_nodes.intersection(Maps.all_children[node]):
            continue

        unused.append(node)

    return unused


def move_framed_unused(frame):
    box = get_box(Maps.used_children[frame])
    for node in get_unused(frame):
        move_to(node, x=box.left, y=box.bottom + (get_top(node) - get_bottom(node)))


def get_unused_subtrees(unused):
    subtrees = []
    for node in unused:
        item = [node]
        for input in node.inputs:
            item.extend([n for n in Maps.links[input] if n in unused])

        subtrees.append(item)

    for node in unused:
        shared = [i for i in subtrees if node in i]

        for item in shared:
            subtrees.remove(item)

        subtrees.append(set(chain(*shared)))

    return subtrees


def move_unframed_unused(offset, boxes):
    unused = get_unused(None)

    for node in unused:
        move(node, x=offset.x, y=offset.y)

    subtree_boxes = {tuple(s): get_box(s) for s in get_unused_subtrees(unused)}
    for box in subtree_boxes.values():
        box.expand(*MARGIN / 2)

    indexed_boxes = {i: b for i, b in enumerate(boxes.values())}
    movements = dispersed(subtree_boxes, indexed_boxes)
    for subtree, movement in movements.items():
        for node in subtree:
            move(node, y=-movement)


# -------------------------------------------------------------------
#   Maps
# -------------------------------------------------------------------


def clear_bl_data_references():
    for key, val in vars(Maps).items():
        if not key.startswith('_'):
            val.clear()


class Maps:
    selected = []
    links = defaultdict(list)
    sockets = defaultdict(list)

    universal_columns = []
    all_children = defaultdict(list)

    frame_columns = {}
    used_children = {}
    frame_successors = {}


# -------------------------------------------------------------------


class NA_OT_ArrangeSelected(Operator):
    bl_idname = "node.na_arrange_selected"
    bl_label = "Arrange Selected"
    bl_description = "Arrange selected nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ntree = context.space_data.edit_tree
        nodes = ntree.nodes
        selected = [n for n in nodes if n.select]

        if not selected:
            self.report({'WARNING'}, "No nodes selected")
            return {'CANCELLED'}

        if all(n.bl_idname == 'NodeFrame' for n in selected):
            self.report({'WARNING'}, "No valid nodes selected")
            return {'CANCELLED'}

        output_nodes = [n for n in nodes if not n.outputs and any(i.is_linked for i in n.inputs)]

        if not output_nodes:
            self.report({'WARNING'}, "No output node")
            return {'CANCELLED'}

        # -------------------------------------------------------------------

        get_links(ntree)
        universal_columns = get_columns(output_nodes)

        if not universal_columns:
            self.report({'WARNING'}, "No valid nodes selected")
            return {'CANCELLED'}

        Maps.universal_columns.extend(universal_columns)
        Maps.selected.extend(selected)

        active_nodes = tuple(chain(*universal_columns))
        for socket, linked in Maps.links.items():
            indices = [i for i, n in enumerate(linked) if n not in active_nodes]
            for i in reversed(indices):
                del linked[i]
                del Maps.sockets[socket][i]

        # -------------------------------------------------------------------

        settings = context.scene.na_settings

        global MARGIN
        MARGIN = Vector(settings.margin).freeze()

        for node in nodes:
            Maps.all_children[node.parent].append(node)

        locs = [(n, abs_loc(n)) for n in active_nodes]
        origin_node, old_origin_loc = max(locs, key=lambda nl: sum(nl[1]))

        # -----------------------------------------------------------------

        get_frame_columns()
        frame_columns = Maps.frame_columns

        arrange_frame_columns()
        move_frames_to_linked_y()

        # -------------------------------------------------------------------

        for frame in frame_columns:
            make_space_for_stretched(frame)

        arrange_principled()

        if None in frame_columns:
            regenerate_columns(None)

        for frame, columns in frame_columns.items():
            move_to_linked_y(columns)
            move_to_linked_y(columns)

        for frame in frame_columns:
            align_discrete_rows(frame)

        # -------------------------------------------------------------------

        frame_boxes = {f: get_frame_box(f) for f in frame_columns if f}
        col_boxes = get_col_boxes(frame_columns.get(None, []))

        compact_frames_x(frame_boxes, col_boxes)
        center_frames_x(frame_boxes)

        unite_box_rows(frame_boxes, col_boxes)
        center_and_disperse_frames_y(frame_boxes, col_boxes)

        contract_x(frame_boxes, col_boxes)

        # -------------------------------------------------------------------

        arrange_all_framed_reroutes(frame_boxes)

        unframed_segments = get_reroute_segments(Maps.used_children.get(None, []))

        for segm in unframed_segments:
            arrange_unframed_reroutes(segm)

        disperse_reroutes_x(unframed_segments, list(frame_boxes.values()))

        # -------------------------------------------------------------------

        offset = abs_loc(origin_node) - old_origin_loc

        get_links(ntree)  # Get unused links
        for frame in Maps.used_children:
            if frame:
                move_framed_unused(frame)
            else:
                move_unframed_unused(offset, frame_boxes | col_boxes)

        x, y = -offset
        move_nodes(selected, x=x, y=y)

        # -------------------------------------------------------------------

        clear_bl_data_references()

        return {'FINISHED'}


classes = [NA_OT_ArrangeSelected]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        if cls.is_registered:
            bpy.utils.unregister_class(cls)
