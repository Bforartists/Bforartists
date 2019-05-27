import bpy
from bpy.app.handlers import persistent

import queue

from blenderkit import utils


@persistent
def scene_load(context):
    if not (bpy.app.timers.is_registered(queue_worker)):
        bpy.app.timers.register(queue_worker)


def get_queue():
    # we pick just a random one of blender types, to try to get a persistent queue
    t = bpy.types.Scene

    if not hasattr(t, 'task_queue'):
        t.task_queue = queue.Queue()
    return t.task_queue


def add_task(task):
    q = get_queue()
    q.put(task)


def queue_worker():
    q = get_queue()
    while not q.empty():
        utils.p('as a task:   ')
        # print('window manager', bpy.context.window_manager)
        task = q.get()
        utils.p(task)
        try:
            task[0](*task[1])
        except Exception as e:
            utils.p('task failed:')
            print(e)
    return 2.0


def register():
    bpy.app.handlers.load_post.append(scene_load)


def unregister():
    bpy.app.handlers.load_post.remove(scene_load)


