#!/usr/bin/env python3
"""
Blender Weekly Report Generator

Generates a devtalk-style weekly changelog from the Blender git repository.
By default filters out fixes, cleanups, and minor performance changes to focus on
exciting, human-readable features and improvements.

Can run in two modes:
  1. Local repo:  point --repo at a full local clone of Blender.
  2. Remote mode: omit --repo and it auto-clones a shallow, blobless copy
     (metadata only, ~1.2 MB) and fetches only the requested date range.

Usage:
    python weekly_report.py                           # Remote mode, last 7 full days
    python weekly_report.py --repo /path/to/blender   # Local repo mode
    python weekly_report.py --since 2026-06-11 --until 2026-05-18
    python weekly_report.py --since 2026-06-11
    python weekly_report.py --show-all                 # Include fixes/cleanups
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ── Remote repository configuration ───────────────────────────────────────
# When --repo is not given, the script auto-clones a shallow copy of Blender.
BLENDER_REPO_URL = "https://github.com/blender/blender.git"
REPO_DIR_NAME = ".blender-src"

# ── Category lookup table ──────────────────────────────────────────────────
# Each entry: (display_name, [list of case-insensitive substrings to match])
# Matches are checked against the subject line and commit body.
CATEGORY_KEYWORDS = [
    ("Animation", [
        "anim:", "fcurve", "f-curve", "action ", "armature",
        "pose ", "keyframe", "motion path", "graph editor", "nla",
        "driver:", "rigify", "pose slide", "bone ",
    ]),
    ("Assets", [
        "asset", "asset library", "online asset", "remote asset",
        "essentials", "catalog",
    ]),
    ("Compositor", [
        "compositor", "composite", "stabilize 2d", "gpu compositor",
    ]),
    ("Core", [
        "core:", "liboverride", "liboverride", "copy-paste", "i18n",
        "ghost/wayland", "ghost/cocoa", "ghost/", "python api",
        "imbuf", "image:", "blenloader", "deps:",
        "benchmark", "bke_", "bli_", "render:", "object:",
    ]),
    ("Cycles", [
        "cycles:", "hip/", "hip-rt", "cuda", "oneapi", "optix", "mnee",
        "denoising", "osl", "bvh", "principled bsdf",
        "thin wall", "thin glass", "raytrace",
    ]),
    ("EEVEE", [
        "eevee:", "eevee", "bsl", "gbuffer", "hiz", "cryptomatte",
        "lightprobe", "raycast", "deferred", "lookdev", "surfel",
        "shadow pool", "pixel jitter", "depth of field",
    ]),
    ("Functions", ["functions"]),
    ("GPU", [
        "gpu:", "vulkan:", "metal:", "opengl", "shader tool",
        "compute", "resource table", "shadercreateinfo",
    ]),
    ("Geometry Nodes", [
        "geometry nodes", "geometry node", "geo nodes",
        "xpbd", "hair physics", "cloth dynamics",
        "solver node", "bundle type", "switch node",
        "get attribute names", "reverse string",
    ]),
    ("Grease Pencil", ["grease pencil", "gpencil", "gp_"]),
    ("I/O", [
        "io:", "alembic:", "gltf:", "ffmpeg", "obj:", "usd:",
        "ply:", "stl:", "export", "import",
    ]),
    ("LineArt", ["lineart", "line art"]),
    ("Modeling", [
        "bmesh", "bm_", "modeling:", "mesh:",
        "multires", "subdivide", "unsubdivide",
        "remesh", "points to curves", "looptools",
        "space evenly",
    ]),
    ("Nodes", [
        "nodes:", "node tool", "node group", "reroute",
        "swap node", "move to nodes",
    ]),
    ("Outliner", ["outliner:", "outliner"]),
    ("Paint", [
        "paint:", "texture paint", "clone brush",
        "weight paint", "vertex paint", "brush",
    ]),
    ("Selection", ["selection", "select overlap"]),
    ("Shader Nodes", [
        "shader editor", "shader node", "shader nodes",
        "shader group", "scene time node",
    ]),
    ("UI", [
        "ui:", "ui/", "text-box", "tree view", "tooltip",
        "scrubbing", "popover", "template", "grip", "icon",
        "button text", "arrow keys",
    ]),
    ("VSE", [
        "vse:", "sequencer", "strip", "channel",
        "text strip", "scene strip", "video stream", "audio stream",
    ]),
    ("Windows Engine", ["windows"]),
    ("Workbench", ["workbench:"]),
]

# ── Filters: commits to EXCLUDE from the report ───────────────────────────

def is_cleanup(subject):
    """Check if commit is purely cleanup/maintenance."""
    return bool(re.match(r"^(Cleanup|cleanup)\b", subject, re.IGNORECASE))


def is_fix(subject):
    """Check if commit is a bugfix."""
    # Catches "Fix #123456: ...", "Fix: ...", "Assets: fix possible ..."
    if re.match(r"^Fix\b", subject, re.IGNORECASE):
        return True
    # Also catch "<Category>: fix ..." style
    if re.match(r"^[A-Za-z/]+:\s*[Ff]ix\b", subject):
        return True
    return False


def is_performance_only(subject, body):
    """
    Check if commit is performance-only with no feature changes.
    """
    perf_pattern = re.compile(
        r"^(performance|perf|speed up|reduce |optimize|tune|improve |faster)\b",
        re.IGNORECASE
    )
    if perf_pattern.match(subject):
        # Check if body has any feature-like language
        feature_hints = ["add", "new", "support", "implement", "expose"]
        body_lower = (body or "").lower()
        if not any(hint in body_lower[:200] for hint in feature_hints):
            return True
    return False


def is_test_only(subject):
    """Check if commit is test-only."""
    if re.match(r"^(Tests|tests)\b", subject):
        return True
    if "add unit test" in subject.lower() or "add test" in subject.lower():
        return True
    return False


def is_refactor(subject):
    """Check if commit is refactoring with no user-facing change."""
    return bool(re.match(r"^(Refactor|refactor)\b", subject, re.IGNORECASE))


def is_cleanup_or_fix_in_body(subject, body):
    """
    Check if a commit body reveals it as a fix/cleanup even if the
    subject line isn't clearly one. Catches things like a Fix or Cleanup
    reference in the body with no new feature description.
    """
    if not body:
        return False
    body_lower = body.lower()
    # If the body says "fix #" with no feature description, it's a fix
    has_fix_ref = bool(re.search(r"\b(fix|fixes|fixed)\s+#\d+", body_lower))
    has_cleanup_ref = "cleanup" in body_lower[:100]
    has_feature_desc = any(w in body_lower[:200] for w in ["add", "new", "implement", "support for"])
    # If it has a fix reference but no feature description, treat as fix
    if has_fix_ref and not has_feature_desc:
        return True
    return False


def is_trivial_change(subject, body):
    """
    Catch miscellaneous trivial changes: typo fixes, comment fixes,
    version bumps, silence warnings, test threshold updates, etc.
    """
    trivia = [
        r"threshold", r"typo", r"comment", r"punctuation",
        r"silence warning", r"remove unused", r"rename leftover",
        r"update test fail", r"test blocklist", r"versioning",
        r"i18n.*translat", r"gitea.*section",
    ]
    for pattern in trivia:
        if re.search(pattern, subject, re.IGNORECASE):
            return True
    return False


def should_skip(subject, body):
    """
    Determine if a commit should be excluded from the report.
    Returns True if the commit should be skipped.
    """
    if is_cleanup(subject):
        return True
    if is_fix(subject):
        return True
    if is_test_only(subject):
        return True
    if is_performance_only(subject, body):
        return True
    if is_refactor(subject):
        return True
    if is_trivial_change(subject, body):
        return True
    if is_cleanup_or_fix_in_body(subject, body):
        return True
    return False


# ── Remote repository helpers ─────────────────────────────────────────────
# These handle the self-contained shallow clone mode (when --repo is omitted).


def _resolve_since_date(since_arg):
    """Convert a git-style date string like '7 days ago' to YYYY-MM-DD."""
    try:
        # Try parsing as a natural date via git
        result = subprocess.run(
            ["git", "log", "-1", f"--before={since_arg}", "--format=%cI"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            dt = datetime.fromisoformat(result.stdout.strip())
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    # Fallback: assume it's already YYYY-MM-DD or subtract days
    try:
        dt = datetime.strptime(since_arg, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    # Try "N days/weeks ago" style
    m = re.match(r"(\d+)\s+(day|days|week|weeks)\s+ago", since_arg.lower())
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        days = num * 7 if "week" in unit else num
        dt = datetime.now() - timedelta(days=days)
        return dt.strftime("%Y-%m-%d")
    # Last resort: 7 days ago
    return (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")


def _script_dir():
    """Return the directory where this script lives."""
    return Path(__file__).parent.resolve()


def ensure_shallow_repo(since_date, repo_url=None):
    """
    Create or update a shallow, blobless clone of the Blender repository.
    Returns the Path to the repo directory.
    """
    url = repo_url or BLENDER_REPO_URL
    repo_dir = _script_dir() / REPO_DIR_NAME

    if repo_dir.exists():
        print(f"📡 Updating existing shallow clone in {repo_dir}…", file=sys.stderr)
        subprocess.run(
            ["git", "fetch", "--shallow-since", since_date, "origin", "main"],
            cwd=repo_dir, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "update-ref", "HEAD", "origin/main"],
            cwd=repo_dir, check=True, capture_output=True,
        )
        print("✅ Shallow clone updated.", file=sys.stderr)
    else:
        print(f"📥 Creating shallow clone (metadata only, no code files)…", file=sys.stderr)
        print(f"    since {since_date}", file=sys.stderr)
        subprocess.run(
            [
                "git", "clone",
                "--filter=blob:none",
                "--no-checkout",
                "--shallow-since", since_date,
                "--single-branch", "--branch", "main",
                url, str(repo_dir),
            ],
            check=True, capture_output=True,
        )
        print(f"✅ Shallow clone created at {repo_dir}", file=sys.stderr)

    return repo_dir


# ── Parsing helpers ───────────────────────────────────────────────────────

def _run_git(args):
    """Run a git command and return stdout as text, handling Unicode properly."""
    try:
        result = subprocess.run(
            args, capture_output=True, check=True, cwd=REPO_PATH,
            encoding="utf-8", errors="replace"
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def get_commit_body(hash):
    """Get the full commit body (description) for a given commit hash."""
    return _run_git(["git", "log", "-1", "--format=%b", hash]).strip()


def extract_pr_link(body):
    """Extract Pull Request URL from commit body."""
    if not body:
        return None
    # Full PR URL
    m = re.search(r"Pull Request:\s*(https://projects\.blender\.org/blender/blender/pulls/\d+)", body)
    if m:
        return m.group(1)
    # Ref style: Ref !158876
    m = re.search(r"Ref\s+!(\d+)", body)
    if m:
        return f"https://projects.blender.org/blender/blender/pulls/{m.group(1)}"
    return None


def extract_issue_links(subject, body):
    """Extract issue references (#123456) from subject or body."""
    issues = []
    text = f"{subject} {body or ''}"
    for m in re.finditer(r"#(\d{4,6})", text):
        issue_num = m.group(1)
        issues.append(f"https://projects.blender.org/blender/blender/issues/{issue_num}")
    return issues


def get_commit_link(hash):
    """Build the commit URL."""
    return f"https://projects.blender.org/blender/blender/commit/{hash}"


def categorize(subject, body):
    """
    Assign a commit to a category based on subject prefix and body content.
    Returns a category name string.
    """
    text = f"{subject} {body or ''}".lower()

    for category, keywords in CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in text:
                return category

    return "Other"


def get_commits(since, until):
    """Get list of commits with hash, author, subject between dates."""
    stdout = _run_git([
        "git", "log",
        f"--since={since}",
        f"--until={until}",
        "--format=%H|%an|%s",
        "--reverse"
    ])
    commits = []
    for line in stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "subject": parts[2],
            })
    return commits


# ── Report generation ─────────────────────────────────────────────────────

def generate_report(commits, show_all=False, since_date=None, until_date=None):
    """
    Generate the markdown report from the filtered and categorized commits.

    If show_all is True, fixes/cleanups/refactors are included in the output
    (mirroring parsero's inclusive behavior).
    """
    # ── Stats counters (inspired by parsero) ──
    nr_fix = 0
    nr_cleanup = 0
    nr_refactor = 0

    interesting = []
    for c in commits:
        body = get_commit_body(c["hash"])
        skipped = should_skip(c["subject"], body)
        if skipped and not show_all:
            continue
        c["body"] = body
        c["category"] = categorize(c["subject"], body)
        c["pr_link"] = extract_pr_link(body)
        c["issue_links"] = extract_issue_links(c["subject"], body)
        c["commit_link"] = get_commit_link(c["hash"])
        interesting.append(c)

        # Count stats for the stats line
        if is_fix(c["subject"]):
            nr_fix += 1
        if is_cleanup(c["subject"]):
            nr_cleanup += 1
        if is_refactor(c["subject"]):
            nr_refactor += 1

    # Group by category
    grouped = defaultdict(list)
    for c in interesting:
        grouped[c["category"]].append(c)

    # Sort categories: put "Other" at the end, rest alphabetically
    def sort_key(item):
        cat, _ = item
        return (1 if cat == "Other" else 0, cat)

    report_lines = []

    # ── Header ──
    report_lines.append(f"# Weekly Blender Report")
    report_lines.append("")
    if since_date and until_date:
        report_lines.append(f"**{since_date} → {until_date}**")
        report_lines.append("")
    report_lines.append("Notes for weekly communication of ongoing projects and modules.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## New Features and Changes")
    report_lines.append("")

    # ── Stats bar ──
    total_original = len(commits)
    total_shown = len(interesting)
    nr_features = total_shown - nr_fix - nr_cleanup - nr_refactor
    report_lines.append(
        f"> ✨ {total_shown} changes this week "
        f"({nr_features} features, {nr_fix} fixes, {nr_cleanup} cleanup, {nr_refactor} refactor) "
        f"out of {total_original} total commits."
    )
    report_lines.append("")

    for category, items in sorted(grouped.items(), key=sort_key):
        if not items:
            continue
        report_lines.append(f"### {category}")
        report_lines.append("")

        for c in items:
            # Build the entry line
            entry = f"• {c['subject']} ([commit]({c['commit_link']}))"

            # Add PR link if available
            if c["pr_link"]:
                entry = entry.replace("([commit]", f"([PR]({c['pr_link']}), [commit]")

            # Add issue links if no PR link
            if not c["pr_link"] and c["issue_links"]:
                for i, issue_url in enumerate(c["issue_links"]):
                    entry = entry.replace("([commit]", f"([issue #{issue_url.split('/')[-1]}]({issue_url}), [commit]")

            entry += f" — ({c['author']})"
            report_lines.append(entry)

            # Add short description (first paragraph of body, if meaningful)
            if c["body"]:
                # Strip PR/Ref lines from description
                desc = re.sub(r"Pull Request:.*", "", c["body"])
                desc = re.sub(r"Ref\s+!\d+.*", "", desc)
                desc = re.sub(r"Co-authored-by:.*", "", desc)
                desc = re.sub(r"See PR description.*", "", desc)
                desc = re.sub(r"Design task:.*", "", desc)
                desc = re.sub(r"Part of.*", "", desc)
                desc = desc.strip()
                if desc and len(desc) > 20:
                    # Take first paragraph only
                    first_para = desc.split("\n\n")[0].strip()
                    # Collapse hard line-wraps into a single flowing paragraph.
                    # A newline followed by a lowercase letter or number means
                    # it's likely a hard wrap, join it. A newline followed by
                    # a capital letter or bullet could be a real sentence break,
                    # but in commit messages those are also often wraps.
                    # Strategy: join all consecutive lines, but preserve
                    # intentional paragraph breaks (handled above).
                    first_para = re.sub(r"\n+", " ", first_para)
                    # Collapse multiple spaces
                    first_para = re.sub(r" {2,}", " ", first_para)
                    if len(first_para) > 30:
                        report_lines.append(f"  > {first_para[:500]}")
                        if len(first_para) > 500:
                            report_lines[-1] += "…"
                        report_lines.append("")

        report_lines.append("")

    # ── Footer ──
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("This is a selection of changes that happened over the last week. "
                        "For a full overview including fixes, code-only changes and more visit "
                        f"[projects.blender.org](https://projects.blender.org/blender/blender/commits/branch/main).")
    if show_all:
        report_lines.append("")
        report_lines.append("> *Report mode: `--show-all` — includes fixes, cleanups, and refactors.*")
    report_lines.append("")

    return "\n".join(report_lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a Blender weekly report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--since", default=None,
                        help="Start date (YYYY-MM-DD or relative like '7 days ago'). "
                             "Default: 7 days before --until.")
    parser.add_argument("--until", default=None,
                        help="End date (YYYY-MM-DD). Default: today")
    parser.add_argument("--repo", default=None,
                        help="Path to local git repository. If omitted, auto-clones "
                             "a shallow copy (metadata only, ~1.2 MB).")
    parser.add_argument("--remote-url", default=None,
                        help=f"Remote repository URL (default: {BLENDER_REPO_URL})")
    parser.add_argument("--show-all", action="store_true",
                        help="Include fixes, cleanups, and refactors in the report "
                             "(like parsero's inclusive behavior)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output file path (default: auto-saves to reports/ folder)")
    parser.add_argument("--print", "-p", action="store_true", dest="print_stdout",
                        help="Also print the report to stdout")
    args = parser.parse_args()

    global REPO_PATH

    # Default: last 7 days as concrete dates.
    today = datetime.now().strftime("%Y-%m-%d")
    since = args.since or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    until = args.until or today

    # ── Resolve repository ──
    if args.repo:
        # Use existing local repo (original behavior)
        REPO_PATH = args.repo
        print(f"🔍 Using local repository: {REPO_PATH}", file=sys.stderr)
    else:
        # Self-contained mode: shallow clone from remote
        since_date = _resolve_since_date(since)
        print(f"🔍 No local repo specified — using remote mode.", file=sys.stderr)
        print(f"   Shallow clone will fetch commits since {since_date}", file=sys.stderr)
        REPO_PATH = str(ensure_shallow_repo(since_date, args.remote_url))

    print(f"📅 Scanning commits from {since} to {until} in {REPO_PATH}...", file=sys.stderr)

    commits = get_commits(since, until)
    print(f"📥 Found {len(commits)} total commits.", file=sys.stderr)

    # Resolve display dates for the report header.
    report_since = _resolve_since_date(since)
    report_until = until
    report = generate_report(commits, show_all=args.show_all,
                             since_date=report_since, until_date=report_until)

    # ── Auto-save to file ──
    date_range = f"{report_since}__{report_until}"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    output_path = args.output or os.path.join(
        reports_dir, f"weekly-report-{date_range}.md"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Report saved to {output_path}", file=sys.stderr)

    # ── Also print to stdout (always, so you can preview or pipe) ──
    if args.print_stdout or args.output is None:
        print(report)


if __name__ == "__main__":
    main()