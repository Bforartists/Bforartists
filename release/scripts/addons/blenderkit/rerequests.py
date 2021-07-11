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


from blenderkit import ui, utils, paths, tasks_queue, bkit_oauth

import requests
import bpy
import logging

bk_logger = logging.getLogger('rerequests')


def rerequest(method, url, recursion=0, **kwargs):
    # first get any additional args from kwargs
    immediate = False
    if kwargs.get('immediate'):
        immediate = kwargs['immediate']
        kwargs.pop('immediate')
    # first normal attempt
    try:
        response = requests.request(method, url, **kwargs)
    except Exception as e:
        print(e)
        return None

    bk_logger.debug(url + str(kwargs))
    bk_logger.debug(response.status_code)

    if response.status_code == 401:
        try:
            rdata = response.json()
        except:
            rdata = {}

        tasks_queue.add_task((ui.add_report, (method + ' request Failed.' + str(rdata.get('detail')),)))

        if rdata.get('detail') == 'Invalid token.':
            user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
            if user_preferences.api_key != '':
                if user_preferences.enable_oauth and user_preferences.api_key_refresh != '':
                    tasks_queue.add_task((ui.add_report, (
                        'refreshing token. If this fails, please login in BlenderKit Login panel.', 10)))
                    refresh_url = paths.get_bkit_url()
                    auth_token, refresh_token, oauth_response = bkit_oauth.refresh_token(
                        user_preferences.api_key_refresh, refresh_url)

                    # bk_logger.debug(auth_token, refresh_token)
                    if auth_token is not None:
                        if immediate == True:
                            # this can write tokens occasionally into prefs. used e.g. in upload. Only possible
                            #  in non-threaded tasks
                            bpy.context.preferences.addons['blenderkit'].preferences.api_key = auth_token
                            bpy.context.preferences.addons['blenderkit'].preferences.api_key_refresh = refresh_token
                        else:
                            tasks_queue.add_task((bkit_oauth.write_tokens, (auth_token, refresh_token, oauth_response)))

                        kwargs['headers'] = utils.get_headers(auth_token)
                        response = requests.request(method, url, **kwargs)
                        bk_logger.debug('reresult', response.status_code)
                        if response.status_code >= 400:
                            bk_logger.debug('reresult', response.text)
                            tasks_queue.add_task((ui.add_report, (
                                response.text, 10)))

                    else:
                        tasks_queue.add_task((ui.add_report, (
                            'Refreshing token failed.Please login manually.', 10)))
                        # tasks_queue.add_task((bkit_oauth.write_tokens, ('', '', '')))
                        tasks_queue.add_task((bpy.ops.wm.blenderkit_login, ('INVOKE_DEFAULT',)), fake_context=True)
    return response


def get(url, **kwargs):
    response = rerequest('get', url, **kwargs)
    return response


def post(url, **kwargs):
    response = rerequest('post', url, **kwargs)
    return response


def put(url, **kwargs):
    response = rerequest('put', url, **kwargs)
    return response


def patch(url, **kwargs):
    response = rerequest('patch', url, **kwargs)
    return response
