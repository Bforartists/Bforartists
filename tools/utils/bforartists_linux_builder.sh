#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# bforartists_linux_builder.sh
#
# Linux builds of Bforartists from WSL, in the same Rocky Linux 8 environment Blender uses
# for its official builds, so the result runs on old and new distros and includes the
# Cycles GPU kernels (CUDA 12.8 + HIP/ROCm 7.2.1).
#
# Two modes, picked automatically:
#   native     the WSL distro IS Rocky Linux 8 (recommended, the official way): Blender's
#              build_files/build_environment/linux/linux_rocky8_setup.sh runs directly on it.
#   container  any other distro (Ubuntu/Debian): the same setup runs in a Podman container.
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
#   bforartists_linux_builder.sh setup     once: tools (git, git-lfs ...) + clone the source
#   bforartists_linux_builder.sh image     once (and when Blender changes its Rocky 8 setup):
#                                          install the Rocky 8 toolchain: gcc-toolset-14, CUDA,
#                                          ROCm (native) or build the container image (about
#                                          25 GB, 30-60 min)
#   bforartists_linux_builder.sh test      update + quick `make lite` build + start it once:
#                                          proves the toolchain works before a release build
#   bforartists_linux_builder.sh weekly    update + build + package + upload: the scheduled run
#   bforartists_linux_builder.sh release   update + build + all release packages (no upload):
#                                          Bforartists-X.Y.Z-Linux.tar.xz, bforartists_X.Y.Z.deb,
#                                          Bforartists-X.Y.Z-x86_64.AppImage
#
#   Single steps: update, build, launch, package, upload, shell, status
#
# Environment (defaults):
#   BFA_HOME              ~/bfa
#   BFA_BRANCH            master        a branch or a release tag (e.g. v5.3.0)
#   BFA_TARGET            release       make target for build: release or lite
#   BFA_PACKAGE           devbuild      devbuild = linux-devbuild-DD-MM-YYYY.tar.xz
#                                       release  = Bforartists-X.Y.Z-Linux.tar.xz (Flathub's input)
#   BFA_RELEASE_FORMATS   all           release packages: all (AppImage + deb + tar) or tar
#   BFA_MODE              auto          native (on Rocky 8) or container (elsewhere)
#   BFA_IMAGE             bforartists-rocky8   container mode only
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
BFA_TARGET="${BFA_TARGET:-release}"
BUILD_DIR="$BFA_HOME/bfa_build_linux_${BFA_TARGET}"
OUTPUT_DIR="$BFA_HOME/build_output"
LOG_DIR="$BFA_HOME/logs"
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"
if [ -z "${BFA_MODE:-}" ]; then
  if grep -qs 'release 8' /etc/rocky-release; then BFA_MODE=native; else BFA_MODE=container; fi
fi
APPIMAGETOOL="${APPIMAGETOOL:-$BFA_HOME/appimagetool-x86_64.AppImage}"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
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

TOOLCHAIN='source scl_source enable gcc-toolset-14 && export PATH=/usr/local/cuda/bin:/opt/rocm/bin:$PATH && export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}'

# Run a command with the Rocky 8 toolchain: directly (native) or in the build container,
# with $BFA_HOME mounted at the same path.
in_container() {
  if [ "$BFA_MODE" = native ]; then
    # WSL has no FUSE, so AppImages (appimagetool itself) run by extracting themselves first.
    (cd "$REPO" && NPROCS="${BFA_JOBS:-$(auto_jobs)}" BFA_BUILD_DIR="$BUILD_DIR" OUTPUT_DIR="$OUTPUT_DIR" \
      APPIMAGETOOL="$APPIMAGETOOL" APPIMAGE_EXTRACT_AND_RUN=1 \
      bash -lc "$TOOLCHAIN && $1")
    return
  fi
  mkdir -p "$BFA_HOME/.container-home"
  # Rootless: keep your user id inside, so the build files stay yours. As root it isn't needed.
  local userns=()
  [ "$(id -u)" -ne 0 ] && userns=(--userns=keep-id)
  podman_cmd run --rm "${userns[@]}" \
    -v "$BFA_HOME:$BFA_HOME" \
    -w "$REPO" \
    -e HOME="$BFA_HOME/.container-home" \
    -e NPROCS="${BFA_JOBS:-$(auto_jobs)}" \
    -e BFA_BUILD_DIR="$BUILD_DIR" \
    -e OUTPUT_DIR="$OUTPUT_DIR" \
    -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0='*' \
    "$BFA_IMAGE" \
    bash -lc "$TOOLCHAIN && $1"
}

need_repo() {
  [ -d "$REPO/.git" ] || die "No source in $REPO. Run: $0 setup"
}

need_image() {
  if [ "$BFA_MODE" = native ]; then
    [ -d /opt/rh/gcc-toolset-14 ] || die "Rocky 8 toolchain not installed. Run: $0 image"
  else
    podman_cmd image exists "$BFA_IMAGE" || die "No build image '$BFA_IMAGE'. Run: $0 image"
  fi
}

# ---------------- Commands ---------------- #

cmd_setup() {
  local sudo="$SUDO"
  info "Mode: $BFA_MODE"
  if [ "$BFA_MODE" = native ]; then
    info "Installing the basic tools (git, git-lfs from EPEL, Python 3.9 ...)"
    $sudo dnf -y install epel-release
    $sudo dnf -y install git git-lfs python39 make xz tar util-linux gawk which procps-ng findutils \
      diffutils ca-certificates
  else
    command -v apt-get >/dev/null || die "Container mode expects Ubuntu/Debian (apt). Use a Rocky 8 distro for native mode."
    info "Installing host tools (asks for your password once)"
    $sudo apt-get update
    $sudo apt-get install -y podman uidmap slirp4netns fuse-overlayfs git git-lfs python3 make \
      xz-utils rclone ca-certificates
  fi
  git lfs install --skip-repo
  # Rootless Podman needs a range of sub-user ids for this user.
  if [ "$BFA_MODE" = container ] && [ "$(id -u)" -ne 0 ] && ! grep -q "^$(id -un):" /etc/subuid 2>/dev/null; then
    $sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$(id -un)"
    ok "Added sub-user ids for $(id -un) (rootless Podman)"
  fi
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
  if [ "$BFA_MODE" = native ]; then
    info "Installing Blender's Rocky 8 toolchain on this distro (gcc-toolset-14, CUDA 12.8, ROCm 7.2.1)"
    $SUDO bash "$ctx/linux_rocky8_setup.sh"
    # Window libraries (Wayland/X11), so a build can also be opened on the Windows desktop (WSLg).
    $SUDO dnf -y install libwayland-client libwayland-cursor libwayland-egl libxkbcommon libX11 libXi \
      libXxf86vm libXcursor libXrandr libXinerama libXfixes mesa-libGL mesa-libEGL mesa-dri-drivers \
      || warn "Window libraries not installed (only needed to open builds on the Windows desktop)"
    rm -rf "$ctx"
    ok "Rocky 8 toolchain installed"
    return
  fi
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
  git fetch origin --prune --tags --force
  if git show-ref --verify --quiet "refs/remotes/origin/$BFA_BRANCH"; then
    git checkout "$BFA_BRANCH" 2>/dev/null || git checkout -b "$BFA_BRANCH" "origin/$BFA_BRANCH"
    git pull --rebase origin "$BFA_BRANCH"
  elif git show-ref --verify --quiet "refs/tags/$BFA_BRANCH"; then
    # A release tag (e.g. v5.3.0): build exactly that commit.
    git checkout --detach "refs/tags/$BFA_BRANCH"
  else
    die "No branch or tag '$BFA_BRANCH' on origin"
  fi
  # Rocky 8's default Python is 3.6; use 3.9 for Blender's update script.
  if [ "$BFA_MODE" = native ]; then make update PYTHON=python3.9; else make update; fi
  ok "Source: $BFA_BRANCH at $(git rev-parse --short HEAD) ($(git log -1 --format=%s | cut -c1-70))"
}

cmd_build() {
  need_repo; need_image
  # OptiX (NVIDIA ray tracing) needs NVIDIA's SDK, a login-only download: used when unpacked in ~/bfa/optix.
  local cmake_args=""
  if [ -f "$BFA_HOME/optix/include/optix.h" ]; then
    cmake_args="BUILD_CMAKE_ARGS='-DOPTIX_ROOT_DIR=$BFA_HOME/optix'"
    ok "OptiX SDK found: $BFA_HOME/optix"
  elif [ "$BFA_TARGET" = release ]; then
    warn "No OptiX SDK in $BFA_HOME/optix: the build has CUDA and HIP, but no OptiX"
  fi
  info "Building (make $BFA_TARGET) with ${BFA_JOBS:-$(auto_jobs)} jobs"
  in_container "make $BFA_TARGET $cmake_args"
  [ -x "$BUILD_DIR/bin/bforartists" ] || die "Build finished but $BUILD_DIR/bin/bforartists is missing"
  ok "Built: $("$BUILD_DIR/bin/bforartists" -v 2>/dev/null | grep -m1 '^Bforartists' || echo "$BUILD_DIR/bin/bforartists")"
}

cmd_package() {
  need_repo; need_image
  local what="tar devbuild"
  if [ "$BFA_PACKAGE" != "devbuild" ]; then
    what="${BFA_RELEASE_FORMATS:-all}"
    [ "$BFA_MODE" = native ] || { warn "Container mode packages the tarball only"; what="tar"; }
  fi
  info "Packaging: $what"
  in_container "./tools/utils/bforartists_package_linux.sh $what"
  local newest
  newest=$(ls -t "$OUTPUT_DIR"/tar/*.tar.xz 2>/dev/null | head -1)
  [ -n "$newest" ] || die "No tarball in $OUTPUT_DIR/tar"
  ok "Package: $newest ($(du -h "$newest" | cut -f1))"
  if [ "$BFA_PACKAGE" != "devbuild" ]; then
    local f
    for f in "$OUTPUT_DIR"/deb/*.deb "$OUTPUT_DIR"/appimage/*.AppImage; do
      [ -f "$f" ] && ok "Package: $f ($(du -h "$f" | cut -f1))"
    done
  fi
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

# Tools for the .deb (dpkg, from EPEL) and the AppImage (appimagetool), installed when missing.
ensure_release_tools() {
  [ "$BFA_MODE" = native ] || return 0
  [ "${BFA_RELEASE_FORMATS:-all}" = tar ] && return 0
  if ! command -v dpkg >/dev/null; then
    info "Installing dpkg (for the .deb) and file (for appimagetool)"
    $SUDO dnf -y install dpkg file || die "Could not install dpkg"
  fi
  if [ ! -s "$APPIMAGETOOL" ]; then
    info "Downloading appimagetool"
    curl -fL -o "$APPIMAGETOOL" "$APPIMAGETOOL_URL" || die "Could not download appimagetool"
    chmod +x "$APPIMAGETOOL"
  fi
  ok "Release packaging tools ready (dpkg, appimagetool)"
}

# Release: all release packages. The .tar.xz is the file Flathub repackages.
cmd_release() {
  BFA_PACKAGE=release
  ensure_release_tools
  cmd_update
  cmd_build
  cmd_launch
  cmd_package
  ok "Release packages ready in $OUTPUT_DIR (tar/, deb/, appimage/). Attach them to the GitHub release;"
  ok "Flathub's bot then opens its update PR from the .tar.xz"
}

# Start the build once without a window and check that it runs Python and reports its version.
cmd_launch() {
  [ -x "$BUILD_DIR/bin/bforartists" ] || die "No build in $BUILD_DIR"
  local probe="$BFA_HOME/.launch_probe.py"
  printf '%s\n' 'import bpy, sys' \
    'print("BFA_LAUNCH_OK", bpy.app.version_string, "| Python", sys.version.split()[0])' > "$probe"
  info "Starting $BUILD_DIR/bin/bforartists in background mode"
  local out
  out=$(in_container "'$BUILD_DIR/bin/bforartists' -b --factory-startup --python '$probe'" 2>&1 || true)
  echo "$out" | tail -15
  echo "$out" | grep -q BFA_LAUNCH_OK || die "Bforartists did not start correctly (see the lines above)"
  ok "Bforartists starts: $(echo "$out" | grep BFA_LAUNCH_OK | sed 's/BFA_LAUNCH_OK //')"
}

cmd_test() {
  BFA_TARGET=lite
  BUILD_DIR="$BFA_HOME/bfa_build_linux_lite"
  cmd_update
  cmd_build
  cmd_launch
  ok "Test build works. Next: the full release build (run / weekly)"
}

cmd_weekly() {
  cmd_update
  cmd_build
  cmd_launch
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
  echo "Mode       : $BFA_MODE"
  if [ "$BFA_MODE" = native ]; then
    [ -d /opt/rh/gcc-toolset-14 ] && echo "Toolchain  : Rocky 8 toolchain ready" || echo "Toolchain  : missing (run image)"
  else
    podman_cmd image exists "$BFA_IMAGE" 2>/dev/null && echo "Image      : $BFA_IMAGE ready" || echo "Image      : missing (run image)"
  fi
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
    setup|image|update|build|launch|test|release|package|upload|weekly|shell|status) ;;
    -h|--help|help) usage; exit 0 ;;
    *) die "Unknown command '$cmd'. Run '$0 help'." ;;
  esac
  if [ "$cmd" = "shell" ] || [ "$cmd" = "status" ]; then "cmd_$cmd"; exit 0; fi

  mkdir -p "$LOG_DIR"
  local log="$LOG_DIR/$(date +%Y-%m-%d_%H%M%S)-$cmd.log"
  # One run at a time (a scheduled run and a manual one must not build together).
  if command -v flock >/dev/null; then
    exec 9>"$BFA_HOME/.builder.lock"
    flock -n 9 || die "Another builder run is in progress"
  fi
  info "Log: $log"
  { "cmd_$cmd"; } 2>&1 | tee "$log"
  exit "${PIPESTATUS[0]}"
}

main "$@"
