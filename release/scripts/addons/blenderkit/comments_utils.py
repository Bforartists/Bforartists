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
    print(dir(r))
    print(r.text)
    # except requests.exceptions.RequestException as e:
    #     print('ratings upload failed: %s' % str(e))


def upload_comment_flag_thread(url, comment_id='', flag='like', api_key=None):
    ''' Upload rating thread function / disconnected from blender data.'''
    headers = utils.get_headers(api_key)

    bk_logger.debug('upload comment flag' + str(comment_id))

    # rating_url = url + rating_name + '/'
    data = {
        "comment": comment_id,
        "flag": flag,
    }

    # try:
    r = rerequests.post(url, data=data, verify=True, headers=headers)
    print(r)
    print(dir(r))
    print(r.text)
    # except requests.exceptions.RequestException as e:
    #     print('ratings upload failed: %s' % str(e))


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
    if r.status_code == 200:
        rj = r.json()
        comments = []
        # store comments - send them to task queue

        tasks_queue.add_task((store_comments_local, (asset_id, rj['results'])))

        # if len(rj['results'])==0:
        #     # store empty ratings too, so that server isn't checked repeatedly
        #     tasks_queue.add_task((store_rating_local_empty,(asset_id,)))
        # return ratings

def store_notifications_local(notifications):
    bpy.context.window_manager['bkit notifications'] = notifications

def count_unread_notifications():
    notifications = bpy.context.window_manager.get('bkit notifications')
    if notifications is None:
        return 0
    unread = 0
    for n in notifications:
        
        if n['unread'] == 1:
            unread +=1
    print('counted', unread)
    return unread

def check_notifications_read():
    '''checks if all notifications were already read, and removes them if so'''
    notifications = bpy.context.window_manager.get('bkit notifications')
    if notifications is None:
        return True
    for n in notifications:
        if n['unread'] == 1:
            return False
    bpy.context.window_manager['bkit notifications'] = None
    return True

def get_notifications(api_key, unread_count = 1000):
    '''
    Retrieve notifications from BlenderKit server. Can be run from a thread.

    Parameters
    ----------
    api_key
    unread_count

    Returns
    -------
    '''
    headers = utils.get_headers(api_key)

    params = {}

    url = paths.get_api_url() + 'notifications/api/unread_count/'
    r = rerequests.get(url, params=params, verify=True, headers=headers)
    if r.status_code ==200:
        rj = r.json()
        # no new notifications?
        if unread_count >= rj['unreadCount']:
            return
    print('notifications', unread_count, rj['unreadCount'])
    url = paths.get_api_url() + 'notifications/unread/'
    r = rerequests.get(url, params=params, verify=True, headers=headers)
    if r is None:
        return
    if r.status_code == 200:
        rj = r.json()
        # store notifications - send them to task queue
        tasks_queue.add_task((store_notifications_local, ([rj])))


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
    # if r.status_code == 200:
    #     rj = r.json()
    #     # store notifications - send them to task queue
    #     print(rj)
    #     tasks_queue.add_task((mark_notification_read_local, ([notification_id])))

