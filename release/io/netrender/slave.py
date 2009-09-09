import sys, os
import http, http.client, http.server, urllib
import subprocess, time

from netrender.utils import *
import netrender.model

CANCEL_POLL_SPEED = 2
MAX_TIMEOUT = 10
INCREMENT_TIMEOUT = 1

def slave_Info():
	sysname, nodename, release, version, machine = os.uname()
	slave = netrender.model.RenderSlave()
	slave.name = nodename
	slave.stats = sysname + " " + release + " " + machine
	return slave

def testCancel(conn, job_id):
		conn.request("HEAD", "status", headers={"job-id":job_id})
		response = conn.getresponse()
		
		# cancelled if job isn't found anymore
		if response.status == http.client.NO_CONTENT:
			return True
		else:
			return False

def testFile(conn, JOB_PREFIX, file_path, main_path = None):
	job_full_path = prefixPath(JOB_PREFIX, file_path, main_path)
	
	if not os.path.exists(job_full_path):
		temp_path = JOB_PREFIX + "slave.temp.blend"
		conn.request("GET", "file", headers={"job-id": job.id, "slave-id":slave_id, "job-file":file_path})
		response = conn.getresponse()
		
		if response.status != http.client.OK:
			return None # file for job not returned by server, need to return an error code to server
		
		f = open(temp_path, "wb")
		buf = response.read(1024)
		
		while buf:
			f.write(buf)
			buf = response.read(1024)
		
		f.close()
		
		os.renames(temp_path, job_full_path)
		
	return job_full_path


def render_slave(engine, scene):
	netsettings = scene.network_render
	timeout = 1
	
	engine.update_stats("", "Network render node initiation")
	
	conn = clientConnection(scene)
	
	if conn:
		conn.request("POST", "slave", repr(slave_Info().serialize()))
		response = conn.getresponse()
		
		slave_id = response.getheader("slave-id")
		
		NODE_PREFIX = netsettings.path + "slave_" + slave_id + os.sep
		if not os.path.exists(NODE_PREFIX):
			os.mkdir(NODE_PREFIX)
	
		while not engine.test_break():
			
			conn.request("GET", "job", headers={"slave-id":slave_id})
			response = conn.getresponse()
			
			if response.status == http.client.OK:
				timeout = 1 # reset timeout on new job
				
				job = netrender.model.RenderJob.materialize(eval(str(response.read(), encoding='utf8')))
				
				JOB_PREFIX = NODE_PREFIX + "job_" + job.id + os.sep
				if not os.path.exists(JOB_PREFIX):
					os.mkdir(JOB_PREFIX)
				
				job_path = job.files[0][0] # data in files have format (path, start, end)
				main_path, main_file = os.path.split(job_path)
				
				job_full_path = testFile(conn, JOB_PREFIX, job_path)
				print("Fullpath", job_full_path)
				print("File:", main_file, "and %i other files" % (len(job.files) - 1,))
				engine.update_stats("", "Render File", main_file, "for job", job.id)
				
				for file_path, start, end in job.files[1:]:
					print("\t", file_path)
					testFile(conn, JOB_PREFIX, file_path, main_path)
				
				frame_args = []
				
				for frame in job.frames:
					print("frame", frame.number)
					frame_args += ["-f", str(frame.number)]
					
				start_t = time.time()
				
				process = subprocess.Popen([sys.argv[0], "-b", job_full_path, "-o", JOB_PREFIX + "######", "-E", "BLENDER_RENDER", "-F", "MULTILAYER"] + frame_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)	
				
				cancelled = False
				stdout = bytes()
				run_t = time.time()
				while process.poll() == None and not cancelled:
					stdout += process.stdout.read(32)
					current_t = time.time()
					cancelled = engine.test_break()
					if current_t - run_t > CANCEL_POLL_SPEED:
						if testCancel(conn, job.id):
							cancelled = True
						else:
							run_t = current_t
				
				if cancelled:
					continue # to next frame
				
				total_t = time.time() - start_t
				
				avg_t = total_t / len(job.frames)
				
				status = process.returncode
				
				print("status", status)
				
				headers = {"job-id":job.id, "slave-id":slave_id, "job-time":str(avg_t)}
				
				if status == 0: # non zero status is error
					headers["job-result"] = str(DONE)
					for frame in job.frames:
						headers["job-frame"] = str(frame.number)
						# send result back to server
						f = open(JOB_PREFIX + "%06d" % frame.number + ".exr", 'rb')
						conn.request("PUT", "render", f, headers=headers)
						f.close()
						response = conn.getresponse()
				else:
					headers["job-result"] = str(ERROR)
					for frame in job.frames:
						headers["job-frame"] = str(frame.number)
						# send error result back to server
						conn.request("PUT", "render", headers=headers)
						response = conn.getresponse()
				
				for frame in job.frames:
					headers["job-frame"] = str(frame.number)
					# send log in any case
					conn.request("PUT", "log", stdout, headers=headers)
					response = conn.getresponse()
			else:
				if timeout < MAX_TIMEOUT:
					timeout += INCREMENT_TIMEOUT
				
				for i in range(timeout):
					time.sleep(1)
					if engine.test_break():
						conn.close()
						return
			
		conn.close()
