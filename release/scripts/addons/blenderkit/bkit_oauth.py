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


from blenderkit import tasks_queue, utils, paths, search, categories, oauth, ui, ui_panels

import bpy

import threading
import requests
import time
import logging
bk_logger = logging.getLogger('blenderkit')

from bpy.props import (
    BoolProperty,
)

CLIENT_ID = "IdFRwa3SGA8eMpzhRVFMg5Ts8sPK93xBjif93x0F"
PORTS = [62485, 65425, 55428, 49452]

active_authenticator = None


def login_thread(signup=False):
    global active_authenticator
    r_url = paths.get_oauth_landing_url()
    url = paths.get_bkit_url()
    authenticator = oauth.SimpleOAuthAuthenticator(server_url=url, client_id=CLIENT_ID, ports=PORTS)
    # we store authenticator globally to be able to ping the server if connection fails.
    active_authenticator = authenticator
    thread = threading.Thread(target=login, args=([signup, url, r_url, authenticator]), daemon=True)
    thread.start()


def login(signup, url, r_url, authenticator):
    auth_token, refresh_token, oauth_response = authenticator.get_new_token(register=signup, redirect_url=r_url)
    bk_logger.debug('tokens retrieved')
    tasks_queue.add_task((write_tokens, (auth_token, refresh_token, oauth_response)))


def refresh_token_thread():
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if len(preferences.api_key_refresh) > 0 and preferences.refresh_in_progress == False:
        preferences.refresh_in_progress = True
        url = paths.get_bkit_url()
        thread = threading.Thread(target=refresh_token, args=([preferences.api_key_refresh, url]), daemon=True)
        thread.start()
    else:
        ui.add_report('Already Refreshing token, will be ready soon. If this fails, please login again in Login panel.')


def refresh_token(api_key_refresh, url):
    authenticator = oauth.SimpleOAuthAuthenticator(server_url=url, client_id=CLIENT_ID, ports=PORTS)
    auth_token, refresh_token, oauth_response = authenticator.get_refreshed_token(api_key_refresh)
    if auth_token is not None and refresh_token is not None:
        tasks_queue.add_task((write_tokens, (auth_token, refresh_token, oauth_response)))
    return auth_token, refresh_token, oauth_response


def write_tokens(auth_token, refresh_token, oauth_response):
    bk_logger.debug('writing tokens')
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    preferences.api_key_refresh = refresh_token
    preferences.api_key = auth_token
    preferences.api_key_timeout = time.time() + oauth_response['expires_in']
    preferences.api_key_life = oauth_response['expires_in']
    preferences.login_attempt = False
    preferences.refresh_in_progress = False
    props = utils.get_search_props()
    if props is not None:
        props.report = ''
    ui.add_report('BlenderKit Re-Login success')
    search.get_profile()
    categories.fetch_categories_thread(auth_token, force = False)


class RegisterLoginOnline(bpy.types.Operator):
    """Login online on BlenderKit webpage"""

    bl_idname = "wm.blenderkit_login"
    bl_label = "BlenderKit login/signup"
    bl_options = {'REGISTER', 'UNDO'}

    signup: BoolProperty(
        name="create a new account",
        description="True for register, otherwise login",
        default=False,
        options={'SKIP_SAVE'}
    )

    message: bpy.props.StringProperty(
        name="Message",
        description="",
        default="You were logged out from BlenderKit.\n Clicking OK takes you to web login. ")

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        utils.label_multiline(layout, text=self.message, width = 300)

    def execute(self, context):
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        preferences.login_attempt = True
        login_thread(self.signup)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = bpy.context.window_manager
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        preferences.api_key_refresh = ''
        preferences.api_key = ''
        return wm.invoke_props_dialog(self)


class Logout(bpy.types.Operator):
    """Logout from BlenderKit immediately"""

    bl_idname = "wm.blenderkit_logout"
    bl_label = "BlenderKit logout"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        preferences.login_attempt = False
        preferences.api_key_refresh = ''
        preferences.api_key = ''
        if bpy.context.window_manager.get('bkit profile'):
            del (bpy.context.window_manager['bkit profile'])
        return {'FINISHED'}


class CancelLoginOnline(bpy.types.Operator):
    """Cancel login attempt"""

    bl_idname = "wm.blenderkit_login_cancel"
    bl_label = "BlenderKit login cancel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global active_authenticator
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        preferences.login_attempt = False
        try:
            if active_authenticator is not None:
                requests.get(active_authenticator.redirect_uri)
                active_authenticator = None
        except Exception as e:
            print('stopped login attempt')
            print(e)
        return {'FINISHED'}


classes = (
    RegisterLoginOnline,
    CancelLoginOnline,
    Logout,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
