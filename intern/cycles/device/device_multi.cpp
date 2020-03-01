/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stdlib.h>
#include <sstream>

#include "device/device.h"
#include "device/device_intern.h"
#include "device/device_network.h"

#include "render/buffers.h"

#include "util/util_foreach.h"
#include "util/util_list.h"
#include "util/util_logging.h"
#include "util/util_map.h"
#include "util/util_time.h"

CCL_NAMESPACE_BEGIN

class MultiDevice : public Device {
 public:
  struct SubDevice {
    explicit SubDevice(Device *device_) : device(device_)
    {
    }

    Device *device;
    map<device_ptr, device_ptr> ptr_map;
  };

  list<SubDevice> devices, denoising_devices;
  device_ptr unique_key;

  MultiDevice(DeviceInfo &info, Stats &stats, Profiler &profiler, bool background_)
      : Device(info, stats, profiler, background_), unique_key(1)
  {
    foreach (DeviceInfo &subinfo, info.multi_devices) {
      Device *device = Device::create(subinfo, sub_stats_, profiler, background);

      /* Always add CPU devices at the back since GPU devices can change
       * host memory pointers, which CPU uses as device pointer. */
      if (subinfo.type == DEVICE_CPU) {
        devices.push_back(SubDevice(device));
      }
      else {
        devices.push_front(SubDevice(device));
      }
    }

    foreach (DeviceInfo &subinfo, info.denoising_devices) {
      Device *device = Device::create(subinfo, sub_stats_, profiler, background);

      denoising_devices.push_back(SubDevice(device));
    }

#ifdef WITH_NETWORK
    /* try to add network devices */
    ServerDiscovery discovery(true);
    time_sleep(1.0);

    vector<string> servers = discovery.get_server_list();

    foreach (string &server, servers) {
      Device *device = device_network_create(info, stats, profiler, server.c_str());
      if (device)
        devices.push_back(SubDevice(device));
    }
#endif
  }

  ~MultiDevice()
  {
    foreach (SubDevice &sub, devices)
      delete sub.device;
    foreach (SubDevice &sub, denoising_devices)
      delete sub.device;
  }

  const string &error_message()
  {
    error_msg.clear();

    foreach (SubDevice &sub, devices)
      error_msg += sub.device->error_message();
    foreach (SubDevice &sub, denoising_devices)
      error_msg += sub.device->error_message();

    return error_msg;
  }

  virtual bool show_samples() const
  {
    if (devices.size() > 1) {
      return false;
    }
    return devices.front().device->show_samples();
  }

  virtual BVHLayoutMask get_bvh_layout_mask() const
  {
    BVHLayoutMask bvh_layout_mask = BVH_LAYOUT_ALL;
    foreach (const SubDevice &sub_device, devices) {
      bvh_layout_mask &= sub_device.device->get_bvh_layout_mask();
    }
    return bvh_layout_mask;
  }

  bool load_kernels(const DeviceRequestedFeatures &requested_features)
  {
    foreach (SubDevice &sub, devices)
      if (!sub.device->load_kernels(requested_features))
        return false;

    if (requested_features.use_denoising) {
      foreach (SubDevice &sub, denoising_devices)
        if (!sub.device->load_kernels(requested_features))
          return false;
    }

    return true;
  }

  bool wait_for_availability(const DeviceRequestedFeatures &requested_features)
  {
    foreach (SubDevice &sub, devices)
      if (!sub.device->wait_for_availability(requested_features))
        return false;

    if (requested_features.use_denoising) {
      foreach (SubDevice &sub, denoising_devices)
        if (!sub.device->wait_for_availability(requested_features))
          return false;
    }

    return true;
  }

  DeviceKernelStatus get_active_kernel_switch_state()
  {
    DeviceKernelStatus result = DEVICE_KERNEL_USING_FEATURE_KERNEL;

    foreach (SubDevice &sub, devices) {
      DeviceKernelStatus subresult = sub.device->get_active_kernel_switch_state();
      switch (subresult) {
        case DEVICE_KERNEL_WAITING_FOR_FEATURE_KERNEL:
          result = subresult;
          break;

        case DEVICE_KERNEL_FEATURE_KERNEL_INVALID:
        case DEVICE_KERNEL_FEATURE_KERNEL_AVAILABLE:
          return subresult;

        case DEVICE_KERNEL_USING_FEATURE_KERNEL:
        case DEVICE_KERNEL_UNKNOWN:
          break;
      }
    }

    return result;
  }

  bool build_optix_bvh(BVH *bvh)
  {
    // Broadcast acceleration structure build to all render devices
    foreach (SubDevice &sub, devices)
      if (!sub.device->build_optix_bvh(bvh))
        return false;

    return true;
  }

  void mem_alloc(device_memory &mem)
  {
    device_ptr key = unique_key++;

    foreach (SubDevice &sub, devices) {
      mem.device = sub.device;
      mem.device_pointer = 0;
      mem.device_size = 0;

      sub.device->mem_alloc(mem);
      sub.ptr_map[key] = mem.device_pointer;
    }

    mem.device = this;
    mem.device_pointer = key;
    stats.mem_alloc(mem.device_size);
  }

  void mem_copy_to(device_memory &mem)
  {
    device_ptr existing_key = mem.device_pointer;
    device_ptr key = (existing_key) ? existing_key : unique_key++;
    size_t existing_size = mem.device_size;

    foreach (SubDevice &sub, devices) {
      mem.device = sub.device;
      mem.device_pointer = (existing_key) ? sub.ptr_map[existing_key] : 0;
      mem.device_size = existing_size;

      sub.device->mem_copy_to(mem);
      sub.ptr_map[key] = mem.device_pointer;
    }

    mem.device = this;
    mem.device_pointer = key;
    stats.mem_alloc(mem.device_size - existing_size);
  }

  void mem_copy_from(device_memory &mem, int y, int w, int h, int elem)
  {
    device_ptr key = mem.device_pointer;
    int i = 0, sub_h = h / devices.size();

    foreach (SubDevice &sub, devices) {
      int sy = y + i * sub_h;
      int sh = (i == (int)devices.size() - 1) ? h - sub_h * i : sub_h;

      mem.device = sub.device;
      mem.device_pointer = sub.ptr_map[key];

      sub.device->mem_copy_from(mem, sy, w, sh, elem);
      i++;
    }

    mem.device = this;
    mem.device_pointer = key;
  }

  void mem_zero(device_memory &mem)
  {
    device_ptr existing_key = mem.device_pointer;
    device_ptr key = (existing_key) ? existing_key : unique_key++;
    size_t existing_size = mem.device_size;

    foreach (SubDevice &sub, devices) {
      mem.device = sub.device;
      mem.device_pointer = (existing_key) ? sub.ptr_map[existing_key] : 0;
      mem.device_size = existing_size;

      sub.device->mem_zero(mem);
      sub.ptr_map[key] = mem.device_pointer;
    }

    if (strcmp(mem.name, "RenderBuffers") == 0) {
      foreach (SubDevice &sub, denoising_devices) {
        mem.device = sub.device;
        mem.device_pointer = (existing_key) ? sub.ptr_map[existing_key] : 0;
        mem.device_size = existing_size;

        sub.device->mem_zero(mem);
        sub.ptr_map[key] = mem.device_pointer;
      }
    }

    mem.device = this;
    mem.device_pointer = key;
    stats.mem_alloc(mem.device_size - existing_size);
  }

  void mem_free(device_memory &mem)
  {
    device_ptr key = mem.device_pointer;
    size_t existing_size = mem.device_size;

    foreach (SubDevice &sub, devices) {
      mem.device = sub.device;
      mem.device_pointer = sub.ptr_map[key];
      mem.device_size = existing_size;

      sub.device->mem_free(mem);
      sub.ptr_map.erase(sub.ptr_map.find(key));
    }

    if (strcmp(mem.name, "RenderBuffers") == 0) {
      foreach (SubDevice &sub, denoising_devices) {
        mem.device = sub.device;
        mem.device_pointer = sub.ptr_map[key];
        mem.device_size = existing_size;

        sub.device->mem_free(mem);
        sub.ptr_map.erase(sub.ptr_map.find(key));
      }
    }

    mem.device = this;
    mem.device_pointer = 0;
    mem.device_size = 0;
    stats.mem_free(existing_size);
  }

  void const_copy_to(const char *name, void *host, size_t size)
  {
    foreach (SubDevice &sub, devices)
      sub.device->const_copy_to(name, host, size);
  }

  void draw_pixels(device_memory &rgba,
                   int y,
                   int w,
                   int h,
                   int width,
                   int height,
                   int dx,
                   int dy,
                   int dw,
                   int dh,
                   bool transparent,
                   const DeviceDrawParams &draw_params)
  {
    device_ptr key = rgba.device_pointer;
    int i = 0, sub_h = h / devices.size();
    int sub_height = height / devices.size();

    foreach (SubDevice &sub, devices) {
      int sy = y + i * sub_h;
      int sh = (i == (int)devices.size() - 1) ? h - sub_h * i : sub_h;
      int sheight = (i == (int)devices.size() - 1) ? height - sub_height * i : sub_height;
      int sdy = dy + i * sub_height;
      /* adjust math for w/width */

      rgba.device_pointer = sub.ptr_map[key];
      sub.device->draw_pixels(
          rgba, sy, w, sh, width, sheight, dx, sdy, dw, dh, transparent, draw_params);
      i++;
    }

    rgba.device_pointer = key;
  }

  void map_tile(Device *sub_device, RenderTile &tile)
  {
    if (!tile.buffer) {
      return;
    }

    foreach (SubDevice &sub, devices) {
      if (sub.device == sub_device) {
        tile.buffer = sub.ptr_map[tile.buffer];
        return;
      }
    }

    foreach (SubDevice &sub, denoising_devices) {
      if (sub.device == sub_device) {
        tile.buffer = sub.ptr_map[tile.buffer];
        return;
      }
    }
  }

  int device_number(Device *sub_device)
  {
    int i = 0;

    foreach (SubDevice &sub, devices) {
      if (sub.device == sub_device)
        return i;
      i++;
    }

    foreach (SubDevice &sub, denoising_devices) {
      if (sub.device == sub_device)
        return i;
      i++;
    }

    return -1;
  }

  void map_neighbor_tiles(Device *sub_device, RenderTile *tiles)
  {
    for (int i = 0; i < 9; i++) {
      if (!tiles[i].buffers) {
        continue;
      }

      device_vector<float> &mem = tiles[i].buffers->buffer;
      tiles[i].buffer = mem.device_pointer;

      if (mem.device == this && denoising_devices.empty()) {
        /* Skip unnecessary copies in viewport mode (buffer covers the
         * whole image), but still need to fix up the tile device pointer. */
        map_tile(sub_device, tiles[i]);
        continue;
      }

      /* If the tile was rendered on another device, copy its memory to
       * to the current device now, for the duration of the denoising task.
       * Note that this temporarily modifies the RenderBuffers and calls
       * the device, so this function is not thread safe. */
      if (mem.device != sub_device) {
        /* Only copy from device to host once. This is faster, but
         * also required for the case where a CPU thread is denoising
         * a tile rendered on the GPU. In that case we have to avoid
         * overwriting the buffer being de-noised by the CPU thread. */
        if (!tiles[i].buffers->map_neighbor_copied) {
          tiles[i].buffers->map_neighbor_copied = true;
          mem.copy_from_device();
        }

        if (mem.device == this) {
          /* Can re-use memory if tile is already allocated on the sub device. */
          map_tile(sub_device, tiles[i]);
          mem.swap_device(sub_device, mem.device_size, tiles[i].buffer);
        }
        else {
          mem.swap_device(sub_device, 0, 0);
        }

        mem.copy_to_device();

        tiles[i].buffer = mem.device_pointer;
        tiles[i].device_size = mem.device_size;

        mem.restore_device();
      }
    }
  }

  void unmap_neighbor_tiles(Device *sub_device, RenderTile *tiles)
  {
    device_vector<float> &mem = tiles[9].buffers->buffer;

    if (mem.device == this && denoising_devices.empty()) {
      return;
    }

    /* Copy denoised result back to the host. */
    mem.swap_device(sub_device, tiles[9].device_size, tiles[9].buffer);
    mem.copy_from_device();
    mem.restore_device();

    /* Copy denoised result to the original device. */
    mem.copy_to_device();

    for (int i = 0; i < 9; i++) {
      if (!tiles[i].buffers) {
        continue;
      }

      device_vector<float> &mem = tiles[i].buffers->buffer;

      if (mem.device != sub_device && mem.device != this) {
        /* Free up memory again if it was allocated for the copy above. */
        mem.swap_device(sub_device, tiles[i].device_size, tiles[i].buffer);
        sub_device->mem_free(mem);
        mem.restore_device();
      }
    }
  }

  int get_split_task_count(DeviceTask &task)
  {
    int total_tasks = 0;
    list<DeviceTask> tasks;
    task.split(tasks, devices.size());
    foreach (SubDevice &sub, devices) {
      if (!tasks.empty()) {
        DeviceTask subtask = tasks.front();
        tasks.pop_front();

        total_tasks += sub.device->get_split_task_count(subtask);
      }
    }
    return total_tasks;
  }

  void task_add(DeviceTask &task)
  {
    list<SubDevice> task_devices = devices;
    if (!denoising_devices.empty()) {
      if (task.type == DeviceTask::DENOISE_BUFFER) {
        /* Denoising tasks should be redirected to the denoising devices entirely. */
        task_devices = denoising_devices;
      }
      else if (task.type == DeviceTask::RENDER && (task.tile_types & RenderTile::DENOISE)) {
        const uint tile_types = task.tile_types;
        /* For normal rendering tasks only redirect the denoising part to the denoising devices.
         * Do not need to split the task here, since they all run through 'acquire_tile'. */
        task.tile_types = RenderTile::DENOISE;
        foreach (SubDevice &sub, denoising_devices) {
          sub.device->task_add(task);
        }
        /* Rendering itself should still be executed on the rendering devices. */
        task.tile_types = tile_types ^ RenderTile::DENOISE;
      }
    }

    list<DeviceTask> tasks;
    task.split(tasks, task_devices.size());

    foreach (SubDevice &sub, task_devices) {
      if (!tasks.empty()) {
        DeviceTask subtask = tasks.front();
        tasks.pop_front();

        if (task.buffer)
          subtask.buffer = sub.ptr_map[task.buffer];
        if (task.rgba_byte)
          subtask.rgba_byte = sub.ptr_map[task.rgba_byte];
        if (task.rgba_half)
          subtask.rgba_half = sub.ptr_map[task.rgba_half];
        if (task.shader_input)
          subtask.shader_input = sub.ptr_map[task.shader_input];
        if (task.shader_output)
          subtask.shader_output = sub.ptr_map[task.shader_output];

        sub.device->task_add(subtask);
      }
    }
  }

  void task_wait()
  {
    foreach (SubDevice &sub, devices)
      sub.device->task_wait();
    foreach (SubDevice &sub, denoising_devices)
      sub.device->task_wait();
  }

  void task_cancel()
  {
    foreach (SubDevice &sub, devices)
      sub.device->task_cancel();
    foreach (SubDevice &sub, denoising_devices)
      sub.device->task_cancel();
  }

 protected:
  Stats sub_stats_;
};

Device *device_multi_create(DeviceInfo &info, Stats &stats, Profiler &profiler, bool background)
{
  return new MultiDevice(info, stats, profiler, background);
}

CCL_NAMESPACE_END
