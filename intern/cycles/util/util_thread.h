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

#ifndef __UTIL_THREAD_H__
#define __UTIL_THREAD_H__

#include <condition_variable>
#include <functional>
#include <mutex>
#include <queue>
#include <thread>

#ifdef _WIN32
#  include "util_windows.h"
#else
#  include <pthread.h>
#endif

#ifdef __APPLE__
#  include <libkern/OSAtomic.h>
#endif

#include "util/util_function.h"

CCL_NAMESPACE_BEGIN

typedef std::mutex thread_mutex;
typedef std::unique_lock<std::mutex> thread_scoped_lock;
typedef std::condition_variable thread_condition_variable;

/* Own thread implementation similar to std::thread, so we can set a
 * custom stack size on macOS. */

class thread {
 public:
  /* NOTE: Node index of -1 means that affinity will be inherited from the
   * parent thread and no override on top of that will happen. */
  thread(function<void()> run_cb, int node = -1);
  ~thread();

  static void *run(void *arg);
  bool join();

 protected:
  function<void()> run_cb_;
#ifdef __APPLE__
  pthread_t pthread_id;
#else
  std::thread std_thread;
#endif
  bool joined_;
  int node_;
};

/* Own wrapper around pthread's spin lock to make it's use easier. */

class thread_spin_lock {
 public:
#ifdef __APPLE__
  inline thread_spin_lock()
  {
    spin_ = OS_SPINLOCK_INIT;
  }

  inline void lock()
  {
    OSSpinLockLock(&spin_);
  }

  inline void unlock()
  {
    OSSpinLockUnlock(&spin_);
  }
#elif defined(_WIN32)
  inline thread_spin_lock()
  {
    const DWORD SPIN_COUNT = 50000;
    InitializeCriticalSectionAndSpinCount(&cs_, SPIN_COUNT);
  }

  inline ~thread_spin_lock()
  {
    DeleteCriticalSection(&cs_);
  }

  inline void lock()
  {
    EnterCriticalSection(&cs_);
  }

  inline void unlock()
  {
    LeaveCriticalSection(&cs_);
  }
#else
  inline thread_spin_lock()
  {
    pthread_spin_init(&spin_, 0);
  }

  inline ~thread_spin_lock()
  {
    pthread_spin_destroy(&spin_);
  }

  inline void lock()
  {
    pthread_spin_lock(&spin_);
  }

  inline void unlock()
  {
    pthread_spin_unlock(&spin_);
  }
#endif
 protected:
#ifdef __APPLE__
  OSSpinLock spin_;
#elif defined(_WIN32)
  CRITICAL_SECTION cs_;
#else
  pthread_spinlock_t spin_;
#endif
};

class thread_scoped_spin_lock {
 public:
  explicit thread_scoped_spin_lock(thread_spin_lock &lock) : lock_(lock)
  {
    lock_.lock();
  }

  ~thread_scoped_spin_lock()
  {
    lock_.unlock();
  }

  /* TODO(sergey): Implement manual control over lock/unlock. */

 protected:
  thread_spin_lock &lock_;
};

CCL_NAMESPACE_END

#endif /* __UTIL_THREAD_H__ */
