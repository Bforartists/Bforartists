# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import urllib.request
import urllib.parse
import zipfile
from pathlib import Path

def unzip(zip_path, extract_dir_path):
    '''Get a zip path and a directory path to extract to'''
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir_path)

def simple_dl_url(url, dest, fallback_url=None):
    ## need to import urlib.request or linux module does not found 'request' using urllib directly
    ## need to create an SSl context or linux fail returning unverified ssl
    # ssl._create_default_https_context = ssl._create_unverified_context

    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print('Error trying to download\n', e)
        if fallback_url:
            print('\nDownload page for manual install:', fallback_url)
        return e

def get_brushes(blend_fp):
    cur_brushes = [b.name for b in bpy.data.brushes]
    with bpy.data.libraries.load(str(blend_fp), link=False) as (data_from, data_to):
        # load brushes starting with 'tex' prefix if there are not already there
        data_to.brushes = [b for b in data_from.brushes if b.startswith('tex_') and not b in cur_brushes]
        # Add holdout
        if 'z_holdout' in data_from.brushes and not 'z_holdout' in cur_brushes:
            data_to.brushes.append('z_holdout')

    ## force fake user for the brushes
    for b in data_to.brushes:
        b.use_fake_user = True

    return len(data_to.brushes)

class GP_OT_install_brush_pack(bpy.types.Operator):
    bl_idname = "gp.import_brush_pack"
    bl_label = "Download and import texture brush pack"
    bl_description = "Download and import Grease Pencil brush pack from the web (~3.7 Mo)"
    bl_options = {"REGISTER", "INTERNAL"}

    # @classmethod
    # def poll(cls, context):
    #     return True

    def _append_brushes(self, blend_fp):
        bct = get_brushes(blend_fp)
        if bct:
            self.report({'INFO'}, f'{bct} brushes installed')
        else:
            self.report({'WARNING'}, 'Brushes already loaded')

    def _install_from_zip(self):
        ## get blend file name
        blendname = None
        with zipfile.ZipFile(self.brushzip, 'r') as zfd:
            for f in zfd.namelist():
                if f.endswith('.blend'):
                    blendname = f
                    break
        if not blendname:
            self.report({'ERROR'}, f'blend file not found in zip {self.brushzip}')
            return

        unzip(self.brushzip, self.temp)

        self._append_brushes(Path(self.temp) / blendname)

    def execute(self, context):
        import ssl
        import tempfile
        import os

        temp = tempfile.gettempdir()
        if not temp:
            self.report({'ERROR'}, 'no os temporary directory found to download brush pack (using python tempfile.gettempdir())')
            return {"CANCELLED"}

        self.temp = Path(temp)

        dl_url = 'https://download.blender.org/demo/bundles/bundles-3.0/grease-pencil-brush-pack.zip'

        ## need to create an SSl context or linux fail and raise unverified ssl
        ssl._create_default_https_context = ssl._create_unverified_context

        file_size = None

        try:
            with urllib.request.urlopen(dl_url) as response:
                file_size = int(response.getheader('Content-Length'))
        except:
            ## try loading from tempdir
            packs = [f for f in os.listdir(self.temp) if 'gp_brush_pack' in f.lower() and f.endswith('.blend')]
            if packs:
                packs.sort()
                self._append_brushes(Path(self.temp) / packs[-1])
                self.report({'WARNING'}, 'Brushes loaded from temp directory (No download)')
                return {"FINISHED"}

            self.report({'ERROR'}, f'Check your internet connection, impossible to connect to url: {dl_url}')
            return {"CANCELLED"}

        if file_size is None:
            self.report({'ERROR'}, f'No response read from: {dl_url}')
            return {"CANCELLED"}

        self.brushzip = self.temp / Path(dl_url).name

        ### Load existing files instead of redownloading if exists and up to date (same hash)
        if self.brushzip.exists():

            ### compare using file size with size from url header
            disk_size = self.brushzip.stat().st_size
            if disk_size == file_size:
                ## is up to date, install
                print(f'{self.brushzip} is up do date, appending brushes')
                self._install_from_zip()
                return {"FINISHED"}

        ## Download, unzip, use blend
        print(f'Downloading brushpack in {self.brushzip}')

        fallback_url='https://cloud.blender.org/p/gallery/5f235cc297f8815e74ffb90b'
        err = simple_dl_url(dl_url, str(self.brushzip), fallback_url)

        if err:
            self.report({'ERROR'}, 'Could not download brush pack. Check your internet connection. (see console for detail)')
            return {"CANCELLED"}
        else:
            print('Done')
        self._install_from_zip()
        return {"FINISHED"}


def register():
    bpy.utils.register_class(GP_OT_install_brush_pack)

def unregister():
    bpy.utils.unregister_class(GP_OT_install_brush_pack)
