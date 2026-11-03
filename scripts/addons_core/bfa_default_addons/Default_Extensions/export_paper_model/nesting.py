from mathutils.geometry import box_pack_2d
from time import time


def get_nester(method):
    can_pack = can_pack_ccor if method == 'CCOR' else can_pack_bpy
    return branch_and_bound(can_pack)


class Page:
    """Container for several Islands"""
    __slots__ = ('islands', 'name', 'image_path')

    def __init__(self, num=1, islands=None):
        self.islands = islands or list()
        self.name = "page{}".format(num)  # note: this is only used in svg files naming
        self.image_path = None


def can_pack_ccor(islands, cage_size):
    raise NotImplementedError
    if len(islands) <= 1:
        islands[0].pos.xy = 0, 0
        return True
    for isle in islands[1:]:
        ...
    boxes = [[0, 0, isle.bounding_box.x, isle.bounding_box.y / aspect] for isle in islands]
    width, height = box_pack_2d(boxes)
    if width < cage_size.x > height:
        for (x, y, *_), isle in zip(boxes, islands):
            isle.pos.xy = x, y * aspect
        return True
    return False


def can_pack_bpy(islands, cage_size):
    if len(islands) <= 1:
        islands[0].pos.xy = 0, 0
        return True
    aspect = cage_size.y / cage_size.x
    boxes = [[0, 0, isle.bounding_box.x, isle.bounding_box.y / aspect] for isle in islands]
    width, height = box_pack_2d(boxes)
    if width < cage_size.x > height:
        for (x, y, *_), isle in zip(boxes, islands):
            isle.pos.xy = x, y * aspect
        return True
    return False


def branch_and_bound(can_pack_fn, timeout_seconds=15):
    # exhaustive search for minimal number of pages
    def result(islands, cage_size):
        time_limit = time() + timeout_seconds
        # default solution: each island goes to i-th page on position [0, 0]
        best = [(i, [0, 0]) for i, _ in enumerate(islands)]
        # current solution: first island will definitely go to page 0
        path = [0]
        while True:
            if path[-1] > max(path[:-1], default=0) + 1 or max(path) >= max(i for i, _ in best):
                # invalid step
                path.pop()
                if len(path) <= 1:
                    break
                path[-1] += 1
                continue
            page = [isle for i, isle in zip(path, islands) if i == path[-1]]
            if can_pack_fn(page, cage_size):
                # good step
                if len(path) == len(islands):
                    best = [(i, isle.pos.xy) for i, isle in zip(path, islands)]
                    path.pop()
                    path[-1] += 1
                else:
                    path.append(0)
            else:
                # bad step
                if time() > time_limit:
                    break
                path[-1] += 1
        pages = [[] for _ in range(max(i for i, _ in best) + 1)]
        for (i, pos), isle in zip(best, islands):
            isle.pos.xy = pos
            pages[i].append(isle)
        return [Page(i, page) for i, page in enumerate(pages)]
    return result
