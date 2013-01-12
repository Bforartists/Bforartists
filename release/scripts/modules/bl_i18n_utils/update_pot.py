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

# Update blender.pot file from messages.txt

import subprocess
import collections
import os
import sys
import re
import tempfile
import argparse
import time
import pickle

try:
    import settings
    import utils
except:
    from . import (settings, utils)


LANGUAGES_CATEGORIES = settings.LANGUAGES_CATEGORIES
LANGUAGES = settings.LANGUAGES

PO_COMMENT_PREFIX = settings.PO_COMMENT_PREFIX
PO_COMMENT_PREFIX_SOURCE = settings.PO_COMMENT_PREFIX_SOURCE
PO_COMMENT_PREFIX_SOURCE_CUSTOM = settings.PO_COMMENT_PREFIX_SOURCE_CUSTOM
MSG_COMMENT_PREFIX = settings.MSG_COMMENT_PREFIX
MSG_CONTEXT_PREFIX = settings.MSG_CONTEXT_PREFIX
FILE_NAME_MESSAGES = settings.FILE_NAME_MESSAGES
FILE_NAME_POT = settings.FILE_NAME_POT
SOURCE_DIR = settings.SOURCE_DIR
POTFILES_DIR = settings.POTFILES_SOURCE_DIR
SRC_POTFILES = settings.FILE_NAME_SRC_POTFILES

CONTEXT_DEFAULT = settings.CONTEXT_DEFAULT
PYGETTEXT_ALLOWED_EXTS = settings.PYGETTEXT_ALLOWED_EXTS
PYGETTEXT_MAX_MULTI_CTXT = settings.PYGETTEXT_MAX_MULTI_CTXT

SVN_EXECUTABLE = settings.SVN_EXECUTABLE

WARN_NC = settings.WARN_MSGID_NOT_CAPITALIZED
NC_ALLOWED = settings.WARN_MSGID_NOT_CAPITALIZED_ALLOWED

SPELL_CACHE = settings.SPELL_CACHE


# Do this only once!
# Get contexts defined in blf.
CONTEXTS = {}
with open(os.path.join(SOURCE_DIR, settings.PYGETTEXT_CONTEXTS_DEFSRC)) as f:
    reg = re.compile(settings.PYGETTEXT_CONTEXTS)
    f = f.read()
    # This regex is supposed to yield tuples
    # (key=C_macro_name, value=C_string).
    CONTEXTS = dict(m.groups() for m in reg.finditer(f))

# Build regexes to extract messages (with optional contexts) from C source.
pygettexts = tuple(re.compile(r).search
                   for r in settings.PYGETTEXT_KEYWORDS)
_clean_str = re.compile(settings.str_clean_re).finditer
clean_str = lambda s: "".join(m.group("clean") for m in _clean_str(s))


def _new_messages():
    return getattr(collections, "OrderedDict", dict)()


def check_file(path, rel_path, messages):
    def process_entry(ctxt, msg):
        # Context.
        if ctxt:
            if ctxt in CONTEXTS:
                ctxt = CONTEXTS[ctxt]
            elif '"' in ctxt or "'" in ctxt:
                ctxt = clean_str(ctxt)
            else:
                print("WARNING: raw context “{}” couldn’t be resolved!"
                      "".format(ctxt))
                ctxt = CONTEXT_DEFAULT
        else:
            ctxt = CONTEXT_DEFAULT
        # Message.
        if msg:
            if '"' in msg or "'" in msg:
                msg = clean_str(msg)
            else:
                print("WARNING: raw message “{}” couldn’t be resolved!"
                      "".format(msg))
                msg = ""
        else:
            msg = ""
        return (ctxt, msg)

    with open(path, encoding="utf-8") as f:
        f = f.read()
        for srch in pygettexts:
            m = srch(f)
            line = pos = 0
            while m:
                d = m.groupdict()
                # Line.
                line += f[pos:m.start()].count('\n')
                msg = d.get("msg_raw")
                # First, try the "multi-contexts" stuff!
                ctxts = tuple(d.get("ctxt_raw{}".format(i)) for i in range(PYGETTEXT_MAX_MULTI_CTXT))
                if ctxts[0]:
                    for ctxt in ctxts:
                        if not ctxt:
                            break
                        ctxt, _msg = process_entry(ctxt, msg)
                        # And we are done for this item!
                        messages.setdefault((ctxt, _msg), []).append(":".join((rel_path, str(line))))
                else:
                    ctxt = d.get("ctxt_raw")
                    ctxt, msg = process_entry(ctxt, msg)
                    # And we are done for this item!
                    messages.setdefault((ctxt, msg), []).append(":".join((rel_path, str(line))))
                pos = m.end()
                line += f[m.start():pos].count('\n')
                m = srch(f, pos)


def py_xgettext(messages):
    forbidden = set()
    forced = set()
    with open(SRC_POTFILES) as src:
        for l in src:
            if l[0] == '-':
                forbidden.add(l[1:].rstrip('\n'))
            elif l[0] != '#':
                forced.add(l.rstrip('\n'))
    for root, dirs, files in os.walk(POTFILES_DIR):
        if "/.svn" in root:
            continue
        for fname in files:
            if os.path.splitext(fname)[1] not in PYGETTEXT_ALLOWED_EXTS:
                continue
            path = os.path.join(root, fname)
            rel_path = os.path.relpath(path, SOURCE_DIR)
            if rel_path in forbidden:
                continue
            elif rel_path not in forced:
                forced.add(rel_path)
    for rel_path in sorted(forced):
        path = os.path.join(SOURCE_DIR, rel_path)
        if os.path.exists(path):
            check_file(path, rel_path, messages)


# Spell checking!
import enchant
dict_spelling = enchant.Dict("en_US")

from spell_check_utils import (dict_uimsgs,
                               split_words,
                              )

_spell_checked = set()


def spell_check(txt, cache):
    ret = []

    if cache is not None and txt in cache:
        return ret

    for w in split_words(txt):
        w_lower = w.lower()
        if w_lower in dict_uimsgs | _spell_checked:
            continue
        if not dict_spelling.check(w):
            ret.append("{}: suggestions are ({})"
                       .format(w, "'" + "', '".join(dict_spelling.suggest(w))
                                  + "'"))
        else:
            _spell_checked.add(w_lower)

    if not ret:
        if cache is not None:
            cache.add(txt)

    return ret


def get_svnrev():
    cmd = [SVN_EXECUTABLE,
           "info",
           "--xml",
           SOURCE_DIR,
           ]
    xml = subprocess.check_output(cmd)
    return re.search(b'revision="(\d+)"', xml).group(1)


def gen_empty_pot():
    blender_ver = ""
    blender_rev = get_svnrev().decode()
    utctime = time.gmtime()
    time_str = time.strftime("%Y-%m-%d %H:%M+0000", utctime)
    year_str = time.strftime("%Y", utctime)

    return utils.I18nMessages.gen_empty_messages("__POT__", blender_ver, blender_rev, time_str, year_str)


escape_re = tuple(re.compile(r[0]) for r in settings.ESCAPE_RE)
escape = lambda s, n: escape_re[n].sub(settings.ESCAPE_RE[n][1], s)


def merge_messages(msgs, messages, do_checks, spell_cache):
    num_added = 0
    num_present = msgs.nbr_msgs
    for (context, msgid), srcs in messages.items():
        if do_checks:
            err = spell_check(msgid, spell_cache)
            if err:
                print("WARNING: spell check failed on “" + msgid + "”:")
                print("\t\t" + "\n\t\t".join(err))
                print("\tFrom:\n\t\t" + "\n\t\t".join(srcs))

        # Escape some chars in msgid!
        for n in range(len(escape_re)):
            msgid = escape(msgid, n)

        key = (context, msgid)
        if key not in msgs.msgs:
            msg = utils.I18nMessage([context], [msgid], [""], [])
            msg.sources = srcs
            msgs.msgs[key] = msg
            num_added += 1
        else:
            # We need to merge sources!
            msgs.msgs[key].sources += srcs

    return num_added, num_present


def main():
    parser = argparse.ArgumentParser(description="Update blender.pot file from messages.txt and source code parsing, "
                                                 "and performs some checks over msgids.")
    parser.add_argument('-w', '--warning', action="store_true",
                        help="Show warnings.")
    parser.add_argument('-i', '--input', metavar="File",
                        help="Input messages file path.")
    parser.add_argument('-o', '--output', metavar="File",
                        help="Output pot file path.")

    args = parser.parse_args()
    if args.input:
        global FILE_NAME_MESSAGES
        FILE_NAME_MESSAGES = args.input
    if args.output:
        global FILE_NAME_POT
        FILE_NAME_POT = args.output

    print("Running fake py gettext…")
    # Not using any more xgettext, simpler to do it ourself!
    messages = _new_messages()
    py_xgettext(messages)
    print("Finished, found {} messages.".format(len(messages)))

    if SPELL_CACHE and os.path.exists(SPELL_CACHE):
        with open(SPELL_CACHE, 'rb') as f:
            spell_cache = pickle.load(f)
    else:
        spell_cache = set()

    print("Generating POT file {}…".format(FILE_NAME_POT))
    msgs = gen_empty_pot()
    tot_messages, _a = merge_messages(msgs, messages, True, spell_cache)

    # add messages collected automatically from RNA
    print("\tMerging RNA messages from {}…".format(FILE_NAME_MESSAGES))
    messages.clear()
    with open(FILE_NAME_MESSAGES, encoding="utf-8") as f:
        srcs = []
        context = ""
        for line in f:
            line = utils.stripeol(line)

            if line.startswith(MSG_COMMENT_PREFIX):
                srcs.append(line[len(MSG_COMMENT_PREFIX):].strip())
            elif line.startswith(MSG_CONTEXT_PREFIX):
                context = line[len(MSG_CONTEXT_PREFIX):].strip()
            else:
                key = (context, line)
                messages[key] = srcs
                srcs = []
                context = ""
    num_added, num_present = merge_messages(msgs, messages, True, spell_cache)
    tot_messages += num_added
    print("\tMerged {} messages ({} were already present).".format(num_added, num_present))

    print("\tAdding languages labels...")
    messages.clear()
    messages.update(((CONTEXT_DEFAULT, lng[1]), ("Languages’ labels from bl_i18n_utils/settings.py",))
                    for lng in LANGUAGES)
    messages.update(((CONTEXT_DEFAULT, cat[1]), ("Language categories’ labels from bl_i18n_utils/settings.py",))
                     for cat in LANGUAGES_CATEGORIES)
    num_added, num_present = merge_messages(msgs, messages, True, spell_cache)
    tot_messages += num_added
    print("\tAdded {} language messages.".format(num_added))

    # Write back all messages into blender.pot.
    msgs.write('PO', FILE_NAME_POT)

    if SPELL_CACHE and spell_cache:
        with open(SPELL_CACHE, 'wb') as f:
            pickle.dump(spell_cache, f)

    print("Finished, total: {} messages!".format(tot_messages))

    return 0


if __name__ == "__main__":
    print("\n\n *** Running {} *** \n".format(__file__))
    sys.exit(main())
