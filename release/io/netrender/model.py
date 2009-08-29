import sys, os
import http, http.client, http.server, urllib
import subprocess, shutil, time, hashlib

from netrender.utils import *

class RenderSlave:
	_slave_map = {}
	
	def __init__(self):
		self.id = ""
		self.name = ""
		self.adress = (0,0)
		self.stats = ""
		self.total_done = 0
		self.total_error = 0
		self.last_seen = 0.0
		
	def serialize(self):
		return 	{
							"id": self.id,
							"name": self.name,
							"adress": self.adress,
							"stats": self.stats,
							"total_done": self.total_done,
							"total_error": self.total_error,
							"last_seen": self.last_seen
						}
	
	@staticmethod
	def materialize(data):
		if not data:
			return None
		
		slave_id = data["id"]
		
		if slave_id in RenderSlave._slave_map:
			return RenderSlave._slave_map[slave_id]
		else:
			slave = RenderSlave()
			slave.id = slave_id
			slave.name = data["name"]
			slave.adress = data["adress"]
			slave.stats = data["stats"]
			slave.total_done = data["total_done"]
			slave.total_error = data["total_error"]
			slave.last_seen = data["last_seen"]
			
			RenderSlave._slave_map[slave_id] = slave
			
			return slave

class RenderJob:
	def __init__(self):
		self.id = ""
		self.name = ""
		self.path = ""
		self.frames = []
		self.chunks = 0
		self.priority = 0
		self.credits = 0
		self.blacklist = []
		self.last_dispatched = 0.0
	
	def __len__(self):
		return len(self.frames)
	
	def status(self):
		results = {
								QUEUED: 0,
								DISPATCHED: 0,
								DONE: 0,
								ERROR: 0
							}
		
		for frame in self.frames:
			results[frame.status] += 1
			
		return results
	
	def __contains__(self, frame_number):
		for f in self.frames:
			if f.number == frame_number:
				return True
		else:
			return False
	
	def __getitem__(self, frame_number):
		for f in self.frames:
			if f.number == frame_number:
				return f
		else:
			return None
		
	def serialize(self, frames = None):
		return 	{
							"id": self.id,
							"name": self.name,
							"path": self.path,
							"frames": [f.serialize() for f in self.frames if not frames or f in frames],
							"priority": self.priority,
							"credits": self.credits,
							"blacklist": self.blacklist,
							"last_dispatched": self.last_dispatched
						}

	@staticmethod
	def materialize(data):
		if not data:
			return None
		
		job = RenderJob()
		job.id = data["id"]
		job.name = data["name"]
		job.path = data["path"]
		job.frames = [RenderFrame.materialize(f) for f in data["frames"]]
		job.priority = data["priority"]
		job.credits = data["credits"]
		job.blacklist = data["blacklist"]
		job.last_dispatched = data["last_dispatched"]

		return job

class RenderFrame:
	def __init__(self):
		self.number = 0
		self.time = 0
		self.status = QUEUED
		self.slave = None

	def serialize(self):
		return 	{
							"number": self.number,
							"time": self.time,
							"status": self.status,
							"slave": None if not self.slave else self.slave.serialize()
						}
						
	@staticmethod
	def materialize(data):
		if not data:
			return None
		
		frame = RenderFrame()
		frame.number = data["number"]
		frame.time = data["time"]
		frame.status = data["status"]
		frame.slave = RenderSlave.materialize(data["slave"])

		return frame
