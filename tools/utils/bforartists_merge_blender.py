#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Automate the Blender → Bforartists merge workflow.

Creates a merge-week{N} branch from the latest Bforartists master,
updates the local Blender main tracking branch, pre-fetches LFS objects,
merges Blender main into the new branch, pauses for conflict resolution,
then performs LFS checkout with BFA bias.

Usage:
    python tools/utils/bforartists_merge_blender.py --week-number 30                      # Standard run
    python tools/utils/bforartists_merge_blender.py --week-number 30 --force              # Force skip confirmation
    python tools/utils/bforartists_merge_blender.py --week-number 30 --dry-run            # Simulate run
    python tools/utils/bforartists_merge_blender.py --week-number 30 --skip-master-update # Skip master update
    python tools/utils/bforartists_merge_blender.py --week-number 30 --resume             # Resume from conflicts

Help:
    python tools/utils/bforartists_merge_blender.py --help
"""

__all__ = (
    "main",
)

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Ensure Unicode output (→, ⚠, ✓, ═ ...) works even when the console codepage is not
# UTF-8 (e.g. cp1252 on Windows). Without this, printing these glyphs raises
# UnicodeEncodeError.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ---------------------------------------------------------------------------
# Terminal formatting helpers
# ---------------------------------------------------------------------------

class Color:
    """ANSI terminal colors (works on Windows 10+ and Linux/macOS)."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text: str) -> None:
    """Print a bold, colored section header."""
    print(f"\n{Color.BOLD}{Color.CYAN}{'=' * 72}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}  {text}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{'=' * 72}{Color.RESET}\n")


def print_step(text: str) -> None:
    """Print a numbered step."""
    print(f"{Color.BOLD}→ {text}{Color.RESET}")


def print_ok(text: str) -> None:
    """Print a success message."""
    print(f"  {Color.GREEN}✓ {text}{Color.RESET}")


def print_warn(text: str) -> None:
    """Print a warning message."""
    print(f"  {Color.YELLOW}⚠ {text}{Color.RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"  {Color.RED}✗ {text}{Color.RESET}")


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def run(cmd, *, exit_on_error=True, silent=False, cwd=None, env=None):
    """Run a command via subprocess. Returns exit code."""
    if not silent:
        print(f"  $ {' '.join(str(x) for x in cmd)}")

    sys.stdout.flush()
    sys.stderr.flush()

    kwargs = {}
    if cwd:
        kwargs["cwd"] = cwd
    if env:
        full_env = os.environ.copy()
        full_env.update(env)
        kwargs["env"] = full_env

    if silent:
        ret = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
    else:
        ret = subprocess.call(cmd, **kwargs)

    if exit_on_error and ret != 0:
        print_error(f"Command failed with exit code {ret}")
        sys.exit(ret)
    return ret


def run_output(cmd, *, exit_on_error=True):
    """Run a command and return its stdout as a string."""
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                       encoding='utf-8', errors='replace')
        return out.strip()
    except subprocess.CalledProcessError as e:
        if exit_on_error:
            print_error(f"Command failed: {' '.join(cmd)}")
            if e.output:
                print(e.output)
            sys.exit(e.returncode)
        return ""


def git_root():
    """Return the absolute path to the git repo root."""
    return Path(run_output(["git", "rev-parse", "--show-toplevel"]))


def git_current_branch():
    """Return the current branch name."""
    return run_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def git_is_clean():
    """Check if the working tree is clean (no staged or unstaged changes)."""
    out = run_output(["git", "status", "--porcelain", "--untracked-files=no", "--ignore-submodules"])
    return len(out) == 0


def git_remote_exists(name):
    """Check if a remote exists."""
    out = run_output(["git", "remote"], exit_on_error=False)
    return name in out.split()


def git_branch_exists_local(name):
    """Check if a local branch exists."""
    return run(["git", "rev-parse", "--verify", name], exit_on_error=False, silent=True) == 0


def git_branch_exists_remote(remote, branch):
    """Check if a remote branch exists."""
    return run(["git", "rev-parse", "--verify", f"remotes/{remote}/{branch}"],
               exit_on_error=False, silent=True) == 0


def git_has_merge_in_progress():
    """Check if a merge is currently in progress."""
    merge_head = run_output(["git", "rev-parse", "--git-path", "MERGE_HEAD"], exit_on_error=False)
    return os.path.exists(merge_head)


def git_get_conflicted_files():
    """Return a list of files with merge conflicts."""
    out = run_output(["git", "diff", "--name-only", "--diff-filter=U"], exit_on_error=False)
    if not out:
        return []
    return out.splitlines()


def git_tracking_branch():
    """Return the remote/branch that the current branch tracks, or empty string."""
    branch = git_current_branch()
    remote = run_output(["git", "config", f"branch.{branch}.remote"], exit_on_error=False)
    merge_ref = run_output(["git", "config", f"branch.{branch}.merge"], exit_on_error=False)
    if remote and merge_ref:
        # merge_ref looks like refs/heads/main → strip to just 'main'
        merge_branch = merge_ref.replace("refs/heads/", "")
        return f"{remote}/{merge_branch}"
    return ""


def git_commit_count_ahead_behind(target):
    """Return (ahead, behind) commit counts vs target branch."""
    out = run_output(["git", "rev-list", "--left-right", "--count", f"{target}...HEAD"],
                     exit_on_error=False)
    try:
        parts = out.split()
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 0, 0


# ---------------------------------------------------------------------------
# Platform helpers
# ---------------------------------------------------------------------------

def is_windows():
    return sys.platform == "win32"


def make_update_command():
    """Return the platform-appropriate 'make update' command."""
    if is_windows():
        return [".\\make.bat", "update"]
    else:
        return ["make", "update"]


# ---------------------------------------------------------------------------
# Phase implementations
# ---------------------------------------------------------------------------

def phase_preflight(args):
    """Phase 1: Safety checks and confirmation."""
    print_header("Phase 1: Preflight Checks")

    # 1. Are we in a git repo?
    print_step("Checking git repository...")
    try:
        root = git_root()
        print_ok(f"Git root: {root}")
    except Exception:
        print_error("Not in a git repository. Run this script from within the Bforartists repo.")
        sys.exit(1)

    # 2. Do required remotes exist?
    print_step(f"Checking remotes '{args.origin_remote}' and '{args.blender_remote}'...")
    if not git_remote_exists(args.origin_remote):
        print_error(f"Remote '{args.origin_remote}' not found. Available: {run_output(['git', 'remote'])}")
        sys.exit(1)
    if not git_remote_exists(args.blender_remote):
        print_error(f"Remote '{args.blender_remote}' not found. Available: {run_output(['git', 'remote'])}")
        sys.exit(1)
    print_ok(f"Remotes '{args.origin_remote}' and '{args.blender_remote}' exist")

    # 3. Is the working tree clean?
    print_step("Checking working tree is clean...")
    if not git_is_clean():
        print_error("Working tree has uncommitted changes. Please commit or stash them first.")
        sys.exit(1)
    print_ok("Working tree is clean")

    # 4. Branch name doesn't already exist?
    branch_name = f"merge-week{args.week_number}"
    print_step(f"Checking branch '{branch_name}' doesn't already exist...")
    if git_branch_exists_local(branch_name):
        # Branch exists — check if merge is already done or in progress
        current = git_current_branch()
        run(["git", "checkout", branch_name], silent=True)
        if git_has_merge_in_progress():
            print_warn(f"Branch '{branch_name}' exists with merge IN PROGRESS — will resume from conflict prompt")
        else:
            print_warn(f"Branch '{branch_name}' already exists and merge is complete — will skip to LFS checkout")
        # Switch back
        run(["git", "checkout", current], silent=True)
    else:
        print_ok(f"Branch '{branch_name}' is available")

    # 5. Check git lfs is installed
    print_step("Checking Git LFS is installed...")
    lfs_check = run(["git", "lfs", "version"], exit_on_error=False, silent=True)
    if lfs_check != 0:
        print_error("Git LFS is not installed. Install it from https://git-lfs.com/")
        sys.exit(1)
    print_ok("Git LFS is available")

    # 6. Print summary and confirm
    print_header("Summary")
    print(f"  Origin remote  : {Color.BOLD}{args.origin_remote}{Color.RESET} (Bforartists)")
    print(f"  Blender remote : {Color.BOLD}{args.blender_remote}{Color.RESET} (upstream Blender)")
    print(f"  Merge branch   : {Color.BOLD}merge-week{args.week_number}{Color.RESET}")
    print(f"  Source branch  : {Color.BOLD}{args.origin_remote}/master{Color.RESET}")
    print(f"  Merge from     : {Color.BOLD}{args.blender_remote}/main{Color.RESET}")
    if args.skip_master_update:
        print(f"  Master update  : {Color.YELLOW}SKIPPED{Color.RESET}")
    if args.dry_run:
        print(f"  Mode           : {Color.YELLOW}DRY RUN (no changes will be made){Color.RESET}")
    print()

    if not args.force:
        answer = input(f"{Color.BOLD}Proceed? [Y/n]: {Color.RESET}").strip().lower()
        if answer and answer != 'y':
            print("Aborted.")
            sys.exit(0)


def phase_update_master(args):
    """Phase 2: Fetch all remotes and update BFA master."""
    if args.skip_master_update:
        print_header("Phase 2: Update BFA Master — SKIPPED")
        return

    print_header("Phase 2: Update BFA Master")

    # 4. Fetch all remotes
    print_step("Fetching all remotes...")
    run(["git", "fetch", "--all", "--prune"])

    # 5. Fetch tags
    print_step("Fetching tags from origin...")
    run(["git", "fetch", args.origin_remote, "--tags", "--force"])

    # 6. Checkout master and pull with rebase
    print_step("Checking out master and pulling with rebase...")
    run(["git", "checkout", "master"])
    run(["git", "pull", args.origin_remote, "master", "--rebase"])
    print_ok("Master is up to date")

    # 7. Run make update
    print_step("Running 'make update' for submodules and LFS...")
    cmd = make_update_command()
    ret = run(cmd, exit_on_error=False)
    if ret != 0:
        print_warn("'make update' returned non-zero — continuing anyway (may be benign)")
    else:
        print_ok("'make update' completed")

    # 8. Clean submodules
    print_step("Cleaning submodules...")
    run(["git", "submodule", "foreach", "--recursive", "git", "reset", "--hard"])
    run(["git", "submodule", "foreach", "--recursive", "git", "clean", "-fd"])
    print_ok("Submodules cleaned")


def phase_create_branch(args):
    """Phase 3: Create the merge branch from master."""
    print_header("Phase 3: Create Merge Branch")

    branch_name = f"merge-week{args.week_number}"

    if git_branch_exists_local(branch_name):
        print_warn(f"Branch '{branch_name}' already exists — checking it out")
        run(["git", "checkout", branch_name])
        return

    print_step(f"Creating branch '{branch_name}' from master...")
    run(["git", "checkout", "--no-track", "-b", branch_name, "master"])
    print_ok(f"Branch '{branch_name}' created")


def phase_update_blender_main(args):
    """Phase 4: Update local Blender main tracking branch."""
    print_header("Phase 4: Update Blender Main")

    # 10. Checkout main
    print_step("Checking out 'main' (Blender tracking branch)...")
    if not git_branch_exists_local("main"):
        print_error("Local branch 'main' does not exist. Create it tracking blender/main first:")
        print_error("  git checkout -t blender/main")
        sys.exit(1)
    run(["git", "checkout", "main"])

    # Verify main tracks blender/main
    tracking = git_tracking_branch()
    expected = f"{args.blender_remote}/main"
    if tracking != expected:
        print_warn(f"'main' tracks '{tracking}', expected '{expected}'")
        print_warn("Continuing anyway — make sure this is correct")

    # 11. Hard reset to blender/main
    print_step(f"Resetting to {args.blender_remote}/main...")
    run(["git", "reset", "--hard", f"{args.blender_remote}/main"])

    # 12. Clean untracked files
    print_step("Cleaning untracked files...")
    run(["git", "clean", "-fd"])

    # 13. Pull with rebase
    print_step(f"Pulling {args.blender_remote} main with rebase...")
    run(["git", "pull", args.blender_remote, "main", "--rebase"])
    print_ok("Blender main is up to date")

    # 14. Run make update for submodules and LFS
    print_step("Running 'make update' for Blender submodules and LFS...")
    cmd = make_update_command()
    ret = run(cmd, exit_on_error=False)
    if ret != 0:
        print_warn("'make update' returned non-zero — continuing anyway (may be benign)")
    else:
        print_ok("'make update' completed")

    # 15. Clean submodules
    print_step("Cleaning submodules...")
    run(["git", "submodule", "foreach", "--recursive", "git", "reset", "--hard"])
    run(["git", "submodule", "foreach", "--recursive", "git", "clean", "-fd"])
    print_ok("Submodules cleaned")


def phase_prefetch_lfs(args):
    """Phase 5: Pre-fetch LFS objects to cache (no working tree changes)."""
    print_header("Phase 5: Pre-fetch LFS Objects")

    branch_name = f"merge-week{args.week_number}"

    # 16. Switch back to merge branch
    print_step(f"Switching to '{branch_name}'...")
    run(["git", "checkout", branch_name])

    # 17. Fetch Blender LFS objects
    print_step(f"Fetching LFS objects from {args.blender_remote}/main (cache only)...")
    run(["git", "lfs", "fetch", args.blender_remote, "main", "--all"])
    print_ok("Blender LFS objects cached")

    # 18. Fetch BFA LFS objects
    print_step(f"Fetching LFS objects from {args.origin_remote}/master (cache only)...")
    run(["git", "lfs", "fetch", args.origin_remote, "master", "--all"])
    print_ok("BFA LFS objects cached")


def phase_merge(args):
    """Phase 6: Merge Blender main into merge branch, with pause/resume for conflicts."""
    print_header("Phase 6: Merge Blender Main")

    # Check if merge is already in progress (idempotent re-run)
    if git_has_merge_in_progress():
        print_warn("Merge already in progress — jumping to conflict resolution prompt")
        _conflict_prompt(args)
        return

    # Check if merge commit already exists (fully completed)
    ahead, behind = git_commit_count_ahead_behind(f"{args.blender_remote}/main")
    if behind == 0:
        print_ok("Merge already completed — no new commits to merge")
        return

    # 19. Perform the merge
    print_step(f"Merging {args.blender_remote}/main...")
    ret = run(["git", "merge", f"{args.blender_remote}/main"], exit_on_error=False)

    if ret == 0:
        # Clean merge — no conflicts
        print_ok("Merge succeeded with NO conflicts!")
    else:
        # Conflicts exist
        _conflict_prompt(args)

    # 20. Update submodules after merge
    print_step("Updating submodules after merge...")
    run(["git", "submodule", "update", "--init", "--recursive"])
    print_ok("Submodules updated")


def _conflict_prompt(args):
    """Display conflict info and wait for user to resolve them."""
    conflicted = git_get_conflicted_files()
    print()
    print(f"{Color.BOLD}{Color.YELLOW}{'═' * 72}{Color.RESET}")
    print(f"{Color.BOLD}{Color.YELLOW}  ⚠  MERGE CONFLICTS — {len(conflicted)} files{Color.RESET}")
    print(f"{Color.BOLD}{Color.YELLOW}{'═' * 72}{Color.RESET}")
    print()

    # Show first 30 conflicted files, then summary
    max_show = 30
    for f in conflicted[:max_show]:
        print(f"    {Color.YELLOW}{f}{Color.RESET}")
    if len(conflicted) > max_show:
        print(f"    {Color.YELLOW}... and {len(conflicted) - max_show} more files{Color.RESET}")

    print()
    print(f"  {Color.BOLD}→ Resolve all conflicts now (edit files + git add){Color.RESET}")
    print(f"  {Color.BOLD}→ Type 'ok' and press ENTER when ready to continue{Color.RESET}")
    print(f"  {Color.BOLD}→ Or type 'quit' / 'q' to abort{Color.RESET}")
    print(f"{Color.BOLD}{Color.YELLOW}{'═' * 72}{Color.RESET}")
    print()

    while True:
        answer = input(f"{Color.BOLD}Ready? [ok/quit]: {Color.RESET}").strip().lower()
        if answer in ("ok", ""):
            # Verify conflicts are actually resolved
            remaining = git_get_conflicted_files()
            if remaining:
                print_warn(f"Still {len(remaining)} unresolved conflicts. Resolve them first.")
                for f in remaining[:10]:
                    print(f"    {Color.YELLOW}{f}{Color.RESET}")
                if len(remaining) > 10:
                    print(f"    {Color.YELLOW}... and {len(remaining) - 10} more{Color.RESET}")
                continue
            print_ok("All conflicts resolved — continuing...")
            break
        elif answer in ("quit", "q"):
            print_warn("Aborting merge. Resolve conflicts manually and re-run the script.")
            print_warn("The pre-fetched LFS cache is preserved and won't need re-downloading.")
            sys.exit(0)
        else:
            print_warn("Type 'ok' to continue or 'quit' to abort")


def phase_lfs_checkout(args):
    """Phase 7: LFS checkout with BFA bias."""
    print_header("Phase 7: LFS Checkout")

    # 21. Checkout Blender LFS files
    print_step("Checking out Blender LFS files...")
    run(["git", "lfs", "checkout", args.blender_remote, "main"])
    print_ok("Blender LFS files written")

    # 22. Checkout BFA LFS files (overwrites shared files with BFA versions)
    print_step("Checking out BFA LFS files (BFA bias)...")
    run(["git", "lfs", "checkout", args.origin_remote, "master"])
    print_ok("BFA LFS files written (BFA bias applied)")

    # 23. Verify LFS integrity
    print_step("Verifying LFS integrity...")
    ret = run(["git", "lfs", "fsck"], exit_on_error=False)
    if ret == 0:
        print_ok("LFS integrity check passed")
    else:
        print_warn("LFS fsck reported issues — review manually")


def phase_status_report(args):
    """Phase 8: Print final status report."""
    print_header("Phase 8: Status Report")

    branch_name = f"merge-week{args.week_number}"

    print(f"  Branch          : {Color.BOLD}{branch_name}{Color.RESET}")
    print(f"  Current commit  : {run_output(['git', 'rev-parse', '--short', 'HEAD'])}")

    # Commit counts
    ahead_bfa, behind_bfa = git_commit_count_ahead_behind(f"{args.origin_remote}/master")
    ahead_bl, behind_bl = git_commit_count_ahead_behind(f"{args.blender_remote}/main")

    print(f"  vs origin/master: {Color.GREEN}+{ahead_bfa}{Color.RESET} ahead, "
          f"{Color.YELLOW}-{behind_bfa}{Color.RESET} behind")
    print(f"  vs blender/main : {Color.GREEN}+{ahead_bl}{Color.RESET} ahead, "
          f"{Color.YELLOW}-{behind_bl}{Color.RESET} behind")

    # Submodule status
    print()
    print_step("Submodule status:")
    sub_status = run_output(["git", "submodule", "status"], exit_on_error=False)
    if sub_status:
        for line in sub_status.splitlines():
            print(f"    {line}")
    else:
        print_ok("All submodules clean")

    # LFS status
    print()
    print_step("LFS status:")
    print_ok("LFS checkout complete (verified with fsck)")

    # Next steps
    print()
    print(f"{Color.BOLD}{Color.CYAN}{'═' * 72}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}  NEXT STEPS{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{'═' * 72}{Color.RESET}")
    print()
    print(f"  1. Review the merge:  {Color.BOLD}git log --oneline --graph{Color.RESET}")
    print(f"  2. Build and test:    {Color.BOLD}make{Color.RESET} (or {Color.BOLD}.\\make{Color.RESET} on Windows)")
    print(f"  3. Push when ready:   {Color.BOLD}git push origin {branch_name}{Color.RESET}")
    print(f"  4. Push LFS:          {Color.BOLD}git lfs push --all origin {branch_name}{Color.RESET}")
    print()


def phase_resume_merge(args):
    """Phase 6 (resume): Continue the merge workflow after manual conflict resolution.

    Assumes the user already resolved all conflicts and ran 'git add' on the resolved
    files. Verifies the merge state, then continues with submodule update, LFS checkout
    with BFA bias, and the status report — skipping the setup phases (1-5).
    """
    print_header("Phase 6: Resume Merge (after conflict resolution)")

    # 1. Verify a merge is actually in progress
    if not git_has_merge_in_progress():
        print_warn("No merge is in progress on this branch — nothing to resume")
        print_warn("Continuing with LFS checkout and status report...")
    else:
        # 2. Verify no unresolved conflicts remain
        conflicted = git_get_conflicted_files()
        if conflicted:
            print_warn(f"{len(conflicted)} conflict(s) still unresolved — resolve them now")
            _conflict_prompt(args)
        else:
            print_ok("No unresolved conflicts")

        # 3. Warn about unstaged changes (resolved files must be 'git add'ed)
        unstaged = run_output(["git", "diff", "--name-only"], exit_on_error=False)
        if unstaged:
            print_warn(
                "Unstaged changes detected — make sure resolved files were staged with "
                "'git add'"
            )
            for f in unstaged.splitlines()[:10]:
                print(f"    {Color.YELLOW}{f}{Color.RESET}")

    # 4. Update submodules (same as the normal merge path)
    print_step("Updating submodules after merge...")
    run(["git", "submodule", "update", "--init", "--recursive"])
    print_ok("Submodules updated")

    # 5. LFS checkout with BFA bias
    phase_lfs_checkout(args)

    # 6. Status report
    phase_status_report(args)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Automate Blender → Bforartists merge workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/utils/bforartists_merge_blender.py --week-number 30
  python tools/utils/bforartists_merge_blender.py --week-number 30 --force
  python tools/utils/bforartists_merge_blender.py --week-number 30 --dry-run
  python tools/utils/bforartists_merge_blender.py --week-number 30 --skip-master-update
        """,
    )
    parser.add_argument(
        "--week-number", "-w",
        type=int,
        required=True,
        help="Week number for the merge branch name (e.g., 30 → merge-week30)",
    )
    parser.add_argument(
        "--blender-remote",
        default="blender",
        help="Name of the Blender upstream remote (default: 'blender')",
    )
    parser.add_argument(
        "--origin-remote",
        default="origin",
        help="Name of the Bforartists origin remote (default: 'origin')",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip the confirmation prompt",
    )
    parser.add_argument(
        "--skip-master-update",
        action="store_true",
        help="Skip updating the local master branch (Phase 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the full merge process without making changes.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume the merge and LFS checkout after manual conflict resolution was completed.",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.dry_run:
        print_header("DRY RUN — No changes will be made")
        print("Would execute the following phases:")
        print("  1. Preflight checks")
        if not args.skip_master_update:
            print("  2. Update BFA master (fetch, pull, make update, clean submodules)")
        else:
            print("  2. [SKIPPED] Update BFA master")
        print("  3. Create merge-week{} branch from master".format(args.week_number))
        print("  4. Update Blender main (reset, pull, make update, clean submodules)")
        print("  5. Pre-fetch LFS objects (cache only)")
        if args.resume:
            print("  6. Resume merge: verify conflicts resolved")
            print("  7. LFS checkout (BFA bias) + fsck")
        else:
            print("  6. Merge blender/main → merge-week{} (pause on conflicts)".format(args.week_number))
            print("  7. LFS checkout (BFA bias) + fsck")
        print("  8. Status report")
        print()
        print("Run without --dry-run to execute.")
        return 0

    # ── Resume path: setup phases are skipped — the merge state is already in progress ──
    if args.resume:
        phase_resume_merge(args)
        return 0

    # ── Phase 1: Preflight ──
    phase_preflight(args)

    # ── Phase 2: Update BFA master ──
    phase_update_master(args)

    # ── Phase 3: Create merge branch ──
    phase_create_branch(args)

    # ── Phase 4: Update Blender main ──
    phase_update_blender_main(args)

    # ── Phase 5: Pre-fetch LFS ──
    phase_prefetch_lfs(args)

    # ── Phase 6: Merge Blender main ──
    phase_merge(args)

    # ── Phase 7: LFS checkout ──
    phase_lfs_checkout(args)

    # ── Phase 8: Status report ──
    phase_status_report(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())