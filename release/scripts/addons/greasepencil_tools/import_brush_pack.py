import bpy
import re
import ssl
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

def download_url(url, dest):
    '''download passed url to dest file (include filename)'''
    import shutil
    import time
    ssl._create_default_https_context = ssl._create_unverified_context
    start_time = time.time()

    try:
        with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        print('Error trying to download\n', e)
        return e

    print(f"Download time {time.time() - start_time:.2f}s",)


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

        import tempfile
        import json
        import hashlib
        import os

        ## get temp dir
        temp = tempfile.gettempdir()
        if not temp:
            self.report({'ERROR'}, 'no os temporary directory found to download brush pack (using python tempfile.gettempdir())')
            return {"CANCELLED"}

        self.temp = Path(temp)

        ## download link from gitlab
        # brush pack project https://gitlab.com/pepe-school-land/gp-brush-pack
        repo_url = r'https://gitlab.com/api/v4/projects/21994857'
        tree_url = f'{repo_url}/repository/tree'

        ## need to create an SSl context or linux fail and raise unverified ssl
        ssl._create_default_https_context = ssl._create_unverified_context

        try:
            with urllib.request.urlopen(tree_url) as response:
                html = response.read()
        except:
            ## try loading from tempdir
            packs = [f for f in os.listdir(self.temp) if 'GP_brush_pack' in f and f.endswith('.blend')]
            if packs:
                packs.sort()
                self._append_brushes(Path(self.temp) / packs[-1])
                self.report({'WARNING'}, 'Brushes loaded from temp directory (No download)')
                # print('Could not reach web url : Brushes were loaded from temp directory file (No download)')
                return {"FINISHED"}

            self.report({'ERROR'}, f'Check your internet connexion, Impossible to connect to url: {tree_url}')
            return {"CANCELLED"}

        if not html:
            self.report({'ERROR'}, f'No response read from: {tree_url}')
            return {"CANCELLED"}

        tree_dic = json.loads(html)
        zips = [fi for fi in tree_dic if fi['type'] == 'blob' and fi['name'].endswith('.zip')]

        if not zips:
            print(f'no zip file found in {tree_url}')
            return {"CANCELLED"}

        ## sort by name to get last
        zips.sort(key=lambda x: x['name'])
        last_zip = zips[-1]
        zipname = last_zip['name']
        id_num = last_zip['id']


        ## url by filename
        # filepath_encode = urllib.parse.quote(zipname, safe='')# need safe to convert possible '/'
        # dl_url = f'{repo_url}/repository/files/{filepath_encode}/raw?ref=master'

        ## url by blobs
        dl_url = f"{repo_url}/repository/blobs/{id_num}/raw"

        self.brushzip = self.temp / zipname


        ### Load existing files instead of redownloading if exists and up to date (same hash)
        if self.brushzip.exists():
            ### Test the hash against online git hash (check for update)
            BLOCK_SIZE = 524288# 512 Kb buf size
            file_hash = hashlib.sha1()
            file_hash.update(("blob %u\0" % os.path.getsize(self.brushzip)).encode('utf-8'))
            with open(self.brushzip, 'rb') as f:
                fb = f.read(BLOCK_SIZE)
                while len(fb) > 0:
                    file_hash.update(fb)
                    fb = f.read(BLOCK_SIZE)

            if file_hash.hexdigest() == id_num: # same git SHA1
                ## is up to date, install
                print(f'{self.brushzip} is up do date, appending brushes')
                self._install_from_zip()
                return {"FINISHED"}

        ## Download, unzip, use blend
        print(f'Downloading brushpack in {self.brushzip}')
        ## https://cloud.blender.org/p/gallery/5f235cc297f8815e74ffb90b

        fallback_url='https://gitlab.com/pepe-school-land/gp-brush-pack/-/blob/master/Official_GP_brush_pack_v01.zip'
        err = simple_dl_url(dl_url, str(self.brushzip), fallback_url)
        # err = download_url(dl_url, str(self.brushzip), fallback_url)

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
