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


import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests

SERVER_URL = "http://localhost:8001"
# SERVER_URL = "https://devel.blenderkit.com"
CLIENT_ID = "IdFRwa3SGA8eMpzhRVFMg5Ts8sPK93xBjif93x0F"
PORTS = [62485, 1234]


class SimpleOAuthAuthenticator(object):
    def __init__(self, server_url, client_id, ports):
        self.server_url = server_url
        self.client_id = client_id
        self.ports = ports

    def _get_tokens(self, authorization_code=None, refresh_token=None, grant_type="authorization_code"):
        data = {
            "grant_type": grant_type,
            "state": "random_state_string",
            "client_id": self.client_id,
            "scopes": "read write",
        }
        if authorization_code:
            data['code'] = authorization_code
        if refresh_token:
            data['refresh_token'] = refresh_token
        print(data)

        response = requests.post(
            '%s/o/token/' % self.server_url,
            data=data
        )
        print(response.content)
        if response.status_code != 200:
            return None, None
        refresh_token = json.loads(response.content)['refresh_token']
        access_token = json.loads(response.content)['access_token']
        return access_token, refresh_token

    def get_new_token(self):
        class HTTPServerHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                if 'code' in self.path:
                    self.auth_code = self.path.split('=')[1]
                    # Display to the user that they no longer need the browser window
                    self.wfile.write(bytes('<html><h1>You may now close this window.</h1></html>', 'utf-8'))
                    qs = parse_qs(urlparse(self.path).query)
                    self.server.authorization_code = qs['code'][0]

        for port in self.ports:
            print(port)
            try:
                httpServer = HTTPServer(('localhost', port), HTTPServerHandler)
            except OSError:
                continue
            break
        print(port)
        webbrowser.open_new(
            "%s/o/authorize?client_id=%s&state=random_state_string&response_type=code&"
            "redirect_uri=http://localhost:%s/consumer/exchange/" % (self.server_url, self.client_id, port),
        )

        httpServer.handle_request()
        authorization_code = httpServer.authorization_code
        return self._get_tokens(authorization_code=authorization_code)

    def get_refreshed_token(self, refresh_token):
        return self._get_tokens(refresh_token=refresh_token, grant_type="refresh_token")


authenticator = SimpleOAuthAuthenticator(server_url=SERVER_URL, client_id=CLIENT_ID, ports=PORTS)
auth_token, refresh_token = authenticator.get_new_token()
print("auth token: %s, refresh_token: %s" % (auth_token, refresh_token))
auth_token, refresh_token = authenticator.get_refreshed_token(refresh_token)
print("auth_token: %s, new refresh_token: %s" % (auth_token, refresh_token))
