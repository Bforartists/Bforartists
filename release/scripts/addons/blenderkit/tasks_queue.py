# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


from blenderkit import utils

import bpy
from bpy.app.handlers import persistent

import queue
import logging
bk_logger = logging.getLogger('blenderkit')

@persistent
def scene_load(context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.use_timers:
        if not (bpy.app.timers.is_registered(queue_worker)):
            bpy.app.timers.register(queue_worker)


def get_queue():
    # we pick just a random one of blender types, to try to get a persistent queue
    t = bpy.types.Scene

    if not hasattr(t, 'task_queue'):
        t.task_queue = queue.Queue()
    return t.task_queue

class task_object:
    def __init__(self, command = '', arguments = (), wait = 0, only_last = False, fake_context = False, fake_context_area = 'VIEW_3D'):
        self.command = command
        self.arguments = arguments
        self.wait = wait
        self.only_last = only_last
        self.fake_context = fake_context
        self.fake_context_area = fake_context_area

def add_task(task, wait = 0, only_last = False, fake_context = False, fake_context_area = 'VIEW_3D'):
    q = get_queue()
    taskob = task_object(task[0],task[1], wait = wait, only_last = only_last, fake_context = fake_context, fake_context_area = fake_context_area)
    q.put(taskob)


def queue_worker():
    # utils.p('start queue worker timer')

    #bk_logger.debug('timer queue worker')
    time_step = 2.0
    q = get_queue()

    back_to_queue = [] #delayed events
    stashed = {}
    # first round we get all tasks that are supposed to be stashed and run only once (only_last option)
    # stashing finds tasks with the property only_last and same command and executes only the last one.
    while not q.empty():
        # print('queue while 1')

        task = q.get()
        if task.only_last:
            #this now makes the keys not only by task, but also first argument.
            # by now stashing is only used for ratings, where the first argument is url.
            # This enables fast rating of multiple assets while allowing larger delay for uploading of ratings.
            # this avoids a duplicate request error on the server
            stashed[str(task.command)+str(task.arguments[0])] = task
        else:
            back_to_queue.append(task)
    if len(stashed.keys())>1:
        bk_logger.debug('task queue stashed task:' +str(stashed))
    #return tasks to que except for stashed
    for task in back_to_queue:
        q.put(task)
    #return stashed tasks to queue
    for k in stashed.keys():
        q.put(stashed[k])
    #second round, execute or put back waiting tasks.
    back_to_queue = []
    while not q.empty():
        # print('window manager', bpy.context.window_manager)
        task = q.get()

        if task.wait>0:
            task.wait-=time_step
            back_to_queue.append(task)
        else:
            bk_logger.debug('task queue task:'+ str( task.command) +str( task.arguments))
            try:
                if task.fake_context:
                    fc = utils.get_fake_context(bpy.context, area_type = task.fake_context_area)
                    task.command(fc,*task.arguments)
                else:
                    task.command(*task.arguments)
            except Exception as e:
                bk_logger.error('task queue failed task:'+ str(task.command)+str(task.arguments)+ str(e))
                # bk_logger.exception('Got exception on main handler')
                # raise
        # print('queue while 2')
    for task in back_to_queue:
        q.put(task)
    # utils.p('end queue worker timer')

    return 2.0


def register():
    bpy.app.handlers.load_post.append(scene_load)


def unregister():
    bpy.app.handlers.load_post.remove(scene_load)
