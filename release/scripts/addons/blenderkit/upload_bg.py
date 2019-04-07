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

import sys, json, os, time
import requests
import logging

import bpy
import addon_utils
from blenderkit import paths, append_link, bg_blender

BLENDERKIT_EXPORT_DATA = sys.argv[-1]


def start_logging():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def print_gap():
    print('\n\n\n\n')


class upload_in_chunks(object):
    def __init__(self, filename, chunksize=1 << 13, report_name='file'):
        self.filename = filename
        self.chunksize = chunksize
        self.totalsize = os.path.getsize(filename)
        self.readsofar = 0
        self.report_name = report_name

    def __iter__(self):
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.chunksize)
                if not data:
                    sys.stderr.write("\n")
                    break
                self.readsofar += len(data)
                percent = self.readsofar * 1e2 / self.totalsize
                bg_blender.progress('uploading %s' % self.report_name, percent)
                # sys.stderr.write("\r{percent:3.0f}%".format(percent=percent))
                yield data

    def __len__(self):
        return self.totalsize


def upload_files(filepath, upload_data, files):
    headers = {"accept": "application/json", "Authorization": "Bearer %s" % upload_data['token']}
    version_id = upload_data['id']
    for f in files:
        bg_blender.progress('uploading %s' % f['type'])
        upload_info = {
            'assetId': version_id,
            'fileType': f['type'],
            'fileIndex': f['index'],
            'originalFilename': os.path.basename(f['file_path'])
        }
        upload_create_url = paths.get_bkit_url() + 'uploads/'
        upload = requests.post(upload_create_url, json=upload_info, headers=headers, verify=True)
        upload = upload.json()

        upheaders = {
            "accept": "application/json",
            "Authorization": "Bearer %s" % upload_data['token'],
            "Content-Type": "multipart/form-data",
            "Content-Disposition": 'form-data; name="file"; filename=%s' % f['file_path']

        }
        chunk_size = 1024 * 256

        # file gets uploaded here:
        uploaded = False
        # s3 upload is now the only option
        for a in range(0, 20):
            if not uploaded:
                try:
                    upload_response = requests.put(upload['s3UploadUrl'],
                                                   data=upload_in_chunks(f['file_path'], chunk_size, f['type']),
                                                   stream=True, verify=True)
                    # print('upload response')
                    # print(upload_response.text)
                    uploaded = True
                except Exception as e:
                    bg_blender.progress('Upload %s failed, retrying' % f['type'])
                    time.sleep(1)

                # confirm single file upload to bkit server
                upload_done_url = paths.get_bkit_url() + 'uploads_s3/' + upload['id'] + '/upload-file/'
                upload_response = requests.post(upload_done_url, headers=headers, verify=True)

        bg_blender.progress('finished uploading')

    return {'FINISHED'}


if __name__ == "__main__":

    bpy.data.scenes.new('upload')
    for s in bpy.data.scenes:
        if s.name != 'upload':
            bpy.data.scenes.remove(s)
    try:
        # bg_blender.progress('preparing scene')
        bg_blender.progress('preparing scene - link objects')
        with open(BLENDERKIT_EXPORT_DATA, 'r') as s:
            data = json.load(s)

            bpy.app.debug_value = data.get('debug_value', 0)
            export_data = data['export_data']
            upload_data = data['upload_data']

            if export_data['type'] == 'MODEL':
                obnames = export_data['models']
                main_source, allobs = append_link.append_objects(file_name=data['source_filepath'],
                                                                 obnames=obnames,
                                                                 rotation=(0, 0, 0))
                g = bpy.data.collections.new(upload_data['name'])
                for o in allobs:
                    g.objects.link(o)
                bpy.context.scene.collection.children.link(g)
            if export_data['type'] == 'SCENE':
                sname = export_data['scene']
                main_source = append_link.append_scene(file_name=data['source_filepath'],
                                                       scenename=sname)
                bpy.data.scenes.remove(bpy.data.scenes['upload'])
                main_source.name = sname
            elif export_data['type'] == 'MATERIAL':
                matname = export_data['material']
                main_source = append_link.append_material(file_name=data['source_filepath'], matname=matname)

            elif export_data['type'] == 'BRUSH':
                brushname = export_data['brush']
                main_source = append_link.append_brush(file_name=data['source_filepath'], brushname=brushname)

        bpy.ops.file.pack_all()

        # TODO fetch asset_id here
        asset_id = main_source.blenderkit.asset_base_id
        main_source.blenderkit.uploading = False

        fpath = os.path.join(data['temp_dir'], asset_id + '.blend')

        bpy.ops.wm.save_as_mainfile(filepath=fpath, compress=True, copy=False)
        os.remove(data['source_filepath'])

        bg_blender.progress('preparing scene - open files')

        files = [{
            "type": "thumbnail",
            "index": 0,
            "file_path": export_data["thumbnail_path"]
        }, {
            "type": "blend",
            "index": 0,
            "file_path": fpath
        }]

        bg_blender.progress('uploading')

        upload_files(fpath, upload_data, files)

        # mark on server as uploaded
        confirm_data = {
            "verificationStatus": "uploaded"
        }

        url = paths.get_bkit_url() + 'assets/'
        headers = {"accept": "application/json", "Authorization": "Bearer %s" % upload_data['token']}
        url += upload_data["id"] + '/'

        r = requests.patch(url, json=confirm_data, headers=headers, verify=True)  # files = files,

        bg_blender.progress('upload finished successfully')


    except Exception as e:
        print(e)
        bg_blender.progress(e)
        sys.exit(1)
