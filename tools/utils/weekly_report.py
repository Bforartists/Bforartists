#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import ast

# https://github.com/disqus/python-phabricator
from phabricator import Phabricator
phab = Phabricator()  # This will use your ~/.arcrc file
phab.update_interfaces()
me = phab.user.whoami()


class PhabTransaction:
    def __init__(self, story_data, time_start, time_end):
        # Unparsed entries:

        # For paging if necessary, but you can increase query limit.
        self.entry_id = int(story_data['chronologicalKey'])

        self.timestamp = int(story_data['epoch'])
        self.author = story_data['authorPHID']
        self.text = story_data['text']
        # Parsed entries:
        self.object_type = None
        self.object_name = None
        self.object_title = None
        self.action = None
        self.action_effect = ""

        # Parse only transactions from me
        if self.author != me['phid']:
            return None

        # Parse only transactions with date in requested range
        if self.timestamp < time_start or self.timestamp > time_end:
            return None

        # Parse object type (PHID-TASK, PHID-DREV, PHID-CMIT)
        self.object_type = story_data['objectPHID'][:9]

        # Parse `text` var
        # Typical strings are:
        # Joe Bloggs (ISS) added a comment to T75265: Movie Clip Editor not loading full image sequences.
        # Joe Bloggs (ISS) created D7318: Cleanup: Change callback suffix to `_fn` in sequencer.
        # Joe Bloggs (ISS) committed rB188ccfb0dd67: Fix T123456: Foo crashes (authored by Joe Bloggs (ISS)).
        text_unparsed = story_data['text']

        # Chop off author part
        start = text_unparsed.find(')') + 2
        text_unparsed = text_unparsed[start:]

        # Parse object name (Txxxx, Dxxxx, commit hash).
        if self.object_type == "PHID-TASK":
            start = text_unparsed.find('T')
            end = text_unparsed.find(':')
            self.object_name = text_unparsed[start:end]
        if self.object_type == "PHID-DREV":
            start = text_unparsed.find('D')
            end = text_unparsed.find(':')
            self.object_name = text_unparsed[start:end]
        if self.object_type == "PHID-CMIT":
            start = text_unparsed.find('rB')
            end = text_unparsed.find(':')
            self.object_name = text_unparsed[start:end]
        if self.object_type == "PHID-PSTE":
            start = text_unparsed.find('P')
            end = text_unparsed.find(':')
            self.object_name = text_unparsed[start:end]
        if self.object_type == "PHID-USER":
            self.object_name = "XXX-profile-edit"
        if self.object_type == "PHID-PROJ":
            self.object_name = "XXX-project-edit"

        # Parse action - like "added a comment to", "created", ...
        end = start - 1
        self.action = text_unparsed[:end]

        # Parse object title
        start = text_unparsed.find(':') + 2
        end = len(text_unparsed)
        if self.object_type == "PHID-CMIT":
            end = text_unparsed.find('(authored by') - 1
        self.object_title = text_unparsed[start:end]

        # Parse "effect" of action for example action "closed" may have effect of "Invalid" or "Resolved"
        start = text_unparsed.rfind('"', 0, len(text_unparsed) - 3)
        if start != -1:
            self.action_effect = text_unparsed[start + 1:-2]

        if self.object_name is None or self.object_type is None or self.action is None:
            raise ValueError('Can not parse transaction. \n', story_data['text'])

    # Nice for debug
    def to_list(self):
        return [
            self.entry_id,
            self.timestamp,
            self.author,
            self.object_type,
            self.object_name,
            self.action,
            self.action_effect,
            self.object_title,
            self.text,
        ]


def add_to_catalog(catalog, transaction):
    key = transaction.object_name
    if key not in catalog:
        catalog[key] = []
    catalog[key].append(transaction)


def report_personal_weekly_get(time_start, time_end):
    result = phab.feed.query(
        filterPHIDs=[me['phid']],
        limit=500,
        view="text"
    )

    # Strip junk from result, so it can be parsed
    result = str(result)[9:-1]
    # Parse and convert to dict
    stories = ast.literal_eval(result)
    transactions = []

    for story in stories:
        data = stories[story]
        transaction = PhabTransaction(data, time_start, time_end)
        transactions.append(transaction)

    # Make catalogs - per-category view
    tasks = {}
    review = {}
    created_diffs = {}
    commits = {}
    confirmed = {}
    resolved = {}
    archived = {}
    duplicate = {}
    needs_info = {}
    needs_info_dev = {}

    # Total number of actions.
    task_txn_count = 0

    for transaction in transactions:
        # Skip unparsed.
        if transaction.object_type is None:
            continue

        if transaction.object_type == 'PHID-TASK':
            add_to_catalog(tasks, transaction)
            task_txn_count += 1
        if transaction.object_type == 'PHID-DREV':
            add_to_catalog(review, transaction)  # Own diffs removed lower in code.
            if transaction.action == 'created':
                add_to_catalog(created_diffs, transaction)
        if transaction.object_type == 'PHID-CMIT' and transaction.action == 'committed':
            add_to_catalog(commits, transaction)
        if transaction.action_effect == 'Confirmed':
            add_to_catalog(confirmed, transaction)
        if transaction.action == 'closed' and transaction.action_effect == 'Resolved':
            add_to_catalog(resolved, transaction)
        if transaction.action == 'closed' and transaction.action_effect == 'Archived':
            add_to_catalog(archived, transaction)
        if transaction.action == 'merged task':
            add_to_catalog(duplicate, transaction)
        if transaction.action_effect == 'Needs Information from User':
            add_to_catalog(needs_info, transaction)
        if transaction.action_effect == 'Needs Information from Developers':
            add_to_catalog(needs_info_dev, transaction)

    # Get all own diffs
    constraints = {
        "authorPHIDs": [me['userName']],
    }
    result = phab.differential.revision.search(constraints=constraints)
    data = result["data"]

    # Remove own diffs from review "catalog"
    for diff in data:
        diff_id = 'D' + str(diff['id'])
        review.pop(diff_id, None)

    # Get open own diffs
    constraints['modifiedStart'] = time_start
    result = phab.differential.revision.search(queryKey="open", constraints=constraints)
    data = result["data"]

    accepteds = [diff for diff in data if diff['fields']['status']['name'] == "Accepted"]
    needs_reviews = [diff for diff in data if diff['fields']['status']['name'] == "Needs Review"]
    needs_revisions = [diff for diff in data if diff['fields']['status']['name'] == "Needs Revision"]
    changes_planneds = [diff for diff in data if diff['fields']['status']['name'] == "Changes Planned"]
    sum_diffs = len(accepteds) + len(needs_reviews) + len(needs_revisions) + len(changes_planneds)

    # Print triaging stats
    print("\'\'\'Involved in %s reports:\'\'\'" % len(tasks))
    print("* Confirmed: %s" % len(confirmed))
    print("* Closed as Resolved: %s" % len(resolved))
    print("* Closed as Archived: %s" % len(archived))
    print("* Closed as Duplicate: %s" % len(duplicate))
    print("* Needs Info from User: %s" % len(needs_info))
    print("* Needs Info from Developers: %s" % len(needs_info_dev))
    print("* Actions total: %s" % task_txn_count)
    print()

    # Print review stats
    print("'''Review: %s'''" % len(review))
    for key in review:
        txn = review[key][0]
        print("* %s [https://developer.blender.org/%s %s]" % (txn.text, txn.object_name, txn.object_name))
    print()

    # Print created diffs
    print("'''Created patches: %s'''" % len(created_diffs))
    for key in created_diffs:
        txn = created_diffs[key][0]
        print("* %s [https://developer.blender.org/%s %s]" % (txn.object_title, txn.object_name, txn.object_name))
    print()

    # Print open diffs
    print("\'\'\'Patches worked on: %s\'\'\'" % sum_diffs)
    for diff in sorted(data, key=lambda i: i['fields']['status']['name']):
        if diff["fields"]["status"]['closed']:
            continue
        diff_title = diff["fields"]["title"]
        diff_status = diff["fields"]["status"]['name']
        print("* %s: %s [https://developer.blender.org/D%s D%s]" % (diff_status, diff_title, diff['id'], diff['id']))
    print()

    # Print commits
    print("'''Commits:'''")
    for key in commits:
        txn = commits[key][0]
        print("* %s {{GitCommit|%s}}" % (txn.object_title, txn.object_name))


def main():
    #end_date = datetime.datetime(2020, 3, 14)
    end_date = datetime.datetime.now()
    weekday = end_date.weekday()

    # Assuming I am lazy and making this at last moment or even later in worst case
    if weekday < 2:
        time_delta = 7 + weekday
        start_date = end_date - datetime.timedelta(days=time_delta, hours=end_date.hour)
        end_date -= datetime.timedelta(days=weekday, hours=end_date.hour)
    else:
        time_delta = weekday
        start_date = end_date - datetime.timedelta(days=time_delta, hours=end_date.hour)

    # Ensure friday :)
    firday = start_date + datetime.timedelta(days=4)
    week = start_date.isocalendar()[1]
    start_date_str = start_date.strftime('%b %d')
    end_date_str = firday.strftime('%b %d')

    print("== Week %d (%s - %s) ==\n\n" % (week, start_date_str, end_date_str))
    report_personal_weekly_get(int(start_date.timestamp()), int(end_date.timestamp()))


if __name__ == "__main__":
    main()

    # wait for input to close window
    input()
