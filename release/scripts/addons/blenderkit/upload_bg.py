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


if "bpy" in locals():
    from importlib import reload

    paths = reload(paths)
    append_link = reload(append_link)
    bg_blender = reload(bg_blender)
    utils = reload(utils)
    rerequests = reload(rerequests)
else:
    from blenderkit import paths, append_link, bg_blender, utils, rerequests

import sys, json, os, time
import requests
import logging

import bpy

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


def upload_file(upload_data, f):
    headers = utils.get_headers(upload_data['token'])
    version_id = upload_data['id']
    bg_blender.progress('uploading %s' % f['type'])
    upload_info = {
        'assetId': version_id,
        'fileType': f['type'],
        'fileIndex': f['index'],
        'originalFilename': os.path.basename(f['file_path'])
    }
    upload_create_url = paths.get_api_url() + 'uploads/'
    upload = rerequests.post(upload_create_url, json=upload_info, headers=headers, verify=True)
    upload = upload.json()
    #
    chunk_size = 1024 * 1024 * 2
    utils.pprint(upload)
    # file gets uploaded here:
    uploaded = False
    # s3 upload is now the only option
    for a in range(0, 5):
        if not uploaded:
            try:
                upload_response = requests.put(upload['s3UploadUrl'],
                                               data=upload_in_chunks(f['file_path'], chunk_size, f['type']),
                                               stream=True, verify=True)

                if upload_response.status_code == 200:
                    uploaded = True
                else:
                    print(upload_response.text)
                    bg_blender.progress(f'Upload failed, retry. {a}')
            except Exception as e:
                print(e)
                bg_blender.progress('Upload %s failed, retrying' % f['type'])
                time.sleep(1)

            # confirm single file upload to bkit server
            upload_done_url = paths.get_api_url() + 'uploads_s3/' + upload['id'] + '/upload-file/'
            upload_response = rerequests.post(upload_done_url, headers=headers, verify=True)

    bg_blender.progress('finished uploading')

    return uploaded


def upload_files(upload_data, files):
    uploaded_all = True
    for f in files:
        uploaded = upload_file(upload_data, f)
        if not uploaded:
            uploaded_all = False
        bg_blender.progress('finished uploading')
    return uploaded_all


if __name__ == "__main__":


    try:
        bg_blender.progress('preparing scene - append data')
        with open(BLENDERKIT_EXPORT_DATA, 'r') as s:
            data = json.load(s)

        bpy.app.debug_value = data.get('debug_value', 0)
        export_data = data['export_data']
        upload_data = data['upload_data']

        upload_set = data['upload_set']
        if 'MAINFILE' in upload_set:
            bpy.data.scenes.new('upload')
            for s in bpy.data.scenes:
                if s.name != 'upload':
                    bpy.data.scenes.remove(s)

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

            main_source.blenderkit.uploading = False
            fpath = os.path.join(data['temp_dir'], upload_data['assetBaseId'] + '.blend')

            bpy.ops.wm.save_as_mainfile(filepath=fpath, compress=True, copy=False)
            os.remove(data['source_filepath'])

        bg_blender.progress('preparing scene - open files')

        files = []
        if 'THUMBNAIL' in upload_set:
            files.append({
                "type": "thumbnail",
                "index": 0,
                "file_path": export_data["thumbnail_path"]
            })
        if 'MAINFILE' in upload_set:
            files.append({
                "type": "blend",
                "index": 0,
                "file_path": fpath
            })

        bg_blender.progress('uploading')

        uploaded = upload_files(upload_data, files)

        if uploaded:
            # mark on server as uploaded
            if 'MAINFILE' in upload_set:
                confirm_data = {
                    "verificationStatus": "uploaded"
                }

                url = paths.get_api_url() + 'assets/'

                headers = utils.get_headers(upload_data['token'])

                url += upload_data["id"] + '/'

                r = rerequests.patch(url, json=confirm_data, headers=headers, verify=True)  # files = files,

            bg_blender.progress('upload finished successfully')
        else:
            bg_blender.progress('upload failed.')

    except Exception as e:
        print(e)
        bg_blender.progress(e)
        sys.exit(1)
