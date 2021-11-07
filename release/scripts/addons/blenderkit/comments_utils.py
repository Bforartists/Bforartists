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

# mainly update functions and callbacks for ratings properties, here to avoid circular imports.
import bpy
from blenderkit import utils, paths, tasks_queue, rerequests

import threading
import requests
import logging

bk_logger = logging.getLogger('blenderkit')


def upload_comment_thread(url, comment='', api_key=None):
    ''' Upload rating thread function / disconnected from blender data.'''
    headers = utils.get_headers(api_key)

    bk_logger.debug('upload comment ' + comment)

    # rating_url = url + rating_name + '/'
    data = {
        "content_type": "",
        "object_pk": "",
        "timestamp": "",
        "security_hash": "",
        "honeypot": "",
        "name": "",
        "email": "",
        "url": "",
        "comment": comment,
        "followup": False,
        "reply_to": None
    }

    # try:
    r = rerequests.put(url, data=data, verify=True, headers=headers)
    print(r)
    # print(dir(r))
    print(r.text)
    # except requests.exceptions.RequestException as e:
    #     print('ratings upload failed: %s' % str(e))


def upload_comment_flag_thread( asset_id = '', comment_id='', flag='like', api_key=None):
    ''' Upload rating thread function / disconnected from blender data.'''
    headers = utils.get_headers(api_key)

    bk_logger.debug('upload comment flag' + str(comment_id))

    # rating_url = url + rating_name + '/'
    data = {
        "comment": comment_id,
        "flag": flag,
    }
    url = paths.get_api_url() + 'comments/feedback/'

    # try:
    r = rerequests.post(url, data=data, verify=True, headers=headers)
    print(r.text)

    #here it's important we read back, so likes are updated accordingly:
    get_comments(asset_id, api_key)


def send_comment_flag_to_thread(asset_id = '', comment_id='', flag='like', api_key = None):
    '''Sens rating into thread rating, main purpose is for tasks_queue.
    One function per property to avoid lost data due to stashing.'''
    thread = threading.Thread(target=upload_comment_flag_thread, args=(asset_id, comment_id, flag, api_key))
    thread.start()

def send_comment_to_thread(url, comment, api_key):
    '''Sens rating into thread rating, main purpose is for tasks_queue.
    One function per property to avoid lost data due to stashing.'''
    thread = threading.Thread(target=upload_comment_thread, args=(url, comment, api_key))
    thread.start()


def store_comments_local(asset_id, comments):
    context = bpy.context
    ac = context.window_manager.get('asset comments', {})
    ac[asset_id] = comments
    context.window_manager['asset comments'] = ac


def get_comments_local(asset_id):
    context = bpy.context
    context.window_manager['asset comments'] = context.window_manager.get('asset comments', {})
    comments = context.window_manager['asset comments'].get(asset_id)
    if comments:
        return comments
    return None

def get_comments_thread(asset_id, api_key):
    thread = threading.Thread(target=get_comments, args=([asset_id, api_key]), daemon=True)
    thread.start()

def get_comments(asset_id, api_key):
    '''
    Retrieve comments  from BlenderKit server. Can be run from a thread
    Parameters
    ----------
    asset_id
    headers

    Returns
    -------
    ratings - dict of type:value ratings
    '''
    headers = utils.get_headers(api_key)

    url = paths.get_api_url() + 'comments/assets-uuidasset/' + asset_id + '/'
    params = {}
    r = rerequests.get(url, params=params, verify=True, headers=headers)
    if r is None:
        return
    print(r.status_code)
    if r.status_code == 200:
        rj = r.json()
        # store comments - send them to task queue
        # print('retrieved comments')
        # print(rj)
        tasks_queue.add_task((store_comments_local, (asset_id, rj['results'])))

        # if len(rj['results'])==0:
        #     # store empty ratings too, so that server isn't checked repeatedly
        #     tasks_queue.add_task((store_rating_local_empty,(asset_id,)))
        # return ratings


def store_notifications_count_local(all_count):
    '''Store total count of notifications on server in preferences'''
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    user_preferences.notifications_counter = all_count

def store_notifications_local(notifications):
    '''Store notifications in Blender'''
    bpy.context.window_manager['bkit notifications'] = notifications

def count_all_notifications():
    '''Return count of all notifications on server'''
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    return user_preferences.notifications_counter


def check_notifications_read():
    '''checks if all notifications were already read, and removes them if so'''
    notifications = bpy.context.window_manager.get('bkit notifications')
    if notifications is None or notifications.get('count') == 0:
        return True
    for n in notifications['results']:
        if n['unread'] == 1:
            return False
    bpy.context.window_manager['bkit notifications'] = None
    return True

def get_notifications_thread(api_key, all_count = 1000):
    thread = threading.Thread(target=get_notifications, args=([api_key, all_count]), daemon=True)
    thread.start()

def get_notifications(api_key, all_count = 1000):
    '''
    Retrieve notifications from BlenderKit server. Can be run from a thread.

    Parameters
    ----------
    api_key
    all_count

    Returns
    -------
    '''
    headers = utils.get_headers(api_key)

    params = {}

    url = paths.get_api_url() + 'notifications/all_count/'
    r = rerequests.get(url, params=params, verify=True, headers=headers)
    if r.status_code ==200:
        rj = r.json()
        # print(rj)
        # no new notifications?
        if all_count >= rj['allCount']:
            tasks_queue.add_task((store_notifications_count_local, ([rj['allCount']])))

            return
    url = paths.get_api_url() + 'notifications/unread/'
    r = rerequests.get(url, params=params, verify=True, headers=headers)
    if r is None:
        return
    if r.status_code == 200:
        rj = r.json()
        # store notifications - send them to task queue
        tasks_queue.add_task((store_notifications_local, ([rj])))

def mark_notification_read_thread(api_key, notification_id):
    thread = threading.Thread(target=mark_notification_read, args=([api_key, notification_id]), daemon=True)
    thread.start()

def mark_notification_read(api_key, notification_id):
    '''
    mark notification as read
    '''
    headers = utils.get_headers(api_key)

    url = paths.get_api_url() + f'notifications/mark-as-read/{notification_id}/'
    params = {}
    r = rerequests.get(url, params=params, verify=True, headers=headers)
    if r is None:
        return
    # print(r.text)
    # if r.status_code == 200:
    #     rj = r.json()
    #     # store notifications - send them to task queue
    #     print(rj)
    #     tasks_queue.add_task((mark_notification_read_local, ([notification_id])))

