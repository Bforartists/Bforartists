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

import time

from netrender.utils import *
import netrender.model

class RatingRule:
    def __init__(self):
        self.enabled = True
        self.editable = False

    def id(self):
        return str(id(self))

    def rate(self, job):
        return 0

class ExclusionRule:
    def __init__(self):
        self.enabled = True
        self.editable = True
    def id(self):
        return str(id(self))

    def test(self, job):
        return False

class PriorityRule:
    def __init__(self):
        self.enabled = True
        self.editable = True
    def id(self):
        return str(id(self))

    def test(self, job):
        return False

class Balancer:
    def __init__(self):
        self.rules = []
        self.priorities = []
        self.exceptions = []

    def ruleByID(self, rule_id):
        for rule in self.rules:
            if rule.id() == rule_id:
                return rule
        for rule in self.priorities:
            if rule.id() == rule_id:
                return rule
        for rule in self.exceptions:
            if rule.id() == rule_id:
                return rule

        return None

    def addRule(self, rule):
        self.rules.append(rule)

    def addPriority(self, priority):
        self.priorities.append(priority)

    def addException(self, exception):
        self.exceptions.append(exception)

    def applyRules(self, job):
        return sum((rule.rate(job) for rule in self.rules if rule.enabled))

    def applyPriorities(self, job):
        for priority in self.priorities:
            if priority.enabled and priority.test(job):
                return True # priorities are first

        return False

    def applyExceptions(self, job):
        for exception in self.exceptions:
            if exception.enabled and exception.test(job):
                return True # exceptions are last

        return False

    def sortKey(self, job):
        return (1 if self.applyExceptions(job) else 0, # exceptions after
                        0 if self.applyPriorities(job) else 1, # priorities first
                        self.applyRules(job))

    def balance(self, jobs):
        if jobs:
            # use inline copy to make sure the list is still accessible while sorting
            jobs[:] = sorted(jobs, key=self.sortKey)
            return jobs[0]
        else:
            return None

# ==========================

class RatingUsage(RatingRule):
    def __str__(self):
        return "Usage per job"

    def rate(self, job):
        # less usage is better
        return job.usage / job.priority
    def serialize(self):
        return { "type": "rating",
                 "enabled": self.enabled,
                 "descritpiton":str(self),
                 "limit":"",
                 "id":self.id()
                }


class RatingUsageByCategory(RatingRule):
    def __init__(self, get_jobs):
        super().__init__()
        self.getJobs = get_jobs

    def __str__(self):
        return "Usage per category"

    def rate(self, job):
        total_category_usage = sum([j.usage for j in self.getJobs() if j.category == job.category])
        maximum_priority = max([j.priority for j in self.getJobs() if j.category == job.category])

        # less usage is better
        return total_category_usage / maximum_priority

    def serialize(self):
        return { "type": "rating",
                 "enabled": self.enabled,
                 "editable": self.editable,
                 "descritpiton":str(self),
                 "limit":"",
                 "id":self.id()
                }


class NewJobPriority(PriorityRule):
    def __init__(self, limit = 1):
        super().__init__()
        self.limit = limit

    def setLimit(self, value):
        self.limit = int(value)

    def str_limit(self):
        return "less than %i frame%s done" % (self.limit, "s" if self.limit > 1 else "")

    def __str__(self):
        return "Priority to new jobs"

    def test(self, job):
        return job.countFrames(status = netrender.model.FRAME_DONE) < self.limit
    def serialize(self):
        return { "type": "priority",
                 "enabled": self.enabled,
                 "editable": self.editable,
                 "descritpiton":str(self),
                 "limit": self.limit,
                 "limit_str":self.str_limit(),
                 "id":self.id()
                }

class MinimumTimeBetweenDispatchPriority(PriorityRule):
    def __init__(self, limit = 10):
        super().__init__()
        self.limit = limit

    def setLimit(self, value):
        self.limit = int(value)

    def str_limit(self):
        return "more than %i minute%s since last" % (self.limit, "s" if self.limit > 1 else "")

    def __str__(self):
        return "Priority to jobs that haven't been dispatched recently"

    def test(self, job):
        return job.countFrames(status = netrender.model.FRAME_DISPATCHED) == 0 and (time.time() - job.last_dispatched) / 60 > self.limit

    def serialize(self):
        return { "type": "priority",
                 "enabled": self.enabled,
                 "editable": self.editable,
                 "descritpiton":str(self),
                 "limit": self.limit,
                 "limit_str":self.str_limit(),
                 "id":self.id()
                }

class ExcludeQueuedEmptyJob(ExclusionRule):
    def __init__(self):
        super().__init__()
        self.editable= False
    def __str__(self):
        return "Exclude non queued or empty jobs"

    def test(self, job):
        return job.status != netrender.model.JOB_QUEUED or job.countFrames(status = netrender.model.FRAME_QUEUED) == 0

    def serialize(self):
        return { "type": "exception",
                 "enabled": self.enabled,
                 "editable": self.editable,
                 "descritpiton":str(self),
                 "limit": "",
                 "limit_str":"",
                 "id":self.id()
                }


class ExcludeSlavesLimit(ExclusionRule):
    def __init__(self, count_jobs, count_slaves, limit = 0.75):
        super().__init__()
        self.count_jobs = count_jobs
        self.count_slaves = count_slaves
        self.limit = limit

    def setLimit(self, value):
        self.limit = float(value)

    def str_limit(self):
        return "more than %.0f%% of all slaves" % (self.limit * 100)

    def __str__(self):
        return "Exclude jobs that would use too many slaves"

    def test(self, job):
        return not ( self.count_jobs() == 1 or self.count_slaves() <= 1 or float(job.countSlaves() + 1) / self.count_slaves() <= self.limit )

    def serialize(self):
        return { "type": "exception",
                 "enabled": self.enabled,
                 "editable": self.editable,
                 "descritpiton":str(self),
                 "limit": self.limit,
                 "limit_str":self.str_limit(),
                 "id":self.id()
                }
