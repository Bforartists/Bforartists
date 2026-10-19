#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Build and upload the Bforartists Online Essentials asset library.

The library is Blender's Online Essentials (blender-assets repository, branch
"published", folder "publish/online") with the Bforartists changes from
`assets_bfa/online_essentials/` applied on top:

    thumbnails/               Replacement .webp thumbnails, same relative path as upstream
    blender_assets.cats.txt   (optional) Replacement catalog tree
    catalog_map.json          (optional) {"Asset name": "catalog path or UUID"}
    library.json              (optional) Library name / contact shown to users

No Bforartists build is needed: the listing JSON is patched and its hashes are
recalculated, so the upstream .blend files stay untouched.

Usage:
    python tools/utils/bforartists_online_essentials.py update             # pull + build + upload (asks first)
    python tools/utils/bforartists_online_essentials.py build              # build only, nothing uploaded
    python tools/utils/bforartists_online_essentials.py upload --dry-run   # show what would change online
    python tools/utils/bforartists_online_essentials.py find "clay strips" # where to put a new thumbnail

Help:
    python tools/utils/bforartists_online_essentials.py --help
"""

__all__ = (
    "main",
)

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path, PurePosixPath

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
OVERRIDES_DIR = REPO_ROOT / "assets_bfa" / "online_essentials"
DEFAULT_UPSTREAM = REPO_ROOT.parent / "blender-assets"
DEFAULT_BUILD_DIR = REPO_ROOT.parent / "bfa_online_essentials_build"
DEFAULT_REMOTE = "r2:bforartists-assets/essentials"
UPSTREAM_BRANCH = "published"
UPSTREAM_SUBDIR = Path("publish") / "online"

META_FILENAME = "_asset-library-meta.json"
CATS_FILENAME = "blender_assets.cats.txt"


class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text):
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 72}\n  {text}\n{'═' * 72}{Color.RESET}")


def print_ok(text):
    print(f"  {Color.GREEN}✓{Color.RESET} {text}")


def print_warn(text):
    print(f"  {Color.YELLOW}⚠ {text}{Color.RESET}")


def fail(text):
    print(f"  {Color.RED}✗ {text}{Color.RESET}")
    sys.exit(1)


def run(cmd, *, cwd=None, check=True):
    print(f"  $ {' '.join(str(x) for x in cmd)}")
    sys.stdout.flush()
    ret = subprocess.call([str(x) for x in cmd], cwd=cwd)
    if check and ret != 0:
        fail(f"Command failed with exit code {ret}")
    return ret


def confirm(question, assume_yes):
    if assume_yes:
        return True
    answer = input(f"\n  {Color.BOLD}{question} [y/N]{Color.RESET} ").strip().lower()
    return answer in {"y", "yes"}


# ---------------------------------------------------------------------------
# JSON + hashing (same scheme as Blender's `-c asset_listing generate`)
# ---------------------------------------------------------------------------

def sha256_of(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return "SHA256:" + digest.hexdigest()


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)


def url_to_relpath(url):
    """Listing URLs are relative and URL-quoted; return them as a plain relative path."""
    return PurePosixPath(urllib.parse.unquote(url.split("?", 1)[0]))


def parse_catalogs(cats_file):
    """Parse a catalog file into the listing's `catalogs` list (mirrors listing_asset_catalogs.py)."""
    by_uuid = {}
    for line in cats_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("VERSION "):
            continue
        parts = line.split(":", 2)
        if len(parts) < 2:
            fail(f"{cats_file}: unexpected line {line!r}")
        by_uuid[parts[0]] = (parts[1], parts[2] if len(parts) == 3 else "")

    by_path = {}
    for uuid, (path, simple_name) in by_uuid.items():
        entry = by_path.setdefault(path, {"path": path, "uuids": [], "simple_name": simple_name})
        entry["uuids"].append(uuid)
    return sorted(by_path.values(), key=lambda c: PurePosixPath(c["path"]))


def is_webp(path):
    with path.open("rb") as f:
        header = f.read(12)
    return header[:4] == b"RIFF" and header[8:12] == b"WEBP"


def is_lfs_pointer(path):
    with path.open("rb") as f:
        return f.read(40).startswith(b"version https://git-lfs")


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def upstream_dir(args):
    src = args.assets_repo / UPSTREAM_SUBDIR
    if not (src / META_FILENAME).exists():
        fail(f"No published library at {src}\n"
             f"    Clone it next to Bforartists:  git clone https://projects.blender.org/blender/blender-assets.git\n"
             f"    or pass --assets-repo <path>")
    return src


def step_pull(args):
    print_header("1. Pull Blender's published Online Essentials")
    repo = args.assets_repo
    upstream_dir(args)
    run(["git", "fetch", "origin"], cwd=repo)
    run(["git", "switch", UPSTREAM_BRANCH], cwd=repo)
    run(["git", "pull", "--ff-only"], cwd=repo)
    run(["git", "lfs", "pull"], cwd=repo)
    print_ok(f"{repo} is up to date on '{UPSTREAM_BRANCH}'")


def step_build(args):
    print_header("2. Build the Bforartists library")
    src = upstream_dir(args)
    out = args.build_dir

    branch = subprocess.run(["git", "branch", "--show-current"], cwd=args.assets_repo,
                            capture_output=True, text=True).stdout.strip()
    if branch != UPSTREAM_BRANCH:
        print_warn(f"blender-assets is on '{branch}', not '{UPSTREAM_BRANCH}' (what Blender publishes)")

    blend_files = list(src.rglob("*.blend"))
    if blend_files and is_lfs_pointer(blend_files[0]):
        fail("The .blend files are Git LFS pointers. Run 'git lfs pull' in blender-assets first.")

    # Fresh copy of upstream.
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns(".last_modified"))
    print_ok(f"Copied upstream ({len(blend_files)} .blend files) → {out}")

    meta_path = out / META_FILENAME
    meta = load_json(meta_path)
    index_rel = url_to_relpath(meta["api_versions"]["v1"]["url"])
    index_path = out / index_rel
    index = load_json(index_path)
    pages = [(out / url_to_relpath(p["url"]), load_json(out / url_to_relpath(p["url"])))
             for p in index["pages"]]
    assets = [asset for _path, page in pages for asset in page["assets"]]

    # Thumbnails.
    thumbs_dir = OVERRIDES_DIR / "thumbnails"
    overrides = {}
    if thumbs_dir.exists():
        for f in thumbs_dir.rglob("*"):
            if f.is_file() and f.name != ".gitkeep":
                overrides[PurePosixPath(f.relative_to(thumbs_dir).as_posix())] = f

    replaced = 0
    for asset in assets:
        thumb = asset.get("thumbnail")
        if not thumb:
            continue
        rel = url_to_relpath(thumb["url"])
        src_file = overrides.pop(rel, None)
        if src_file is None:
            continue
        if not is_webp(src_file):
            fail(f"{src_file} is not a .webp image. Export it as WebP (same file name).")
        dst = out / rel
        shutil.copyfile(src_file, dst)
        thumb["hash"] = sha256_of(dst)
        replaced += 1
    print_ok(f"Thumbnails replaced: {replaced}")
    for rel in sorted(overrides):
        print_warn(f"Thumbnail not used, no asset has this path: thumbnails/{rel}  "
                   f"(check the name with the 'find' command)")

    # Catalogs.
    cats_override = OVERRIDES_DIR / CATS_FILENAME
    if cats_override.exists():
        shutil.copyfile(cats_override, out / CATS_FILENAME)
        print_ok("Catalog tree replaced from assets_bfa/online_essentials")
    catalogs = parse_catalogs(out / CATS_FILENAME)
    index["catalogs"] = catalogs

    catalog_map_path = OVERRIDES_DIR / "catalog_map.json"
    if catalog_map_path.exists():
        catalog_map = load_json(catalog_map_path)
        path_to_uuid = {c["path"]: c["uuids"][0] for c in catalogs}
        known_uuids = {u for c in catalogs for u in c["uuids"]}
        by_name = {}
        for asset in assets:
            by_name.setdefault(asset["name"], []).append(asset)
        moved = 0
        for name, target in catalog_map.items():
            if name.startswith("_"):
                continue  # Comments.
            uuid = target if target in known_uuids else path_to_uuid.get(target)
            if uuid is None:
                fail(f"catalog_map.json: catalog {target!r} (for {name!r}) is not in the catalog tree")
            if name not in by_name:
                print_warn(f"catalog_map.json: no asset named {name!r}")
                continue
            for asset in by_name[name]:
                asset.setdefault("meta", {})["catalog_id"] = uuid
                moved += 1
        print_ok(f"Assets moved to another catalog: {moved}")

    # Library name / contact.
    library_path = OVERRIDES_DIR / "library.json"
    if library_path.exists():
        library = {k: v for k, v in load_json(library_path).items() if not k.startswith("_")}
        meta.update(library)
        print_ok(f"Library name: {meta.get('name')}")

    # Re-hash: pages → index → meta.
    for (page_path, page), page_ref in zip(pages, index["pages"]):
        save_json(page, page_path)
        page_ref["hash"] = sha256_of(page_path)
    save_json(index, index_path)
    meta["api_versions"]["v1"]["hash"] = sha256_of(index_path)
    save_json(meta, meta_path)
    print_ok(f"Listing rebuilt: {len(assets)} assets, {len(catalogs)} catalogs")
    print_ok(f"Test it locally: add {out} as an asset library in Preferences → File Paths")


def step_upload(args):
    print_header("3. Upload to " + args.remote)
    out = args.build_dir
    if not (out / META_FILENAME).exists():
        fail(f"Nothing built at {out}. Run the 'build' command first.")
    if shutil.which("rclone") is None:
        fail("rclone is not installed. See the wiki page 'Server 2.0 Overview'.")

    run(["rclone", "sync", out, args.remote, "--checksum", "--dry-run"], check=False)
    if args.dry_run:
        print_ok("Dry run only, nothing uploaded")
        return
    if not confirm("Upload these changes? They are public immediately.", args.yes):
        print_warn("Upload skipped")
        return
    run(["rclone", "sync", out, args.remote, "--checksum", "--progress"])
    run(["rclone", "check", out, args.remote, "--one-way"])
    print_ok("Online Essentials are live")


def cmd_find(args):
    out = args.build_dir if (args.build_dir / META_FILENAME).exists() else upstream_dir(args)
    meta = load_json(out / META_FILENAME)
    index = load_json(out / url_to_relpath(meta["api_versions"]["v1"]["url"]))
    text = args.text.lower()
    found = 0
    for page_ref in index["pages"]:
        for asset in load_json(out / url_to_relpath(page_ref["url"]))["assets"]:
            if text in asset["name"].lower() and asset.get("thumbnail"):
                rel = url_to_relpath(asset["thumbnail"]["url"])
                print(f"  {Color.BOLD}{asset['name']}{Color.RESET} ({asset['id_type'].lower()})")
                print(f"    → assets_bfa/online_essentials/thumbnails/{rel}")
                found += 1
    if not found:
        print_warn(f"No asset name contains {args.text!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        description="Build and upload the Bforartists Online Essentials asset library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:", 1)[1],
    )
    parser.add_argument("command", choices=("update", "build", "upload", "find"))
    parser.add_argument("text", nargs="?", help="Asset name to search for ('find' only)")
    parser.add_argument("--assets-repo", type=Path, default=DEFAULT_UPSTREAM,
                        help=f"Blender's blender-assets clone (default: {DEFAULT_UPSTREAM})")
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR,
                        help=f"Where the library is built (default: {DEFAULT_BUILD_DIR})")
    parser.add_argument("--remote", default=DEFAULT_REMOTE,
                        help=f"rclone destination (default: {DEFAULT_REMOTE})")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded, upload nothing")
    parser.add_argument("--yes", "-y", action="store_true", help="Upload without asking")
    parser.add_argument("--skip-pull", action="store_true", help="'update' without pulling blender-assets")
    args = parser.parse_args(argv)
    if args.command == "find" and not args.text:
        parser.error("'find' needs a search text, e.g. find \"clay strips\"")
    return args


def main(argv=None):
    args = parse_arguments(argv)
    if args.command == "find":
        cmd_find(args)
    elif args.command == "build":
        step_build(args)
    elif args.command == "upload":
        step_upload(args)
    elif args.command == "update":
        if not args.skip_pull:
            step_pull(args)
        step_build(args)
        step_upload(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
