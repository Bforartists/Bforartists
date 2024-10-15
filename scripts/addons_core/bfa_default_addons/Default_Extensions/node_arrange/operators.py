# SPDX-License-Identifier: GPL-2.0-or-later

from collections.abc import (
  Callable,
  Collection,
  Hashable,
  Iterable,
  Iterator,
  MutableSequence,
  Sequence,
)
from collections import defaultdict
from dataclasses import dataclass, field, replace
from functools import cmp_to_key
from itertools import chain, combinations, pairwise
from operator import gt, itemgetter, lt
from statistics import fmean
from typing import Any, TypeVar

import bpy
from bpy.types import Context, Node, NodeFrame, NodeReroute, NodeSocket, NodeTree, Operator
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
OVERLAP_TOL = 0.01
FRAME_PADDING = 29.8
EPS = 65
TARGET_NODE_TYPES = {'ShaderNodeBsdfPrincipled', 'ShaderNodeDisplacement'}
DISPERSE_MULT = 4
INF_BEYOND = 10**10
ITER_LIMIT_MULT = 1000
COMPACT_HEIGHT = 450
MIN_ADJ_COLS = 2

_T1 = TypeVar('_T1', bound=Hashable)
_T2 = TypeVar('_T2', bound=Hashable)

# -------------------------------------------------------------------
#   Parents and children
# -------------------------------------------------------------------


def get_parents(node: Node) -> Iterator[NodeFrame]:
    if parent := node.parent:
        yield parent
        yield from get_parents(parent)


def get_nested_children(frame: NodeFrame | None) -> Iterator[Node]:
    try:
        yield from Maps.used_children[frame]
    except KeyError:
        return

    for node in Maps.selected:
        if node.bl_idname == 'NodeFrame' and node.parent == frame:
            yield from get_nested_children(node)


def is_parented(a: Any, b: Any) -> bool:
    if not isinstance(a, NodeFrame) or not isinstance(b, NodeFrame):
        return False

    return b in get_parents(a) or a in get_parents(b)


# -------------------------------------------------------------------
#   Flatten links
# -------------------------------------------------------------------


def get_predecessors(*nodes: Node) -> list[Node]:
    predecessors = []
    for node in nodes:
        predecessors.extend(chain(*[Maps.links[i] for i in node.inputs]))

    return predecessors


def get_successors(*nodes: Node) -> list[Node]:
    successors = []
    for node in nodes:
        successors.extend(chain(*[Maps.links[o] for o in node.outputs]))

    return successors


def get_ancestors(nodes: Iterable[Node], seen: set[Node] | None = None) -> Iterator[Node]:
    if seen is None:
        seen = set()

    for node in nodes:
        if node in seen:
            continue

        yield node
        seen.add(node)

        for input in node.inputs:
            yield from get_ancestors(Maps.links[input], seen)


def get_descendants(nodes: Iterable[Node], seen: set[Node] | None = None) -> Iterator[Node]:
    if seen is None:
        seen = set()

    for node in nodes:
        if node in seen:
            continue

        yield node
        seen.add(node)

        queue = set(get_successors(node))
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

        yield from get_descendants(queue, seen)


def get_real_sockets(socket: NodeSocket) -> Iterator[NodeSocket]:
    node = socket.node
    if node.bl_idname == 'NodeReroute':
        new_socket = node.inputs[0] if socket.is_output else node.outputs[0]
        for linked_socket in Maps.sockets[new_socket]:
            yield from get_real_sockets(linked_socket)
    else:
        yield socket


# -------------------------------------------------------------------
#   Locations
# -------------------------------------------------------------------


def abs_loc(node: Node) -> Vector:
    loc = node.location.copy()
    for parent in get_parents(node):
        loc += parent.location

    return loc


def dimensions(node: Node) -> Vector:
    return node.dimensions / SCALE_FAC if node.bl_idname != 'NodeReroute' else node.dimensions / 2


def get_right(node: Node) -> float:
    return abs_loc(node).x + dimensions(node).x


def get_top(node: Node, y_loc: float | None = None) -> float:
    if y_loc is None:
        y_loc = abs_loc(node).y

    return (y_loc + dimensions(node).y / 2) - HIDE_OFFSET if node.hide else y_loc


def get_bottom(node: Node, y_loc: float | None = None) -> float:
    if y_loc is None:
        y_loc = abs_loc(node).y

    dim_y = dimensions(node).y
    bottom = y_loc - dim_y
    return bottom + dim_y / 2 - HIDE_OFFSET if node.hide else bottom


def get_hidden_socket_y(socket: NodeSocket) -> float:
    node = socket.node
    x, y = abs_loc(node)

    top = get_top(node, y)
    bottom = get_bottom(node, y)

    cap_width = (dimensions(node).x - HIDDEN_NODE_FLAT_WIDTH) / 2
    inner = x + cap_width
    outer = x - cap_width / 3

    raw_sockets = node.outputs if socket.is_output else node.inputs
    sockets = [s for s in raw_sockets if not s.is_unavailable]

    vectors = map(Vector, ((inner, top), (outer, top), (inner, bottom), (outer, bottom)))
    points = interpolate_bezier(*vectors, len(sockets) + 2)[1:-1]

    return points[sockets.index(socket)].y


def get_input_y(input: NodeSocket, accurate: bool = True) -> float:
    node = input.node

    if not accurate or node.bl_idname == 'NodeReroute':
        return get_top(node)

    if node.hide:
        return get_hidden_socket_y(input)

    y = get_top(node)

    inputs = [i for i in node.inputs if not i.is_unavailable]
    if node.bl_idname != 'ShaderNodeBsdfPrincipled':
        # Start from the bottom socket to avoid any node properties
        y -= dimensions(node).y - BOTTOM_OFFSET
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


def get_output_y(output: NodeSocket, accurate: bool = True) -> float:
    node = output.node

    if not accurate or node.bl_idname == 'NodeReroute':
        return get_top(node)

    if node.hide:
        return get_hidden_socket_y(output)

    y = get_top(node) - TOP_OFFSET
    outputs = [o for o in node.outputs if not o.is_unavailable]
    return y - outputs.index(output) * SOCKET_SPACING_MULTIPLIER


def get_socket_y(socket: NodeSocket, accurate: bool = True) -> float:
    return get_output_y(socket, accurate) if socket.is_output else get_input_y(socket, accurate)


def corrected_y(node: Node, target_y: float) -> float:
    y = abs_loc(node).y
    return target_y + (y - get_top(node)) if y != target_y else y


# -------------------------------------------------------------------
#   Lines
# -------------------------------------------------------------------


@dataclass(slots=True)
class Line:
    a: float
    b: float

    def __post_init__(self) -> None:
        if self.a > self.b:
            raise ValueError(f"'Line' attribute 'a' is greater than 'b': ({self.a}, {self.b})")

    def __iter__(self) -> Iterator[float]:
        yield from (self.a, self.b)

    @property
    def length(self) -> float:
        return self.b - self.a

    @property
    def center(self) -> float:
        return sum(self) / 2

    def expand(self, val: float) -> None:
        self.a -= val
        self.b += val

    def move(self, val: float) -> None:
        self.a += val
        self.b += val

    def overlaps(self, other: 'Line', tol: float = OVERLAP_TOL) -> bool:
        a1, b1 = self
        a2, b2 = other

        a1 += tol
        b1 -= tol
        a2 += tol
        b2 -= tol

        # yapf: disable
        return (
          (a1 <= b2 <= b1)
          or (a1 <= a2 <= b1)
          or (b2 < b1 and a1 < a2)
          or (b1 < b2 and a2 < a1))
        # yapf: enable

    def get_overlap_movement(self, lines: Iterable['Line']) -> float:
        center = self.center
        y_vals = [l.center - center for l in lines if self is not l and self.overlaps(l)]

        if not y_vals:
            return 0

        return clamp(-fmean(y_vals), -1, 1) if any(y_vals) else 1

    def overlap_amount(self, other: 'Line') -> float:
        bottoms, tops = zip(self, other)
        val = -max(bottoms) + min(tops)
        return val if val >= 0 else 0


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
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def center(self) -> Vector:
        return Vector((self.left + self.right, self.bottom + self.top)) / 2

    @property
    def line_x(self) -> Line:
        return Line(self.left, self.right)

    @property
    def line_y(self) -> Line:
        return Line(self.bottom, self.top)

    def expand(self, x: float = 0, y: float = 0) -> None:
        self.left -= x
        self.right += x
        self.bottom -= y
        self.top += y

    def move(self, *, x: float = 0, y: float = 0) -> None:
        self.left += x
        self.right += x
        self.bottom += y
        self.top += y

    def overlaps(self, other: 'Box', tol=OVERLAP_TOL) -> bool:
        # yapf: disable
        return not (
          self.right - tol < other.left + tol
          or self.left + tol > other.right - tol
          or self.top - tol < other.bottom + tol
          or self.bottom + tol > other.top - tol)
        # yapf: enable

    def get_leftwards(self, boxes: dict[Hashable, 'Box']) -> Hashable | None:
        return next((k for k, b in reversed(boxes.items()) if b.right <= self.left), None)

    def get_rightwards(self, boxes: dict[Hashable, 'Box']) -> Hashable | None:
        return next((k for k, b in boxes.items() if b.left >= self.right), None)


def get_box(nodes: Iterable[Node]) -> Box:
    x_vals = []
    y_vals = []
    for node in nodes:
        x, y = abs_loc(node)
        x_vals.extend((x, x + dimensions(node).x))
        y_vals.extend((get_top(node, y), get_bottom(node, y)))

    return Box(min(x_vals), min(y_vals), max(x_vals), max(y_vals))


def get_frame_box(frame: NodeFrame, expand: bool = True) -> Box:

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


def get_col_boxes(columns: Iterable[Sequence[Node]]) -> dict[tuple[Node, ...], Box]:
    subcolumns = []
    for col in columns:
        if len(col) < 2:
            if col:
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


def sorted_boxes(boxes: dict[Hashable, Box]) -> dict[Hashable, Box]:
    return dict(sorted(boxes.items(), key=lambda kb: kb[1].left))


def get_box_rows(boxes: dict[Hashable, Box]) -> list[list[Hashable]]:
    tops = {k: b.top for k, b in boxes.items()}
    boxes_asc = sorted(boxes, key=tops.get)

    prev_key = boxes_asc[0]
    row = [prev_key]
    rows = []
    for key in boxes_asc[1:]:
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


# -------------------------------------------------------------------
#   Update locations
# -------------------------------------------------------------------


def move(node: Node, *, x: float = 0, y: float = 0) -> None:
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

    bpy.ops.transform.translate(value=[v * SCALE_FAC for v in (x, y, 0)])

    for n in Maps.selected:
        n.select = True


def move_to(node: Node, *, x: float | None = None, y: float | None = None) -> None:
    loc = abs_loc(node)
    if x is not None and y is None:
        move(node, x=x - loc.x)
    elif y is not None and x is None:
        move(node, y=y - loc.y)
    else:
        move(node, x=x - loc.x, y=y - loc.y)


def move_nodes(nodes: Iterable[Node], *, x: float = 0, y: float = 0) -> None:
    for node in {n.parent or n for n in nodes}:
        if node.bl_idname != 'NodeFrame' or not node.parent:
            move(node, x=x, y=y)


# -------------------------------------------------------------------
#   Generate maps
# -------------------------------------------------------------------


def get_links(ntree: NodeTree) -> None:
    # Precompute links to:
    # 1. Avoid `O(len(ntree.links))` time
    # 2. Ignore invalid/hidden links
    # 3. Ignore links to unused nodes
    # 4. Ignore links to/from unselected nodes

    links = Maps.links
    sockets = Maps.sockets

    for link in ntree.links:
        if link.is_hidden or not link.is_valid:
            continue

        links[link.to_socket].append(link.from_node)
        sockets[link.to_socket].append(link.from_socket)

        links[link.from_socket].append(link.to_node)
        sockets[link.from_socket].append(link.to_socket)


def get_columns(output_nodes: Collection[Node]) -> list[list[Node]]:
    columns = [output_nodes]
    idx = 0
    while columns[idx]:
        columns.append(tuple(dict.fromkeys(get_predecessors(*columns[idx]))))
        idx += 1

    del columns[idx]

    for col1 in reversed(columns):
        for i, col2 in enumerate(columns):
            if col1 != col2:
                columns[i] = [n for n in col2 if n not in col1]

    return [sc for uc in columns if (sc := [n for n in uc if n.select])]


def min_col_idx(item: Sequence[Any, Iterable[Collection[Node]]]) -> int:
    universal_columns = Maps.universal_columns
    idxs = []
    for col in item[1]:
        idxs.append(next(i for i, c in enumerate(universal_columns) if any(n in c for n in col)))

    return min(idxs)


def get_frame_columns() -> None:
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


def get_arranged(columns: Sequence[Sequence[Node]]) -> dict[Node, Vector]:
    arranged = {}
    for i, col in enumerate(columns):
        if i != 0:
            max_width = max([dimensions(n).x for n in col])
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


def arrange_frame_columns() -> None:
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


def link_stretch(nodes: Collection[Node], movement: float = 0) -> float:
    stretch = 0
    for node in nodes:
        x = abs_loc(node).x + movement
        right = x + dimensions(node).x
        for socket in chain(node.inputs, node.outputs):
            for linked in Maps.links[socket]:
                if linked in nodes:
                    continue

                dist = abs_loc(linked).x - right if socket.is_output else x - get_right(linked)
                if dist < 0:
                    stretch -= dist

    return stretch


def get_input_lengths(nodes: Collection[Node]) -> dict[Node, float]:
    lengths = {}
    for node in nodes:
        input_x = abs_loc(node).x
        for pred in get_predecessors(node):
            if pred in nodes:
                continue

            dist = input_x - get_right(pred)
            if pred not in lengths or lengths[pred] > dist:
                lengths[pred] = dist

    return lengths


def get_output_lengths(nodes: Collection[Node]) -> dict[Node, float]:
    lengths = {}
    for node in nodes:
        output_x = get_right(node)
        for succ in get_successors(node):
            if succ in nodes:
                continue

            dist = abs_loc(succ).x - output_x
            if succ not in lengths or lengths[succ] > dist:
                lengths[succ] = dist

    return lengths


# -------------------------------------------------------------------
#   Make space for stretched
# -------------------------------------------------------------------


def ideal_x_movement(nodes: Collection[Node], line_x: Iterable[float]) -> float:
    from_x = []
    to_x = []
    for node in nodes:
        input_x = abs_loc(node).x
        output_x = get_right(node)
        to_x.extend([(abs_loc(n).x, output_x) for n in get_successors(node) if n not in nodes])
        from_x.extend([(get_right(n), input_x) for n in get_predecessors(node) if n not in nodes])

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


def ideal_frame_x_movement(frame: NodeFrame) -> float:
    children = Maps.used_children[frame]
    return ideal_x_movement(children, get_box(children).line_x)


def resolved_with_min_movement(children: Sequence[Node]) -> bool:
    # Move the children's immediate successor rightwards, then move the
    # children's frame rightwards, and see if it's resolved.

    frame = children[0].parent
    pred, pred_dist = min(get_input_lengths(children).items(), key=itemgetter(1))
    succ, succ_dist = min(get_output_lengths(children).items(), key=itemgetter(1))

    if frame in chain(get_parents(succ), get_parents(pred)):
        return False

    if pred_dist < 0:
        pred_frame = pred.parent
        predecessors = Maps.used_children[pred_frame] if pred_frame else [pred]
        pred_movement = pred_dist - MARGIN.x * 2

        if link_stretch(predecessors, pred_movement):
            return False

    if succ_dist < 0:
        succ_frame = succ.parent
        succ_movement = abs(succ_dist) + MARGIN.x * 2
        if succ_frame:
            if link_stretch(Maps.used_children[succ_frame], succ_movement):
                return False

            move(succ_frame, x=succ_movement)
        else:
            if link_stretch([succ], succ_movement):
                return False

            move(succ, x=succ_movement)

    if pred_dist < 0:
        node = succ_frame if pred_frame and succ_frame else pred
        move(node, x=pred_movement)

    movement = ideal_frame_x_movement(frame)

    if link_stretch(children, movement):
        return False

    move(frame, x=movement)
    return True


def make_space_for_stretched(frame: NodeFrame | None) -> None:
    if not frame:
        return

    children = Maps.used_children[frame]

    to_move = set(get_descendants(get_successors(*children)))
    to_move -= set(get_ancestors(get_predecessors(*children))) | set(children)

    Maps.frame_descendants[frame] = to_move

    move(frame, x=ideal_frame_x_movement(frame))

    pred_stretch = []
    succ_stretch = []
    for node in children:
        pred_stretch.extend([d for d in get_input_lengths([node]).values() if d < 0])
        succ_stretch.extend([d for d in get_output_lengths([node]).values() if d < 0])

    movement = 0

    if pred_stretch:
        movement += abs(min(pred_stretch)) + MARGIN.x * 2

    if succ_stretch:
        movement += abs(min(succ_stretch)) + MARGIN.x * 2

    if movement != 0 and not resolved_with_min_movement(children):
        move_nodes(to_move, x=movement)
        move(frame, x=ideal_frame_x_movement(frame))


# -------------------------------------------------------------------
#   Regenerate columns
# -------------------------------------------------------------------


def move_outlier(node: Node) -> None:
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


def get_new_columns(frame: NodeFrame | None) -> list[list[Node]]:
    nodes_left_to_right = sorted(Maps.used_children[frame], key=lambda n: abs_loc(n).x)

    prev_node = nodes_left_to_right[0]
    col = [prev_node]
    columns = []
    for node in nodes_left_to_right[1:]:
        if abs_loc(node).x <= abs_loc(prev_node).x + EPS:
            col.append(node)
        else:
            columns.append(col)
            col = [node]

        prev_node = node

    columns.append(col)

    return columns


def get_aligned_columns(
  prev_col: Sequence[Node],
  curr_col: Sequence[Node],
  columns: Sequence[Sequence[Node]],
) -> None:
    x = abs_loc(curr_col[0]).x

    for node in curr_col:
        move_to(node, x=x)

    col = curr_col
    i = columns.index(curr_col)

    if prev_col and (movement := -x + get_right(prev_col[0]) + MARGIN.x) > 0:
        to_move = [f for f in Maps.frame_columns if f and get_frame_box(f, False).left > x]
        to_move.extend(chain(*columns[i:]))
        if link_stretch(to_move, movement) != 0:
            movement_to_prev = abs_loc(prev_col[0]).x - x
            if link_stretch(curr_col, movement_to_prev) == 0:
                col = prev_col + curr_col
                for node in curr_col:
                    move(node, x=movement_to_prev)
        else:
            move_nodes(to_move, x=movement)

    col.sort(key=lambda n: dimensions(n).x, reverse=True)
    yield col
    if columns[-1] != curr_col:
        yield from get_aligned_columns(col, columns[i + 1], columns)


def merge_columns(columns: list[Collection[Node]]) -> None:
    for node in dict.fromkeys(chain(*columns)):
        components = [c for c in columns if node in c]

        for col in components:
            columns.remove(col)

        columns.append(list(set(chain(*components))))


def disperse_nodes_y(col: Iterable[Node]) -> None:
    margin = MARGIN.y / 2

    lines = {n: Line(get_bottom(n), get_top(n)) for n in col if n.bl_idname != 'NodeReroute'}
    values = lines.values()

    for line in values:
        line.expand(margin)

    pairs = tuple(combinations(values, 2))
    while any(l1.overlaps(l2) for l1, l2 in pairs):
        for node, line in lines.items():
            movement = line.get_overlap_movement(values)
            line.move(movement)

    for node, line in lines.items():
        move_to(node, y=corrected_y(node, line.b - margin))


def contract_nodes_y(col: Iterable[Node]) -> None:
    for node1, node2 in pairwise(col):
        dist = get_bottom(node1) - get_top(node2)
        if dist > MARGIN.y:
            move(node2, y=dist - MARGIN.y)


def regenerate_columns(frame: NodeFrame | None) -> None:
    for node in Maps.used_children[frame]:
        move_outlier(node)

    new_columns = get_new_columns(frame)
    newer_columns = list(get_aligned_columns(None, new_columns[0], new_columns))
    merge_columns(newer_columns)

    for col in newer_columns:
        disperse_nodes_y(col)
        col.sort(key=get_top, reverse=True)
        contract_nodes_y(col)

    newer_columns.reverse()
    Maps.frame_columns[frame] = newer_columns


# -------------------------------------------------------------------
#   Arrange principled
# -------------------------------------------------------------------


def group_by(iterable: Iterable[_T1], key: Callable[[_T1], _T2]) -> dict[tuple[_T1, ...], _T2]:
    groups = defaultdict(list)
    for item in iterable:
        groups[key(item)].append(item)

    return {tuple(g): k for k, g in groups.items()}


def get_descendants_simple(nodes: Iterable[Node]) -> Iterator[Node]:
    for node in nodes:
        yield node
        for output in node.outputs:
            yield from get_descendants_simple(Maps.links[output])


def arrange_principled() -> None:
    for col in Maps.universal_columns:
        if target_nodes := [n for n in col if n.bl_idname in TARGET_NODE_TYPES]:
            break
    else:
        return

    all_img_nodes = [n for n in get_ancestors(target_nodes) if n.bl_idname == 'ShaderNodeTexImage']

    if not all_img_nodes:
        return

    grouped_by_parent = group_by(all_img_nodes, key=lambda n: n.parent)
    img_nodes = max(grouped_by_parent, key=len)
    x_loc = lambda n: abs_loc(n).x
    leftmost = min(img_nodes, key=x_loc)
    leftmost_row = tuple(get_descendants_simple([leftmost]))

    for img_node in img_nodes:
        row = get_descendants_simple([img_node])
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

    for group in group_by(img_nodes, key=x_loc):
        if len(group) == 1:
            continue

        highest_top = get_top(group[0])
        for node, vec in get_arranged([group]).items():
            move_to(node, y=vec.y + highest_top)

    if frame := leftmost.parent:
        regenerate_columns(frame)


# -------------------------------------------------------------------
#   Move to linked Y
# -------------------------------------------------------------------


def get_linked_y_locs(node: Node) -> list[tuple[Node, float]]:
    y_locs = []
    is_reroute = node.bl_idname == 'NodeReroute'

    for socket in chain(node.inputs, node.outputs):
        if not socket.is_linked or socket.is_unavailable:
            continue

        socket_y = get_socket_y(socket, not is_reroute)
        for linked_socket in chain(*map(get_real_sockets, Maps.sockets[socket])):
            linked_y = get_socket_y(linked_socket, is_reroute)

            if linked_socket.node.bl_idname == 'NodeReroute':
                linked_y += abs_loc(node).y - socket_y

            y_locs.append((linked_socket.node, corrected_y(node, linked_y)))

    return y_locs


def move_frames_to_linked_y() -> None:
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


def get_ideal_y(node: Node, divided_rows: Collection[Sequence[Node]], line_y: Line) -> float:
    y = abs_loc(node).y
    parent = node.parent

    exclusive = node.bl_idname != 'NodeReroute' or parent
    y_locs = [y for n, y in get_linked_y_locs(node) if not exclusive or n.parent == parent]

    if not y_locs:
        return y

    row = next((r for r in divided_rows if node in r), None)
    if row and node not in {row[0], row[-1]}:
        return y

    if not parent:
        return fmean(y_locs)

    height = y - get_bottom(node)
    return clamp(fmean(y_locs), line_y.a + height, line_y.b)


def get_overlapping_lines(lines: dict[Node, Line]) -> dict[Node, Node]:
    keys = tuple(lines)
    margin = MARGIN.y / 2

    overlapping = {}
    for pair in combinations(lines, 2):
        most_moved, other = sorted(pair, key=keys.index)

        if lines[most_moved].overlaps(lines[other]):
            real_top = abs_loc(most_moved).y + margin

            if lines[most_moved].b != real_top:
                overlapping[most_moved] = other

            real_bottom = get_bottom(most_moved) - margin
            if not Line(real_bottom, real_top).overlaps(lines[other]):
                continue

            if lines[other].b != abs_loc(other).y + margin:
                overlapping[other] = most_moved

    return overlapping


def partial_disperse_nodes_y(ideal_y_locs: dict[Node, float]) -> None:
    margin = MARGIN.y / 2

    lines = {}
    most_moved = lambda ny: abs(abs_loc(ny[0]).y - ny[1])
    for node, y in sorted(ideal_y_locs.items(), key=most_moved, reverse=True):
        line = Line(get_bottom(node, y), get_top(node, y))
        line.expand(margin)
        lines[node] = line

    while overlapping := get_overlapping_lines(lines):
        for node in overlapping:
            line = Line(get_bottom(node), abs_loc(node).y)
            line.expand(margin)
            lines[node] = line

    for node, line in lines.items():
        move_to(node, y=corrected_y(node, line.b - margin))


def move_to_linked_y(columns: Sequence[Sequence[Node]]) -> None:
    nodes = tuple(chain(*columns))
    reroutes = {n for n in nodes if n.bl_idname == 'NodeReroute'}

    divided_rows = []
    for row in group_by(nodes, key=get_top):
        row = [n for n in row if n not in reroutes]
        row_len = len(row)

        if row_len < 3:
            continue

        curr_idx = 0
        for i, j in pairwise(range(row_len)):
            if abs_loc(row[j]).x - get_right(row[i]) > MARGIN.x:
                divided_rows.append(row[curr_idx:i + 1])
                curr_idx = j

        divided_rows.append(row[curr_idx:j + 1])

    line_y = get_box(nodes).line_y

    for col in columns:
        ideal_y_locs = {n: get_ideal_y(n, divided_rows, line_y) for n in col if n not in reroutes}
        partial_disperse_nodes_y(ideal_y_locs)

    for col in columns:
        ideal_y_locs = {n: get_ideal_y(n, divided_rows, line_y) for n in col if n in reroutes}
        partial_disperse_nodes_y(ideal_y_locs)


# -------------------------------------------------------------------
#   Disperse Y
# -------------------------------------------------------------------


def get_merged_lines(lines: list[Line]) -> list[Line]:
    if not lines:
        return []

    lines.sort(key=lambda l: l.a)
    merged = []
    for line in lines:
        if merged and merged[-1].b >= line.a:
            merged[-1].b = max(merged[-1].b, line.b)
        else:
            merged.append(line)

    return merged


def get_closest_gap(box: Box, lines_y: Sequence[Line]) -> Line:
    if not lines_y:
        return None

    center = box.center.y
    height = box.height

    vals = chain([lines_y[0].a - INF_BEYOND], chain(*lines_y), [lines_y[-1].b + INF_BEYOND])
    gaps = [
      l for l in zip(vals, vals) if (d := l[1] - l[0]) >= height or abs(d - height) <= OVERLAP_TOL]

    closest_y = min(chain(*gaps), key=lambda y: abs(y - center))
    return next(Line(*l) for l in gaps if closest_y in l)


@dataclass(slots=True)
class Disperser:
    key: Hashable
    box: Box
    overlappers_x: list['Disperser'] = field(default_factory=list)
    frozen_by: 'Disperser | None' = None
    prev_movement: float | None = None
    switched_dir_before: bool = False

    def extend_overlappers_x(self, items: Iterable['Disperser']) -> None:
        line = self.box.line_x
        for item in items:
            if item == self:
                continue

            if self not in item.overlappers_x:
                if not line.overlaps(item.box.line_x) or is_parented(self.key, item.key):
                    continue

            self.overlappers_x.append(item)

    def has_overlaps(self) -> bool:
        return any(self.box.overlaps(k.box) for k in self.overlappers_x)

    def get_overlap_movement(self) -> tuple[float, list['Disperser']]:
        center = self.box.center
        vec = Vector((0, 0))
        overlappers = []
        for other in self.overlappers_x:
            if self.box.overlaps(other.box):
                vec += other.box.center - center
                overlappers.append(other)

        if not overlappers:
            return (vec.y, overlappers)

        vec /= len(overlappers)
        vec.negate()
        vec.normalize()

        movement = vec.y * DISPERSE_MULT
        if round(movement, 1) == 0:
            prev_movement = self.prev_movement
            movement = -DISPERSE_MULT if prev_movement and prev_movement < 0 else DISPERSE_MULT

        return (movement, overlappers)

    def get_lines_y(self) -> list[Line]:
        keys = [k for k in self.overlappers_x if not k.overlappers_x]
        if keys:
            keys.extend([k for k in self.overlappers_x if k.frozen_by])

        return get_merged_lines([k.box.line_y for k in keys])

    def get_better_movement(
      self,
      movement: float,
      lines_y: Sequence[Line] | None = None,
      prevent_overshoot: bool = False,
    ) -> float:
        if lines_y is None:
            lines_y = self.get_lines_y()

        if not lines_y:
            return movement

        box = self.box

        closest_gap = get_closest_gap(box, lines_y)
        center = box.center.y
        closest_y = min(closest_gap, key=lambda y: abs(y - center))

        switch_dir = movement < 0 if closest_gap.a == closest_y else movement > 0
        if switch_dir:
            movement *= -1

        if prevent_overshoot:
            diff = box.height - box.line_y.overlap_amount(closest_gap)
            if abs(movement) > diff:
                movement = -diff if movement < 0 else diff

        prev_movement = self.prev_movement

        diff_dir = prev_movement and (prev_movement > 0) != (movement > 0)
        should_switch_dir = diff_dir and not self.switched_dir_before

        if should_switch_dir:
            self.switched_dir_before = True

        return prev_movement if diff_dir and not should_switch_dir else movement


def freeze_movables(competing: MutableSequence[Disperser], movement: float) -> None:
    center = lambda i: i.box.center.y
    if movement > 0:
        favoured = max(competing, key=center)
    else:
        favoured = min(competing, key=center)

    competing.remove(favoured)

    if gap := get_closest_gap(favoured.box, favoured.get_lines_y()):
        gap_overlaps = [(k, k.box.line_y.overlap_amount(gap)) for k in competing]
        preventer, overlap = max(gap_overlaps, key=itemgetter(1))
        if gap.length - overlap < favoured.box.height:
            preventer.frozen_by = None
            favoured.frozen_by = preventer

    if not favoured.frozen_by:
        for item in competing:
            item.frozen_by = favoured


def disperse_boxes(
  movable_boxes: dict[Hashable, Box],
  immovable_boxes: dict[Hashable, Box],
) -> None:
    movables = [Disperser(*k) for k in movable_boxes.items()]
    immovables = [Disperser(*k) for k in immovable_boxes.items()]

    items = movables + immovables
    for item in movables:
        item.extend_overlappers_x(items)

    i = 0
    iter_limit = len(movables) * ITER_LIMIT_MULT
    while any(k.has_overlaps() for k in movables):
        movements = []
        for item in movables:
            if item.frozen_by:
                if item.box.overlaps(item.frozen_by.box):
                    continue
                else:
                    item.frozen_by = None

            movement, overlappers = item.get_overlap_movement()

            if not overlappers:
                item.prev_movement = None
                continue

            competing = [
              k for k in overlappers
              if k.prev_movement and (k.prev_movement > 0) == (movement > 0)]
            if competing:
                freeze_movables(competing + [item], movement)
                if item.frozen_by:
                    continue

            movements.append((item, item.get_better_movement(movement)))

        for item, movement in movements:
            item.box.move(y=movement)
            item.prev_movement = movement

        i += 1
        if i > iter_limit:  # This should never happen
            break


def disperse_nodes(
  movable_boxes: dict[Node | tuple[Node, ...], Box],
  immovable_boxes: dict[Hashable, Box],
) -> None:
    old_tops = {k: b.top for k, b in movable_boxes.items()}
    disperse_boxes(movable_boxes, immovable_boxes)
    for key, box in movable_boxes.items():
        if isinstance(key, Node):
            move(key, y=-old_tops[key] + box.top)
        else:
            for node in key:
                move(node, y=-old_tops[key] + box.top)


# -------------------------------------------------------------------
#   Align linear chains
# -------------------------------------------------------------------


def get_singly_linked_ancestors(node: Node) -> Iterator[Node]:
    successors = get_successors(node)

    if len(successors) > 1:
        return

    yield node

    predecessors = get_predecessors(node)

    if len(predecessors) != 1 or len(successors) != 1:
        return

    pred = predecessors[0]

    if pred.parent != node.parent:
        return

    col = next(c for c in Maps.frame_columns[node.parent] if pred in c)
    pred_right = max(map(get_right, col))
    node_left = abs_loc(node).x
    spaced_far = int(node_left - pred_right) > MARGIN.x
    nodes = chain(*Maps.universal_columns)
    if spaced_far and any(pred_right < abs_loc(n).x < node_left for n in nodes):
        return

    yield from get_singly_linked_ancestors(pred)


def get_linear_chains(columns: Sequence[Sequence[Node]]) -> list[list[Node]]:
    linear_chains = []
    for col in columns[:-1]:
        for node in col:
            if node in chain(*linear_chains):
                continue

            lin_chain = list(get_singly_linked_ancestors(node))
            if len([n for n in lin_chain if n.bl_idname != 'NodeReroute']) > 1:
                lin_chain.reverse()
                linear_chains.append(lin_chain)

    return linear_chains


def align_lin_chain(lin_chain: Sequence[Node], line_y: Line | None) -> None:
    target_y = min(map(get_top, lin_chain))

    lowers_frame_bottom = line_y and line_y.a > min([get_bottom(n, target_y) for n in lin_chain])
    if (line_y and target_y > line_y.b) or lowers_frame_bottom:
        return

    lower_col_boxes = {}
    for col in Maps.frame_columns[lin_chain[0].parent]:
        try:
            node = next(n for n in lin_chain if n in col)
        except StopIteration:
            continue

        subcol_boxes = get_col_boxes([[n for n in col if n != node]])
        top = get_top(node)
        for subcol, box in subcol_boxes.items():
            if top > box.top:
                lower_col_boxes[subcol] = box

    sub_boxes = {}
    for node in lin_chain:
        move_to(node, y=corrected_y(node, target_y))
        box = Box(abs_loc(node).x, get_bottom(node), get_right(node), target_y + INF_BEYOND)
        box.expand(y=MARGIN.y / 2)
        sub_boxes[node] = box

    disperse_nodes(lower_col_boxes, sub_boxes)


def align_linear_chains(frame: NodeFrame | None) -> None:
    columns = Maps.frame_columns[frame]
    linear_chains = get_linear_chains(columns)

    def idx_in_col(lin_chain1, lin_chain2):
        for col in columns:
            idx = lambda c: next(i for i, n in enumerate(col) if n in c)
            try:
                return -1 if idx(lin_chain1) < idx(lin_chain2) else 1
            except StopIteration:
                continue

        return 0

    linear_chains.sort(key=cmp_to_key(idx_in_col))
    line_y = get_box(chain(*columns)).line_y if frame else None
    for lin_chain in linear_chains:
        align_lin_chain(lin_chain, line_y)

    for col in columns:
        col.sort(key=get_top, reverse=True)


# -------------------------------------------------------------------
#   Align highest nodes
# -------------------------------------------------------------------


def get_alignable_ancestors(trail: list[Node]) -> list[Node]:
    predecessors = [n for n in get_predecessors(trail[-1]) if n.parent == trail[-1].parent]
    try:
        pred = max(predecessors, key=get_top)
    except ValueError:
        return trail

    columns = Maps.frame_columns[pred.parent]
    col = next(c for c in columns if pred in c)

    if col[0] != pred or trail[-1] not in columns[columns.index(col) - 1]:
        return trail

    max_right = max(map(get_right, col))
    if max_right - get_right(pred) >= (max_right - abs_loc(pred).x) / 3:
        return trail

    trail.append(pred)
    return get_alignable_ancestors(trail)


def align_highest_nodes(columns: Sequence[Sequence[Node]]) -> None:
    prev_furthest_idx = 0
    for i, col in enumerate(columns):
        if i < prev_furthest_idx:
            continue

        trail = [n for n in get_alignable_ancestors([col[0]]) if n.bl_idname != 'NodeReroute']
        prev_furthest_idx = i + len(trail)
        tops = {get_top(n) for n in trail}

        if len(tops) < 2:
            continue

        target_y = max(tops)

        curr_aligned = []
        future_aligned = set(trail)
        for group, y in group_by(chain(*columns), key=get_top).items():
            if y not in tops:
                continue

            if y != target_y:
                curr_aligned.append(group)
            else:
                future_aligned.update(group)

        if len(future_aligned) > max(map(len, curr_aligned)) * 2:
            for node in trail:
                move_to(node, y=corrected_y(node, target_y))


# -------------------------------------------------------------------
#   Compact frames X
# -------------------------------------------------------------------


def add_children(nodes: set[Node]) -> None:
    for frame in {n.parent for n in nodes}:
        if frame:
            nodes.update(Maps.used_children[frame])


def saves_space(box1: Box, box2: Box, boxes: dict[Hashable, Box]) -> bool:

    # If the height of the boxes within the overlap range is >=
    # `COMPACT_HEIGHT` (around three math nodes) + margin * 2, then compact
    # the frame. (This is a heuristic meant to approximate how much space
    # would be saved after dispersing the frames.)

    line1 = box1.line_y
    center2 = box2.center.y
    upper_overlap = line1.overlap_amount(Line(center2, box2.top))
    lower_overlap = line1.overlap_amount(Line(box2.bottom, center2))

    height = 0
    if upper_overlap > lower_overlap:
        condition = lambda b: b.bottom < box1.top
    else:
        condition = lambda b: b.top > box1.bottom

    y_locs = []
    for key3, box3 in boxes.items():
        if Line(box2.left, box1.right).overlaps(box3.line_x) and condition(box3):
            if isinstance(key3, NodeFrame):
                height += box3.height
            else:
                y_locs.extend(box3.line_y)

    if y_locs:
        height += max(y_locs) - min(y_locs)

    return height > COMPACT_HEIGHT + MARGIN.y * 2


def get_overlapping(
  to_move: set[Node],
  boxes: dict[NodeFrame | tuple[Node, ...], Box],
  key1: NodeFrame | tuple[Node, ...],
  cmp: Callable[[float, float], bool],
) -> list[NodeFrame | tuple[Node, ...]]:
    box1 = boxes[key1]
    frames_to_move = {n.parent for n in to_move}
    overlapping = []
    for key2, box2 in boxes.items():
        if cmp(box1.left, box2.left):
            continue

        if isinstance(key2, NodeFrame):
            valid = key2 in frames_to_move and not is_parented(key1, key2)
        else:
            valid = to_move.intersection(key2)

        if valid and box1.overlaps(box2) and saves_space(box1, box2, boxes):
            overlapping.append(key2)

    return overlapping


def update_boxes_by_nodes(
  nodes: Iterable[Node],
  boxes: dict[NodeFrame | tuple[Node, ...], Box],
  movement: float,
) -> None:
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


def compact_frames_x(
  frame_boxes: dict[NodeFrame, Box],
  col_boxes: dict[tuple[Node, ...], Box],
) -> None:
    boxes = sorted_boxes(frame_boxes | col_boxes)
    children = Maps.used_children

    for frame1, box1 in frame_boxes.items():
        nodes_right = Maps.frame_descendants[frame1].copy()
        add_children(nodes_right)

        children1 = get_nested_children(frame1)
        center1 = box1.center.x

        nodes_left = set(chain(*children.values())) - nodes_right.union(children1)
        for frame2, box2 in frame_boxes.items():
            if box1.left == box2.left:
                nodes_left.difference_update(children[frame2])

        add_children(nodes_left)

        # -------------------------------------------------------------------

        if not any(len(nodes_right.intersection(c)) not in {0, len(c)} for c in col_boxes):
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

        if not any(len(nodes_left.intersection(c)) not in {0, len(c)} for c in col_boxes):
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


def space_to_move(frame: NodeFrame) -> float:
    children = Maps.used_children[frame]
    lengths = chain(get_input_lengths(children).values(), get_output_lengths(children).values())
    return min(lengths, default=0)


def should_center_x(
  frame: NodeFrame,
  target_center: float,
  frame_boxes: dict[NodeFrame, Box],
) -> bool:
    box = frame_boxes[frame]
    movement = target_center - box.center.x

    if round(movement, 1) == 0:
        return False

    children = Maps.used_children[frame]
    if link_stretch(children) < link_stretch(children, movement):
        return False

    moved_box = replace(box)
    moved_box.move(x=movement)
    for other_box in frame_boxes.values():
        if box is other_box or int(other_box.center.x) == int(target_center):
            continue

        if box.overlaps(other_box) != moved_box.overlaps(other_box):
            return False

    return True


def center_frames_x(frame_boxes: dict[NodeFrame, Box]) -> None:
    others = {f1: [f2 for f2 in frame_boxes if f1 != f2] for f1 in frame_boxes}
    history = defaultdict(set)

    while True:
        has_moved = False
        for frame1 in sorted(frame_boxes, key=space_to_move):
            box1 = frame_boxes[frame1]
            center1 = box1.center.x
            for frame2 in others[frame1]:
                box2 = frame_boxes[frame2]
                center2 = box2.center.x

                center_diff = lambda f: abs(center2 - frame_boxes[f].center.x)
                not_closest = min(others[frame2], key=center_diff) != frame1
                if not_closest and center_diff(frame1) > fmean((box1.width, box2.width)) / 3:
                    continue

                if not should_center_x(frame2, center1, frame_boxes):
                    continue

                item = (frame1, int(center1))
                if item in history[frame2]:
                    continue

                movement = center1 - center2
                move(frame2, x=movement)
                box2.move(x=movement)

                has_moved = True
                history[frame2].add(item)

        if not has_moved:
            break


# -------------------------------------------------------------------
#   Unite box rows
# -------------------------------------------------------------------


def unite(
  row: Collection[NodeFrame | tuple[Node, ...]],
  boxes: dict[NodeFrame | tuple[Node, ...], Box],
) -> None:
    if len(row) < 3:
        return

    for key in row:
        rightwards = boxes[key].get_rightwards(boxes)

        if rightwards is None or rightwards in row or isinstance(rightwards, tuple):
            continue

        box = boxes[rightwards]

        if box.get_rightwards(boxes) not in row:
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


def unite_box_rows(
  frame_boxes: dict[NodeFrame, Box],
  col_boxes: dict[tuple[Node, ...], Box],
) -> None:
    boxes = sorted_boxes(frame_boxes | col_boxes)
    for row in get_box_rows(boxes):
        unite(row, boxes)


# -------------------------------------------------------------------
#   Center and disperse frames Y
# -------------------------------------------------------------------


def get_nested_boxes(
  frame_boxes: dict[NodeFrame, Box],
) -> Iterator[tuple[dict[NodeFrame, Box], dict[tuple[Node, ...], Box]]]:
    for frame in frame_boxes:
        nested_frame_boxes = {f: b for f, b in frame_boxes.items() if f.parent == frame}

        if not nested_frame_boxes:
            continue

        nested_col_boxes = get_col_boxes(Maps.frame_columns[frame])
        yield (nested_frame_boxes, nested_col_boxes)

        yield from get_nested_boxes(nested_frame_boxes)


def center_frames_y(
  frame_boxes: dict[NodeFrame, Box],
  nearest: dict[NodeFrame, Hashable],
) -> list[list[NodeFrame]]:
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

            if not box1.line_y.overlaps(box2.line_y):
                continue

            height1 = box1.height

            if box2.bottom > box1.bottom + height1 / 2:
                continue

            if frame2 not in nearest[row[-1]] and abs(box2.height - height1) > height1 / 2:
                continue

            movement = box1.center.y - box2.center.y

            if movement == 0:
                continue

            prev_left, prev_right = frame_boxes[row[-1]].line_x
            curr_left, curr_right = box2.line_x

            if prev_left > curr_left or curr_right < prev_right:
                break

            if prev_right * -2 + prev_left - curr_right + curr_left * 2 > ntree_span / 4:
                break

            move(frame2, y=movement)
            box2.move(y=movement)

            row.append(frame2)

        rows.append(row)

    return rows


def get_overlappers_x(
  real_boxes: dict[Hashable, Box],
  boxes: dict[Hashable, Box],
) -> defaultdict[Hashable, list[Hashable]]:
    seen = set()
    overlappers_x = defaultdict(list)
    for a, box1 in real_boxes.items():
        for b, box2 in boxes.items():
            if {a, b} in seen or a == b:
                continue

            if box1.line_x.overlaps(box2.line_x) and not is_parented(a, b):
                overlappers_x[a].append(b)
                if b in real_boxes:
                    overlappers_x[b].append(a)

            seen.add(frozenset((a, b)))

    return overlappers_x


def will_break_box_row(
  frame: NodeFrame,
  row: dict[Hashable],
  boxes: dict[Hashable, Box],
  line_x: Line,
) -> bool:
    row = [k for k in row if k == frame or not line_x.overlaps(boxes[k].line_x)]
    i = row.index(frame)
    leftwards = row[(i - MIN_ADJ_COLS):(i)]
    rightwards = row[(i + 1):(i + MIN_ADJ_COLS + 1)]
    return any(#
      isinstance(a, tuple) and isinstance(b, tuple)
      for a, b in pairwise(leftwards + rightwards))


def get_levelled_frames(
  row_items: dict[NodeFrame, Sequence[list[Box], Sequence[Hashable]]],
  boxes: dict[Hashable, Box],
  movement: float,
) -> set[NodeFrame]:
    levelled = set()
    for frame, (overlappers_x, row) in row_items.items():
        box = replace(boxes[frame])
        box.move(y=-movement)

        will_overlap = any(box.overlaps(b) for b in overlappers_x)
        if will_overlap or abs(movement) > box.height / 2:
            continue

        if movement == 0 or not will_break_box_row(frame, row, boxes, box.line_x):
            levelled.add(frame)

    return levelled


def center_and_disperse_frames_y(
  frame_boxes: dict[NodeFrame, Box],
  col_boxes: dict[tuple[Node, ...], Box],
) -> None:
    nested_boxes = tuple(get_nested_boxes(frame_boxes))
    for nested_frame_boxes, nested_col_boxes in reversed(nested_boxes):
        disperse_nodes(nested_frame_boxes, nested_col_boxes)
        parent = next(iter(nested_frame_boxes)).parent
        frame_boxes[parent] = get_frame_box(parent)

    boxes = sorted_boxes(frame_boxes | col_boxes)

    nearest = defaultdict(set)
    for frame1, box1 in frame_boxes.items():
        if rightwards := box1.get_rightwards(boxes):
            nearest[frame1].add(rightwards)

        if leftwards := box1.get_leftwards(boxes):
            nearest[frame1].add(leftwards)

    before_centered = {f: (b.top, replace(b)) for f, b in frame_boxes.items()}
    frame_rows = center_frames_y(frame_boxes, nearest)

    dispersed_boxes = {f: replace(b) for f, b in frame_boxes.items()}
    old_tops = {f: b.top for f, b in dispersed_boxes.items()}
    disperse_boxes(dispersed_boxes, col_boxes)
    movements = {f: old_tops[f] - b.top for f, b in dispersed_boxes.items()}
    dispersed_boxes.update(col_boxes)

    overlappers_x = get_overlappers_x(frame_boxes, boxes)
    rows = get_box_rows(boxes)
    row_map = {f: next(r for r in rows if f in r) for f in frame_boxes}

    for row in frame_rows:
        row_items = {f: ([dispersed_boxes[k] for k in overlappers_x[f]], row_map[f]) for f in row}
        results = {movements[f]: get_levelled_frames(row_items, boxes, movements[f]) for f in row}
        counts = {m: sum(len(nearest[f] & l) + 1 for f in l) for m, l in results.items()}
        largest = max(counts.values())

        if largest < 2:
            to_move_back = row
        else:
            best_movement = min([m for m, l in counts.items() if l == largest], key=abs)
            levelled = results[best_movement]
            to_move_back = []
            for frame in row:
                if frame in levelled:
                    move(frame, y=-best_movement)
                    frame_boxes[frame].move(y=-best_movement)
                else:
                    to_move_back.append(frame)

        for frame in to_move_back:
            old_y, old_box = before_centered[frame]
            move(frame, y=old_y - frame_boxes[frame].top)
            frame_boxes[frame] = old_box

    disperse_nodes(frame_boxes, col_boxes)


# -------------------------------------------------------------------
#   Contract X
# -------------------------------------------------------------------


def get_beyond(
  box1: Box,
  boxes: dict[NodeFrame | tuple[Node, ...], Box],
) -> tuple[list[Node], list[float]]:
    beyond = []
    distances = []
    for key2, box2 in boxes.items():
        if box2.left <= box1.left or box2.right <= box1.right:
            continue

        if isinstance(key2, tuple):
            beyond.extend(key2)
        else:
            beyond.append(key2)

        distances.append(box2.left - box1.right)

    return beyond, distances


def has_closer(
  box1: Box,
  boxes: dict[NodeFrame | tuple[Node, ...], Box],
  movement: float,
) -> bool:
    for box2 in boxes.values():
        if box2.left == box1.left and any(d < movement for d in get_beyond(box2, boxes)[1]):
            return True


def contract_x(
  frame_boxes: dict[NodeFrame, Box],
  col_boxes: dict[tuple[Node, ...], Box],
) -> None:
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


def get_reroute_ancestors(
  node: Node,
  reroutes: Collection[NodeReroute],
  seen: Collection[NodeReroute],
) -> Iterator[NodeReroute]:
    if node not in reroutes:
        return

    yield node

    if node in seen:
        return

    linked = Maps.links[node.inputs[0]][0]
    yield from get_reroute_ancestors(linked, reroutes, seen)


def get_reroute_segments(children: Iterable[Node]) -> list[tuple[NodeReroute, ...]]:
    reroutes = [#
      n for n in children
      if n.bl_idname == 'NodeReroute'
      and (Maps.links[n.inputs[0]] and Maps.links[n.outputs[0]])]

    segments = []
    for reroute in reroutes:
        seen = set(chain(*segments))
        if ancestors := tuple(get_reroute_ancestors(reroute, reroutes, seen)):
            segments.append(ancestors)

    segments.sort(key=len)
    for s1 in reversed(segments):
        for i, s2 in enumerate(segments):
            if s1 != s2:
                segments[i] = [n for n in s2 if n not in s1]

    segments = [tuple(reversed(s)) for s in segments if s]
    segments.sort(key=lambda s: abs_loc(s[0]).x)

    return segments


def arrange_framed_reroutes(segment: Sequence[NodeReroute], children: Collection[Node]) -> None:
    sockets = Maps.sockets

    end = segment[-1]
    linked = sockets[end.outputs[0]]
    input = linked[0]
    if input.node in children:
        move_to(end, y=get_input_y(input))
        x = abs_loc(input.node).x - MARGIN.x
        if link_stretch([end]) >= link_stretch([end], x - abs_loc(end).x):
            move_to(end, x=x)
    else:
        move_to(end, y=get_output_y(sockets[end.inputs[0]][0]))

    segment_rest = segment[:-1]

    if not segment_rest:
        return

    output = sockets[segment[0].inputs[0]][0]
    if output.node in children:
        output_y = get_output_y(output)
        movement = abs_loc(segment_rest[0]).x - (get_right(output.node) + MARGIN.x)
        for reroute in segment_rest:
            move(reroute, x=-movement)
    elif len(linked) == 1:
        output_y = get_input_y(linked[0])
    else:
        output_y = abs_loc(end).y

    for reroute in segment_rest:
        move_to(reroute, y=output_y)


def get_movement_x(
  reroute: NodeReroute,
  box: Box,
  boxes: Collection[Box],
  movement: float,
) -> float | None:
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


def disperse_reroute_x(reroute: NodeReroute, boxes: Collection[Box]) -> None:
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


def disperse_reroutes_x(
  segments: Sequence[Sequence[NodeReroute]],
  boxes: list[Box] | None = None,
) -> None:
    try:
        reroute = segments[0][0]
    except IndexError:
        return

    if boxes is None:
        boxes = []

    margin = MARGIN / 2 - dimensions(reroute) / 2
    for node in Maps.used_children[reroute.parent]:
        if node.bl_idname != 'NodeReroute':
            box = get_box([node])
            box.expand(*margin)
            boxes.append(box)

    for segm in segments:
        for reroute in reversed(segm):
            disperse_reroute_x(reroute, boxes)


def arrange_all_framed_reroutes(frame_boxes: dict[NodeFrame, Box]) -> None:

    # A while loop isn’t worth the risk here. Since `bpy.ops.translate()`
    # rounds new locations, reroutes could endlessly try and fail to move into
    # a position, missing it each time. Two iterations should also be all
    # that’s needed.

    items = [(f, c) for f, c in Maps.used_children.items() if f and len(c) > 1]
    for frame, children in items * 2:
        segments = get_reroute_segments(children)

        if not segments:
            continue

        reroutes = tuple(chain(*segments))
        old_y_locs = [abs_loc(r).y for r in reroutes]

        for segm in segments:
            arrange_framed_reroutes(segm, children)

        disperse_reroutes_x(segments)

        box = frame_boxes[frame]
        for reroute, old_y in zip(reroutes, old_y_locs):
            loc = abs_loc(reroute)
            if loc.y > box.top or loc.y < box.bottom:
                move_to(reroute, y=old_y)


def arrange_unframed_reroutes(segment: Sequence[NodeReroute]) -> None:
    output_y = get_output_y(Maps.sockets[segment[0].inputs[0]][0])
    for reroute in segment:
        move_to(reroute, y=output_y)

    if len(segment) == 1:
        return

    end = segment[-1]
    input = Maps.sockets[end.outputs[0]][0]
    move_to(end, y=get_input_y(input))

    x = abs_loc(input.node).x - MARGIN.x
    if link_stretch([end]) >= link_stretch([end], x - end.location.x):
        move_to(end, x=x)


# -------------------------------------------------------------------
#   Move unused
# -------------------------------------------------------------------


def get_unused(frame: NodeFrame | None) -> list[Node]:
    used = set(chain(*Maps.universal_columns))
    unused = []
    for node in Maps.all_children[frame]:
        if not node.select or node in Maps.used_children[frame]:
            continue

        if node.bl_idname == 'NodeFrame' and used.intersection(Maps.all_children[node]):
            continue

        unused.append(node)

    return unused


def move_framed_unused(frame: NodeFrame) -> None:
    box = get_box(Maps.used_children[frame])
    for node in get_unused(frame):
        move_to(node, x=box.left, y=box.bottom + (get_top(node) - get_bottom(node)))


def get_unused_subtrees(unused: Collection[Node]) -> list[Collection[Node]]:
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


def move_unframed_unused(offset: Vector, boxes: dict[Hashable, Box]) -> None:
    unused = get_unused(None)

    for node in unused:
        move(node, x=offset.x, y=offset.y)

    subtree_boxes = {tuple(s): get_box(s) for s in get_unused_subtrees(unused)}
    for box in subtree_boxes.values():
        box.expand(*MARGIN / 2)

    indexed_boxes = {i: b for i, b in enumerate(boxes.values())}
    disperse_nodes(subtree_boxes, indexed_boxes)


# -------------------------------------------------------------------
#   Maps
# -------------------------------------------------------------------


def clear_bl_data_references() -> None:
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
    frame_descendants = {}


# -------------------------------------------------------------------


class NA_OT_ArrangeSelected(Operator):
    bl_idname = "node.na_arrange_selected"
    bl_label = "Arrange Selected"
    bl_description = "Arrange selected nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context) -> set[str]:
        global MARGIN
        MARGIN = Vector(context.scene.na_settings.margin).freeze()

        global SCALE_FAC
        SCALE_FAC = context.preferences.system.ui_scale

        # -------------------------------------------------------------------

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

        used_nodes = tuple(chain(*universal_columns))
        for socket, linked in Maps.links.items():
            indices = [i for i, n in enumerate(linked) if n not in used_nodes]
            for i in reversed(indices):
                del linked[i]
                del Maps.sockets[socket][i]

        # -------------------------------------------------------------------

        for node in nodes:
            Maps.all_children[node.parent].append(node)

        locs = [(n, abs_loc(n)) for n in used_nodes]
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
            align_linear_chains(frame)

        align_highest_nodes(frame_columns.get(None, []))

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


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        if cls.is_registered:
            bpy.utils.unregister_class(cls)
