#!/usr/bin/python3

# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENSE BLOCK *****

# <pep8 compliant>

# Update trunk from branches:
# * Remove po’s in trunk.
# * Copy po’s from branches advanced enough.
# * Clean po’s in trunk.
# * Compile po’s in trunk in mo’s, keeping track of those failing.
# * Remove po’s, mo’s (and their dir’s) that failed to compile or
#   are no more present in trunk.

import subprocess
import os
import sys
import shutil

try:
    import settings
    import utils
except:
    from . import (settings, utils)

BRANCHES_DIR = settings.BRANCHES_DIR
TRUNK_PO_DIR = settings.TRUNK_PO_DIR
TRUNK_MO_DIR = settings.TRUNK_MO_DIR

LANGUAGES_CATEGORIES = settings.LANGUAGES_CATEGORIES
LANGUAGES = settings.LANGUAGES
LANGUAGES_FILE = settings.LANGUAGES_FILE

PY3 = settings.PYTHON3_EXEC


def find_matching_po(languages, stats):
    """Match languages defined in LANGUAGES setting to relevant po, if possible!"""
    ret = []
    for uid, label, org_key in languages:
        key = org_key
        if key not in stats:
            # Try to simplify the key (eg from es_ES to es).
            if '_' in org_key:
                key = org_key[0:org_key.index('_')]
            if '@' in org_key:
                key = key + org_key[org_key.index('@'):]
        if key in stats:
            ret.append((stats[key], uid, label, org_key))
        else:
            # Mark invalid entries, so that we can put them in the languages file,
            # but commented!
            ret.append((0.0, -uid, label, org_key))
    return ret

def main():
    import argparse
    parser = argparse.ArgumentParser(description=""
                        "Update trunk from branches:\n"
                        "* Remove po’s in trunk.\n"
                        "* Copy po’s from branches advanced enough.\n"
                        "* Clean po’s in trunk.\n"
                        "* Compile po’s in trunk in mo’s, keeping "
                        "track of those failing.\n"
                        "* Remove po’s and mo’s (and their dir’s) that "
                        "failed to compile or are no more present in trunk."
                        "* Generate languages file used by Blender's i18n.")
    parser.add_argument('-t', '--threshold', type=int, help="Import threshold, as a percentage.")
    parser.add_argument('-p', '--po', action="store_true", help="Remove failing po’s.")
    parser.add_argument('-m', '--mo', action="store_true", help="Remove failing mo’s.")
    parser.add_argument('langs', metavar='ISO_code', nargs='*', help="Restrict processed languages to those.")
    args = parser.parse_args()

    ret = 0
    failed = set()
    # 'DEFAULT' and en_US are always valid, fully-translated "languages"!
    stats = {"DEFAULT": 1.0, "en_US": 1.0}

    # Remove po’s in trunk.
    for po in os.listdir(TRUNK_PO_DIR):
        if po.endswith(".po"):
            lang = os.path.basename(po)[:-3]
            if args.langs and lang not in args.langs:
                continue
            po = os.path.join(TRUNK_PO_DIR, po)
            os.remove(po)

    # Copy po’s from branches.
    cmd = [PY3, "./import_po_from_branches.py", "-s"]
    if args.threshold is not None:
        cmd += ["-t", str(args.threshold)]
    if args.langs:
        cmd += args.langs
    t = subprocess.call(cmd)
    if t:
        ret = t

    # Add in failed all mo’s no more having relevant po’s in trunk.
    for lang in os.listdir(TRUNK_MO_DIR):
        if lang in {".svn", LANGUAGES_FILE}:
            continue  # !!!
        if not os.path.exists(os.path.join(TRUNK_PO_DIR, ".".join((lang, "po")))):
            failed.add(lang)

    # Check and compile each po separatly, to keep track of those failing.
    # XXX There should not be any failing at this stage, import step is
    #     supposed to have already filtered them out!
    for po in os.listdir(TRUNK_PO_DIR):
        if po.endswith(".po") and not po.endswith("_raw.po"):
            lang = os.path.basename(po)[:-3]
            if args.langs and lang not in args.langs:
                continue

            cmd = [PY3, "./clean_po.py", "-t", "-s", lang]
            t = subprocess.call(cmd)
            if t:
                ret = t
                failed.add(lang)
                continue

            cmd = [PY3, "./update_mo.py", lang]
            t = subprocess.call(cmd)
            if t:
                ret = t
                failed.add(lang)
                continue

            # Yes, I know, it's the third time we parse each po's here. :/
            u1, u2, _stats = utils.parse_messages(os.path.join(BRANCHES_DIR, lang, po))
            stats[lang] = _stats["trans_msg"] / _stats["tot_msg"]

    # Generate languages file used by Blender's i18n system.
    # First, match all entries in LANGUAGES to a lang in stats, if possible!
    stats = find_matching_po(LANGUAGES, stats)
    limits = sorted(LANGUAGES_CATEGORIES, key=lambda it: it[0], reverse=True)
    print(limits)
    idx = 0
    stats = sorted(stats, key=lambda it: it[0], reverse=True)
    print(stats)
    langs_cats = [[] for i in range(len(limits))]
    highest_uid = 0
    for prop, uid, label, key in stats:
        print(key, prop)
        if prop < limits[idx][0]:
            # Sub-sort languages by iso-codes.
            langs_cats[idx].sort(key=lambda it: it[2])
            print(langs_cats)
            idx += 1
        langs_cats[idx].append((uid, label, key))
        if abs(uid) > highest_uid:
            highest_uid = abs(uid)
    # Sub-sort last group of languages by iso-codes!
    langs_cats[idx].sort(key=lambda it: it[2])
    with open(os.path.join(TRUNK_MO_DIR, LANGUAGES_FILE), 'w', encoding="utf-8") as f:
        f.write("# Highest ID currently in use: {}\n".format(highest_uid))
        for cat, langs_cat in zip(limits, langs_cats):
            # Write "category menu label"...
            f.write("0:{}:\n".format(cat[1]))
            # ...and all matching language entries!
            for uid, label, key in langs_cat:
                if uid < 0:
                    # Non-existing, commented entry!
                    f.write("# No translation yet! #{}:{}:{}\n".format(-uid, label, key))
                else:
                    f.write("{}:{}:{}\n".format(uid, label, key))

    # Remove failing po’s, mo’s and related dir’s.
    for lang in failed:
        print("Lang “{}” failed, removing it...".format(lang))
        if args.po:
            po = os.path.join(TRUNK_PO_DIR, ".".join((lang, "po")))
            if os.path.exists(po):
                os.remove(po)
        if args.mo:
            mo = os.path.join(TRUNK_MO_DIR, lang)
            if os.path.exists(mo):
                shutil.rmtree(mo)


if __name__ == "__main__":
    print("\n\n *** Running {} *** \n".format(__file__))
    sys.exit(main())
