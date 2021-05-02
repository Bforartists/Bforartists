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



from blenderkit import paths, append_link, bg_blender, utils, rerequests, tasks_queue, ui

import sys, json, os, time
import requests
import logging

import bpy

BLENDERKIT_EXPORT_DATA = sys.argv[-1]


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
                tasks_queue.add_task((ui.add_report, (f"Uploading {self.report_name} {percent}%",)))

                # bg_blender.progress('uploading %s' % self.report_name, percent)
                # sys.stderr.write("\r{percent:3.0f}%".format(percent=percent))
                yield data

    def __len__(self):
        return self.totalsize


def upload_file(upload_data, f):
    headers = utils.get_headers(upload_data['token'])
    version_id = upload_data['id']

    message = f"uploading {f['type']} {os.path.basename(f['file_path'])}"
    tasks_queue.add_task((ui.add_report, (message,)))

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
    # utils.pprint(upload)
    # file gets uploaded here:
    uploaded = False
    # s3 upload is now the only option
    for a in range(0, 5):
        if not uploaded:
            try:
                upload_response = requests.put(upload['s3UploadUrl'],
                                               data=upload_in_chunks(f['file_path'], chunk_size, f['type']),
                                               stream=True, verify=True)

                if 250 > upload_response.status_code > 199:
                    uploaded = True
                    upload_done_url = paths.get_api_url() + 'uploads_s3/' + upload['id'] + '/upload-file/'
                    upload_response = rerequests.post(upload_done_url, headers=headers, verify=True)
                    # print(upload_response)
                    # print(upload_response.text)
                    tasks_queue.add_task((ui.add_report, (f"Finished file upload: {os.path.basename(f['file_path'])}",)))
                    return True
                else:
                    print(upload_response.text)
                    message = f"Upload failed, retry. File : {f['type']} {os.path.basename(f['file_path'])}"
                    tasks_queue.add_task((ui.add_report, (message,)))

            except Exception as e:
                print(e)
                message = f"Upload failed, retry. File : {f['type']} {os.path.basename(f['file_path'])}"
                tasks_queue.add_task((ui.add_report, (message,)))
                time.sleep(1)

            # confirm single file upload to bkit server




    return False


def upload_files(upload_data, files):
    '''uploads several files in one run'''
    uploaded_all = True
    for f in files:
        uploaded = upload_file(upload_data, f)
        if not uploaded:
            uploaded_all = False
        tasks_queue.add_task((ui.add_report, (f"Uploaded all files for asset {upload_data['name']}",)))
    return uploaded_all


if __name__ == "__main__":
    try:
        # bg_blender.progress('preparing scene - append data')
        with open(BLENDERKIT_EXPORT_DATA, 'r',encoding='utf-8') as s:
            data = json.load(s)

        bpy.app.debug_value = data.get('debug_value', 0)
        export_data = data['export_data']
        upload_data = data['upload_data']

        bpy.data.scenes.new('upload')
        for s in bpy.data.scenes:
            if s.name != 'upload':
                bpy.data.scenes.remove(s)

        if upload_data['assetType'] == 'model':
            obnames = export_data['models']
            main_source, allobs = append_link.append_objects(file_name=export_data['source_filepath'],
                                                             obnames=obnames,
                                                             rotation=(0, 0, 0))
            g = bpy.data.collections.new(upload_data['name'])
            for o in allobs:
                g.objects.link(o)
            bpy.context.scene.collection.children.link(g)
        elif upload_data['assetType'] == 'scene':
            sname = export_data['scene']
            main_source = append_link.append_scene(file_name=export_data['source_filepath'],
                                                   scenename=sname)
            bpy.data.scenes.remove(bpy.data.scenes['upload'])
            main_source.name = sname
        elif upload_data['assetType'] == 'material':
            matname = export_data['material']
            main_source = append_link.append_material(file_name=export_data['source_filepath'], matname=matname)

        elif upload_data['assetType'] == 'brush':
            brushname = export_data['brush']
            main_source = append_link.append_brush(file_name=export_data['source_filepath'], brushname=brushname)

        bpy.ops.file.pack_all()

        main_source.blenderkit.uploading = False
        #write ID here.
        main_source.blenderkit.asset_base_id = export_data['assetBaseId']
        main_source.blenderkit.id = export_data['id']

        fpath = os.path.join(export_data['temp_dir'], upload_data['assetBaseId'] + '.blend')

        bpy.ops.wm.save_as_mainfile(filepath=fpath, compress=True, copy=False)
        os.remove(export_data['source_filepath'])


    except Exception as e:
        print(e)
        # bg_blender.progress(e)
        sys.exit(1)
