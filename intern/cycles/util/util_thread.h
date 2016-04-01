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

#if (__cplusplus > 199711L) || (defined(_MSC_VER) && _MSC_VER >= 1800)
#  include <thread>
#  include <mutex>
#  include <condition_variable>
#  include <functional>
#else
#  include <boost/thread.hpp>
#endif
#include <pthread.h>
#include <queue>

#ifdef __APPLE__
#  include <libkern/OSAtomic.h>
#endif

#include "util_function.h"

CCL_NAMESPACE_BEGIN

#if (__cplusplus > 199711L) || (defined(_MSC_VER) && _MSC_VER >= 1800)
typedef std::mutex thread_mutex;
typedef std::unique_lock<std::mutex> thread_scoped_lock;
typedef std::condition_variable thread_condition_variable;
#else
/* use boost for mutexes */
typedef boost::mutex thread_mutex;
typedef boost::mutex::scoped_lock thread_scoped_lock;
typedef boost::condition_variable thread_condition_variable;
#endif

/* own pthread based implementation, to avoid boost version conflicts with
 * dynamically loaded blender plugins */

class thread {
public:
	thread(function<void(void)> run_cb_)

	{
		joined = false;
		run_cb = run_cb_;

		pthread_create(&pthread_id, NULL, run, (void*)this);
	}

	~thread()
	{
		if(!joined)
			join();
	}

	static void *run(void *arg)
	{
		((thread*)arg)->run_cb();
		return NULL;
	}

	bool join()
	{
		joined = true;
		return pthread_join(pthread_id, NULL) == 0;
	}

protected:
	function<void(void)> run_cb;
	pthread_t pthread_id;
	bool joined;
};

/* Own wrapper around pthread's spin lock to make it's use easier. */

class thread_spin_lock {
public:
#ifdef __APPLE__
	inline thread_spin_lock() {
		spin_ = OS_SPINLOCK_INIT;
	}

	inline void lock() {
		OSSpinLockLock(&spin_);
	}

	inline void unlock() {
		OSSpinLockUnlock(&spin_);
	}
#else  /* __APPLE__ */
	inline thread_spin_lock() {
		pthread_spin_init(&spin_, 0);
	}

	inline ~thread_spin_lock() {
		pthread_spin_destroy(&spin_);
	}

	inline void lock() {
		pthread_spin_lock(&spin_);
	}

	inline void unlock() {
		pthread_spin_unlock(&spin_);
	}
#endif  /* __APPLE__ */
protected:
#ifdef __APPLE__
	OSSpinLock spin_;
#else
	pthread_spinlock_t spin_;
#endif
};

CCL_NAMESPACE_END

#endif /* __UTIL_THREAD_H__ */

