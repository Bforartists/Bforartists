#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# bforartists_linux_builder.sh
#
# Linux builds of Bforartists from WSL (or any Ubuntu/Debian machine), inside the same
# Rocky Linux 8 environment Blender uses for its official builds, so the result runs on
# old and new distros and includes the Cycles GPU kernels (CUDA 12.8 + HIP/ROCm 7.2.1).
#
# The source and the build live in the Linux file system ($BFA_HOME, default ~/bfa), never
# under /mnt/c: builds there are many times slower.
#
#   ~/bfa/Bforartists                 the source (its own clone, separate from Windows)
#   ~/bfa/bfa_build_linux_release     the build (`make release`)
#   ~/bfa/build_output/tar            packaged tarballs
#   ~/bfa/logs                        one log per run
#   ~/bfa/bin                         a copy of this script (what the weekly task runs)
#
# Usage:
#   bforartists_linux_builder.sh setup     once: host tools (podman, git-lfs, rclone ...) + clone
#   bforartists_linux_builder.sh image     once (and when Blender changes its Rocky 8 setup):
#                                          build the container image (about 25 GB, 30-60 min)
#   bforartists_linux_builder.sh weekly    update + build + package + upload: the scheduled run
#
#   Single steps: update, build, package, upload, shell, status
#
# Environment (defaults):
#   BFA_HOME              ~/bfa
#   BFA_BRANCH            master
#   BFA_PACKAGE           devbuild      devbuild = linux-devbuild-DD-MM-YYYY.tar.xz
#                                       release  = Bforartists-X.Y.Z-Linux.tar.xz (Flathub's input)
#   BFA_IMAGE             bforartists-rocky8
#   BFA_JOBS              auto          parallel compile jobs (auto: fits the WSL memory)
#   BFA_DEVBUILDS_REMOTE  (unset)       rclone destination, e.g. "bfa-devbuilds:bforartists-devbuilds"
#                                       unset = no upload. The rclone remote and its R2 key are set
#                                       up once with `rclone config`; the key never goes in Git.
#   BFA_KEEP              4             how many devbuild tarballs to keep locally

set -euo pipefail

BFA_HOME="${BFA_HOME:-$HOME/bfa}"
BFA_BRANCH="${BFA_BRANCH:-master}"
BFA_PACKAGE="${BFA_PACKAGE:-devbuild}"
BFA_IMAGE="${BFA_IMAGE:-bforartists-rocky8}"
BFA_KEEP="${BFA_KEEP:-4}"
REPO="$BFA_HOME/Bforartists"
BUILD_DIR="$BFA_HOME/bfa_build_linux_release"
OUTPUT_DIR="$BFA_HOME/build_output"
LOG_DIR="$BFA_HOME/logs"
REPO_URL="https://github.com/Bforartists/Bforartists.git"
BLENDER_URL="https://projects.blender.org/blender/blender.git"

# ---------------- Output ---------------- #

if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi
info() { printf "${BLUE}▶ %s${NC}\n" "$*"; }
ok()   { printf "${GREEN}✔ %s${NC}\n" "$*"; }
warn() { printf "${YELLOW}⚠ %s${NC}\n" "$*" >&2; }
die()  { printf "${RED}✘ %s${NC}\n" "$*" >&2; exit 1; }

# ---------------- Helpers ---------------- #

podman_cmd() {
  # WSL without systemd has no cgroup manager for rootless Podman.
  if [ "$(ps -p 1 -o comm= 2>/dev/null)" = "systemd" ]; then
    podman "$@"
  else
    podman --cgroup-manager=cgroupfs --events-backend=file "$@"
  fi
}

auto_jobs() {
  # Linking and CUDA/HIP kernels take 2+ GB per job: cap the jobs by memory.
  local cpus mem_gb by_mem
  cpus=$(nproc)
  mem_gb=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))
  by_mem=$(( mem_gb / 2 ))
  [ "$by_mem" -lt 1 ] && by_mem=1
  [ "$by_mem" -lt "$cpus" ] && echo "$by_mem" || echo "$cpus"
}

# Run a command inside the Rocky 8 build container, with $BFA_HOME mounted at the same path.
in_container() {
  mkdir -p "$BFA_HOME/.container-home"
  podman_cmd run --rm --userns=keep-id \
    -v "$BFA_HOME:$BFA_HOME" \
    -w "$REPO" \
    -e HOME="$BFA_HOME/.container-home" \
    -e NPROCS="${BFA_JOBS:-$(auto_jobs)}" \
    -e BFA_BUILD_DIR="$BUILD_DIR" \
    -e OUTPUT_DIR="$OUTPUT_DIR" \
    -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0='*' \
    "$BFA_IMAGE" \
    bash -lc "source scl_source enable gcc-toolset-14 \
      && export PATH=/usr/local/cuda/bin:/opt/rocm/bin:\$PATH \
      && export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\${LD_LIBRARY_PATH:-} \
      && $1"
}

need_repo() {
  [ -d "$REPO/.git" ] || die "No source in $REPO. Run: $0 setup"
}

need_image() {
  podman_cmd image exists "$BFA_IMAGE" || die "No build image '$BFA_IMAGE'. Run: $0 image"
}

# ---------------- Commands ---------------- #

cmd_setup() {
  command -v apt-get >/dev/null || die "This setup expects Ubuntu/Debian (apt). Install podman, git, git-lfs, python3, make, xz-utils and rclone by hand."
  info "Installing host tools (asks for your password once)"
  sudo apt-get update
  sudo apt-get install -y podman uidmap slirp4netns fuse-overlayfs git git-lfs python3 make \
    xz-utils rclone ca-certificates
  git lfs install --skip-repo
  ok "Host tools installed"

  mkdir -p "$BFA_HOME" "$LOG_DIR" "$BFA_HOME/bin" "$OUTPUT_DIR"
  if [ ! -d "$REPO/.git" ]; then
    info "Cloning Bforartists into $REPO (large: source + LFS)"
    git clone "$REPO_URL" "$REPO"
    git -C "$REPO" remote add blender "$BLENDER_URL" || true
  else
    ok "Source already at $REPO"
  fi

  # The scheduled task runs this copy, so it keeps working whatever branch is checked out.
  cp "$(readlink -f "$0")" "$BFA_HOME/bin/bforartists_linux_builder.sh"
  chmod +x "$BFA_HOME/bin/bforartists_linux_builder.sh"
  ok "Installed $BFA_HOME/bin/bforartists_linux_builder.sh"

  case "$(df -BG --output=avail "$BFA_HOME" | tail -1 | tr -dc 0-9)" in
    ''|[0-9]|[0-9][0-9]) warn "Less than 100 GB free for $BFA_HOME: image + libraries + build need about 80 GB" ;;
  esac
  ok "Setup done. Next: $0 image"
}

cmd_image() {
  need_repo
  local ctx script
  ctx=$(mktemp -d)
  script="$REPO/build_files/build_environment/linux/linux_rocky8_setup.sh"
  [ -f "$script" ] || die "Missing $script"
  # Blender's script reads the architecture with `uname -i`, which can print "unknown";
  # `uname -m` is always set.
  sed 's/uname -i/uname -m/' "$script" > "$ctx/linux_rocky8_setup.sh"
  cat > "$ctx/Containerfile" <<'EOF'
FROM docker.io/rockylinux/rockylinux:8
COPY linux_rocky8_setup.sh /tmp/linux_rocky8_setup.sh
RUN bash /tmp/linux_rocky8_setup.sh && dnf clean all && rm -rf /var/cache/dnf /tmp/linux_rocky8_setup.sh
EOF
  info "Building the Rocky 8 build image '$BFA_IMAGE' (gcc-toolset-14, CUDA 12.8, ROCm 7.2.1)"
  podman_cmd build -t "$BFA_IMAGE" "$ctx"
  rm -rf "$ctx"
  ok "Image ready: $(podman_cmd image inspect "$BFA_IMAGE" --format '{{.Size}}' | awk '{printf "%.1f GB", $1/1e9}')"
}

cmd_update() {
  need_repo
  info "Updating $BFA_BRANCH and the precompiled libraries"
  cd "$REPO"
  if [ -n "$(git status --porcelain --untracked-files=no -- . ':(exclude)lib')" ]; then
    die "Local changes in $REPO; this clone is for builds only. Commit, stash or reset them."
  fi
  git fetch origin --prune
  git checkout "$BFA_BRANCH"
  git pull --rebase origin "$BFA_BRANCH"
  make update
  ok "Source at $(git rev-parse --short HEAD) ($(git log -1 --format=%s | cut -c1-70))"
}

cmd_build() {
  need_repo; need_image
  info "Building (make release) with ${BFA_JOBS:-$(auto_jobs)} jobs"
  in_container "make release"
  [ -x "$BUILD_DIR/bin/bforartists" ] || die "Build finished but $BUILD_DIR/bin/bforartists is missing"
  ok "Built: $("$BUILD_DIR/bin/bforartists" -v 2>/dev/null | grep -m1 '^Bforartists' || echo "$BUILD_DIR/bin/bforartists")"
}

cmd_package() {
  need_repo; need_image
  local mode=""
  [ "$BFA_PACKAGE" = "devbuild" ] && mode="devbuild"
  info "Packaging the tarball ($BFA_PACKAGE)"
  in_container "./tools/utils/bforartists_package_linux.sh tar $mode"
  local newest
  newest=$(ls -t "$OUTPUT_DIR"/tar/*.tar.xz 2>/dev/null | head -1)
  [ -n "$newest" ] || die "No tarball in $OUTPUT_DIR/tar"
  ok "Package: $newest ($(du -h "$newest" | cut -f1))"
  # Keep only the newest devbuilds locally.
  ls -t "$OUTPUT_DIR"/tar/linux-devbuild-*.tar.xz 2>/dev/null | tail -n +"$((BFA_KEEP + 1))" | xargs -r rm -f
}

cmd_upload() {
  local newest
  newest=$(ls -t "$OUTPUT_DIR"/tar/*.tar.xz 2>/dev/null | head -1)
  [ -n "$newest" ] || die "Nothing to upload in $OUTPUT_DIR/tar"
  if [ -z "${BFA_DEVBUILDS_REMOTE:-}" ]; then
    warn "BFA_DEVBUILDS_REMOTE is not set: not uploading. The tarball stays in $OUTPUT_DIR/tar"
    return 0
  fi
  command -v rclone >/dev/null || die "rclone is not installed"
  info "Uploading $(basename "$newest") to $BFA_DEVBUILDS_REMOTE"
  # copy, never sync: nothing on the server is ever deleted from here.
  rclone copy "$newest" "$BFA_DEVBUILDS_REMOTE" --progress
  ok "Uploaded $(basename "$newest")"
}

cmd_weekly() {
  cmd_update
  cmd_build
  cmd_package
  cmd_upload
  ok "Weekly Linux build done"
}

cmd_shell() {
  need_repo; need_image
  in_container "exec bash"
}

cmd_status() {
  echo "BFA_HOME   : $BFA_HOME"
  echo "Branch     : $BFA_BRANCH  (package: $BFA_PACKAGE, upload: ${BFA_DEVBUILDS_REMOTE:-off})"
  [ -d "$REPO/.git" ] && echo "Source     : $(git -C "$REPO" rev-parse --short HEAD) on $(git -C "$REPO" branch --show-current)" \
                      || echo "Source     : missing (run setup)"
  podman_cmd image exists "$BFA_IMAGE" 2>/dev/null && echo "Image      : $BFA_IMAGE ready" || echo "Image      : missing (run image)"
  [ -x "$BUILD_DIR/bin/bforartists" ] && echo "Build      : $("$BUILD_DIR/bin/bforartists" -v 2>/dev/null | grep -m1 '^Bforartists')" \
                                      || echo "Build      : none yet"
  echo "Jobs       : ${BFA_JOBS:-$(auto_jobs) (auto)}  ·  memory: $(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 )) GB"
  echo "Disk free  : $(df -h --output=avail "$BFA_HOME" 2>/dev/null | tail -1 | tr -d ' ')"
  echo "Packages   :"; ls -lt "$OUTPUT_DIR"/tar/*.tar.xz 2>/dev/null | head -4 | awk '{print "  " $6, $7, $8, $9}'
  echo "Last log   : $(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)"
}

usage() { sed -n '2,/^set -euo/p' "$0" | head -n -1 | sed 's/^# \{0,1\}//'; }

# ---------------- Main ---------------- #

main() {
  local cmd="${1:-help}"
  case "$cmd" in
    setup|image|update|build|package|upload|weekly|shell|status) ;;
    -h|--help|help) usage; exit 0 ;;
    *) die "Unknown command '$cmd'. Run '$0 help'." ;;
  esac
  if [ "$cmd" = "shell" ] || [ "$cmd" = "status" ]; then "cmd_$cmd"; exit 0; fi

  mkdir -p "$LOG_DIR"
  local log="$LOG_DIR/$(date +%Y-%m-%d_%H%M%S)-$cmd.log"
  # One run at a time (a scheduled run and a manual one must not build together).
  exec 9>"$BFA_HOME/.builder.lock"
  flock -n 9 || die "Another builder run is in progress"
  info "Log: $log"
  { "cmd_$cmd"; } 2>&1 | tee "$log"
  exit "${PIPESTATUS[0]}"
}

main "$@"
