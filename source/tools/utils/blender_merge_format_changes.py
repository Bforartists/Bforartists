#!/usr/bin/env python3

import os
import subprocess
import sys

format_commit = '<clang-format-commit>' # TODO: update with actual commit that applies formatting
pre_format_commit = format_commit + '~1'

def get_string(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf8').strip()

# Parse arguments.
mode = None
if len(sys.argv) == 2:
    if sys.argv[1] == '--rebase':
        mode = 'rebase'
    elif sys.argv[1] == '--merge':
        mode = 'merge'

if mode == None:
    print("Merge or rebase Blender master into a branch in 3 steps,")
    print("to automatically merge clang-format changes.")
    print("")
    print("  --rebase     Perform equivalent of 'git rebase master'")
    print("  --merge      Perform equivalent of 'git merge master'")
    sys.exit(0)

# Verify we are in the right directory.
root_path = get_string(['git', 'rev-parse', '--show-superproject-working-tree'])
if os.path.realpath(root_path) != os.path.realpath(os.getcwd()):
    print("BLENDER MERGE: must run from blender repository root directory")
    sys.exit(1)

# Abort if a rebase is still progress.
rebase_merge = get_string(['git', 'rev-parse', '--git-path', 'rebase-merge'])
rebase_apply = get_string(['git', 'rev-parse', '--git-path', 'rebase-apply'])
merge_head = get_string(['git', 'rev-parse', '--git-path', 'MERGE_HEAD'])
if os.path.exists(rebase_merge) or \
   os.path.exists(rebase_apply) or \
   os.path.exists(merge_head):
    print("BLENDER MERGE: rebase or merge in progress, complete it first")
    sys.exit(1)

# Abort if uncommitted changes.
changes = get_string(['git', 'status', '--porcelain', '--untracked-files=no'])
if len(changes) != 0:
    print("BLENDER MERGE: detected uncommitted changes, can't run")
    sys.exit(1)

# Setup command, with commit message for merge commits.
if mode == 'rebase':
    mode_cmd = 'rebase'
else:
    branch = get_string(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    mode_cmd = 'merge --no-edit -m "Merge \'master\' into \'' + branch + '\'"';

# Rebase up to the clang-format commit.
code = os.system('git merge-base --is-ancestor ' + pre_format_commit + ' HEAD')
if code != 0:
    code = os.system('git ' + mode_cmd + ' ' + pre_format_commit)
    if code != 0:
        print("BLENDER MERGE: resolve conflicts, complete " + mode + " and run again")
        sys.exit(code)

# Rebase clang-format commit.
code = os.system('git merge-base --is-ancestor ' + format_commit + ' HEAD')
if code != 0:
    os.system('git ' + mode_cmd + ' -Xignore-all-space -Xours ' + format_commit )
    os.system('make format')
    os.system('git add -u')
    count = int(get_string(['git', 'rev-list', '--count', '' + format_commit + '..HEAD']))
    if count == 1 or mode == 'merge':
        # Amend if we just have a single commit or are merging.
        os.system('git commit --amend --no-edit')
    else:
        # Otherwise create a commit for formatting.
        os.system('git commit -m "Cleanup: apply clang format"')

# Rebase remaning commits
code = os.system('git ' + mode_cmd + ' master')
if code != 0:
    print("BLENDER MERGE: resolve conflicts, complete " + mode + " and you're done")
else:
    print("BLENDER MERGE: done")
sys.exit(code)
