#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Bforartists
#
# SPDX-License-Identifier: GPL-2.0-or-later

# bforartists_package_linux.sh
#
# Build the Linux release packages (.tar.xz, .deb, .AppImage) from a compiled
# release build directory. Intended for maintainers producing release builds or
# devbuilds - see the wiki "Building Linux Packages" page.
#
# Usage:
#   bforartists_package_linux.sh <all|tar|deb|appimage> [devbuild]
#
#   all       Build all three packages (default when no argument is given).
#   tar       Build only the .tar.xz archive.
#   deb       Build only the .deb package.
#   appimage  Build only the .AppImage (requires appimagetool).
#   devbuild  Optional second argument: name the tar archive
#             linux-devbuild-DD-MM-YYYY.tar.xz for devbuilds.bforartists.com.
#
# Environment overrides (defaults shown):
#   BFA_BUILD_DIR  <repo>/../bfa_build_linux_release   Compiled build dir.
#   OUTPUT_DIR     <repo>/../build_output              Where packages land.
#   APPIMAGETOOL   <repo>/../appimagetool-x86_64.AppImage
#   DEVBUILD       true/false                          Same as the devbuild arg.
#
# Requirements: tar, xz, dpkg (for .deb), appimagetool (for .AppImage).
#
# Examples:
#   # Full release: builds .AppImage, .deb and .tar.xz into ../build_output
#   ./tools/utils/bforartists_package_linux.sh all
#
#   # Weekly devbuild for devbuilds.bforartists.com:
#   ./tools/utils/bforartists_package_linux.sh tar devbuild
#   # -> ../build_output/tar/linux-devbuild-17-11-2026.tar.xz
#
#   # Package a non-default build dir (e.g. a lite build):
#   BFA_BUILD_DIR=../bfa_build_linux_lite ./tools/utils/bforartists_package_linux.sh tar
#
# NOTE: before copying, this script removes stale versioned datafiles dirs
# (e.g. bin/5.3 after the Blender base bumped to 5.4) and build-time helper
# binaries (makesdna, makesrna, datatoc, msgfmt, shader_tool, zstd_compress)
# from <build>/bin. `make install` restores them on the next build.

set -euo pipefail

# ---------------- Paths & configuration ---------------- #

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/../.." && pwd)
BUILD_ROOT=$(dirname "${REPO_ROOT}")

BFA_BUILD_DIR="${BFA_BUILD_DIR:-${BUILD_ROOT}/bfa_build_linux_release}"
OUTPUT_DIR="${OUTPUT_DIR:-${BUILD_ROOT}/build_output}"
APPIMAGETOOL="${APPIMAGETOOL:-${BUILD_ROOT}/appimagetool-x86_64.AppImage}"
DEVBUILD="${DEVBUILD:-false}"

BIN_DIR="${BFA_BUILD_DIR}/bin"
FREEDESKTOP_DIR="${REPO_ROOT}/release/freedesktop"
BKE_VERSION_H="${REPO_ROOT}/source/blender/blenkernel/BKE_blender_version.h"

# Build-time helper binaries that must not ship in user packages.
DEV_BINS=(makesdna makesrna datatoc msgfmt shader_tool zstd_compress)

# ---------------- Output helpers ---------------- #

if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

info() { printf "${BLUE}%s${NC}\n" "$*"; }
ok()   { printf "${GREEN}✔ %s${NC}\n" "$*"; }
warn() { printf "${YELLOW}⚠ %s${NC}\n" "$*" >&2; }
err()  { printf "${RED}✘ %s${NC}\n" "$*" >&2; }
die()  { err "$*"; exit 1; }

# ---------------- Version detection ---------------- #

detect_versions() {
  [ -x "${BIN_DIR}/bforartists" ] || \
    die "Binary not found: ${BIN_DIR}/bforartists (build Bforartists first)"

  VERSION=$("${BIN_DIR}/bforartists" -v | grep -E '^Bforartists ' | awk '{print $2}')
  [ -n "$VERSION" ] || die "Could not read Bforartists version from the binary"

  # The versioned datafiles dir inside bin/ follows the Blender version
  # (BLENDER_VERSION, e.g. 504 -> 5.4), not the Bforartists version.
  DATA_VERSION=""
  if [ -f "$BKE_VERSION_H" ]; then
    local bv
    bv=$(sed -n 's/^#define BLENDER_VERSION \([0-9][0-9]*\).*/\1/p' "$BKE_VERSION_H")
    [ -n "$bv" ] && DATA_VERSION="$((bv / 100)).$((bv % 100))"
  fi
  [ -n "$DATA_VERSION" ] || warn "Could not determine Blender datafiles version"
}

# ---------------- bin/ cleanup before packaging ---------------- #

# Remove stale versioned datafiles dirs left behind by older builds.
prune_stale_version_dirs() {
  [ -n "$DATA_VERSION" ] || return 0
  local vdir
  for vdir in "${BIN_DIR}/"[0-9]*.[0-9]*/; do
    [ -d "$vdir" ] || continue
    if [ "$(basename "$vdir")" != "$DATA_VERSION" ]; then
      rm -rf "$vdir"
      ok "Removed stale datafiles dir: ${vdir}"
    fi
  done
}

# Remove build-time helper binaries (`make install` restores them).
strip_dev_binaries() {
  local devbin
  for devbin in "${DEV_BINS[@]}"; do
    if [ -f "${BIN_DIR}/${devbin}" ]; then
      rm -f "${BIN_DIR}/${devbin}"
      ok "Removed dev tool from bin/: ${devbin}"
    fi
  done
}

# ---------------- Common checks ---------------- #

check_common() {
  command -v tar >/dev/null || die "Missing required tool: tar"
  command -v xz  >/dev/null || die "Missing required tool: xz"
  [ -d "$BFA_BUILD_DIR" ]  || die "Build dir not found: ${BFA_BUILD_DIR}"
  [ -d "${BIN_DIR}" ]      || die "bin/ not found in ${BFA_BUILD_DIR}"
  [ -d "$FREEDESKTOP_DIR" ] || die "freedesktop dir not found: ${FREEDESKTOP_DIR}"
  ok "Build dir: ${BFA_BUILD_DIR} (Bforartists ${VERSION}, datafiles ${DATA_VERSION:-unknown})"
}

prepare_bin() {
  prune_stale_version_dirs
  strip_dev_binaries
}

# ---------------- tar.xz ---------------- #

build_tar() {
  info "=== Building .tar.xz ==="

  local out_name="Bforartists-${VERSION}-Linux"
  local out_file="${OUTPUT_DIR}/tar/${out_name}.tar.xz"
  if [ "$DEVBUILD" = true ]; then
    # devbuilds.bforartists.com naming; the inner dir keeps the versioned name
    out_file="${OUTPUT_DIR}/tar/linux-devbuild-$(date +%d-%m-%Y).tar.xz"
  fi

  mkdir -p "${OUTPUT_DIR}/tar"
  XZ_OPT="-9e --threads=0" \
    tar -cJf "$out_file" \
      -C "$(dirname "$BIN_DIR")" \
      --transform "s|^bin|${out_name}|" \
      --owner=0 --group=0 \
      "$(basename "$BIN_DIR")"

  ok "Created ${out_file}"
}

# ---------------- .deb ---------------- #

build_deb() {
  info "=== Building .deb ==="
  command -v dpkg >/dev/null || die "Missing required tool: dpkg"

  local stage="${OUTPUT_DIR}/_stage_deb"
  local pkg="${stage}/bforartists"
  local out_file="${OUTPUT_DIR}/deb/bforartists_${VERSION}.deb"

  rm -rf "$stage"
  mkdir -p \
    "${pkg}/opt/bforartists" \
    "${pkg}/usr/bin" \
    "${pkg}/usr/share/applications" \
    "${pkg}/usr/share/doc/bforartists" \
    "${pkg}/usr/share/mime/application" \
    "${pkg}/usr/share/metainfo" \
    "${pkg}/usr/share/icons/hicolor" \
    "${pkg}/DEBIAN" \
    "${OUTPUT_DIR}/deb"

  cp -r "${BIN_DIR}/." "${pkg}/opt/bforartists"
  cp -r "${FREEDESKTOP_DIR}/icons/." "${pkg}/usr/share/icons/hicolor/"
  cp "${FREEDESKTOP_DIR}/bforartists.desktop" "${pkg}/usr/share/applications/"
  cp "${FREEDESKTOP_DIR}/de.bforartists.Bforartists.metainfo.xml" "${pkg}/usr/share/metainfo/"

  cat <<EOF > "${pkg}/usr/share/mime/application/bforartists.xml"
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
<mime-type type="application/bforartists">
<comment>Blend Scene</comment>
<glob pattern="*.blend"/>
</mime-type>
</mime-info>
EOF

  cat <<EOF > "${pkg}/DEBIAN/control"
Package: bforartists
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: amd64
Maintainer: Bforartists Team
Installed-Size: $(du -s "$pkg" | awk '{print $1}')
Description: Bforartists - 3D suite to create 3D content
 Bforartists is a fork of the popular open source 3D software Blender. The primary goal of the Bforartists fork is to deliver a better graphical UI and a better usability. This means a complete switch in the usage philosophy. Away from the hotkey and speed centered usage. Towards a user friendly and intuitive graphical UI.
Homepage: https://www.bforartists.co
EOF

  cat <<'EOF' > "${pkg}/DEBIAN/postrm"
#!/bin/sh
set -e
rm -f /usr/share/mime/application/bforartists.xml
rm -rf /opt/bforartists
exit 0
EOF
  chmod 755 "${pkg}/DEBIAN/postrm"

  cat <<'EOF' > "${pkg}/usr/bin/bforartists"
#!/bin/sh
exec /opt/bforartists/bforartists "$@"
EOF
  chmod 755 "${pkg}/usr/bin/bforartists"

  (cd "$stage" && dpkg -b bforartists "$out_file")
  ok "Created ${out_file}"

  rm -rf "$stage"
}

# ---------------- .AppImage ---------------- #

build_appimage() {
  info "=== Building .AppImage ==="
  [ -f "$APPIMAGETOOL" ] || die "appimagetool not found: ${APPIMAGETOOL}
Download from: https://github.com/AppImage/appimagetool/releases"
  [ -x "$APPIMAGETOOL" ] || chmod +x "$APPIMAGETOOL"

  local appdir="${OUTPUT_DIR}/_stage_appimage/Bforartists.AppDir"
  local out_file="${OUTPUT_DIR}/appimage/Bforartists-${VERSION}-x86_64.AppImage"

  rm -rf "${OUTPUT_DIR}/_stage_appimage"
  mkdir -p \
    "${appdir}/usr/bin" \
    "${appdir}/usr/lib" \
    "${appdir}/usr/share/icons/hicolor" \
    "${appdir}/usr/share/applications" \
    "${appdir}/usr/share/metainfo" \
    "${OUTPUT_DIR}/appimage"

  cp -r "${BIN_DIR}/."     "${appdir}/usr/bin/"
  cp -r "${BIN_DIR}/lib/." "${appdir}/usr/lib/"
  cp -r "${FREEDESKTOP_DIR}/icons/." "${appdir}/usr/share/icons/hicolor/"
  cp "${FREEDESKTOP_DIR}/icons/scalable/apps/bforartists.svg" "${appdir}/bforartists.png"
  cp "${FREEDESKTOP_DIR}/de.bforartists.Bforartists.metainfo.xml" "${appdir}/usr/share/metainfo/"
  cp "${FREEDESKTOP_DIR}/bforartists.desktop" "${appdir}/usr/share/applications/bforartists.desktop"
  ln -sf "usr/share/applications/bforartists.desktop" "${appdir}/bforartists.desktop"

  # AppRun: the binary locates its versioned datafiles dir relative to itself,
  # so no version-specific paths are needed here.
  cat <<'EOF' > "${appdir}/AppRun"
#!/bin/sh
HERE=$(dirname "$0")
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export XDG_CACHE_HOME="${HOME}/.cache"
mkdir -p "${HOME}/.cache/bforartists"
exec "${HERE}/usr/bin/bforartists" "$@"
EOF
  chmod +x "${appdir}/AppRun"

  ARCH=x86_64 "$APPIMAGETOOL" "$appdir" "$out_file"
  ok "Created ${out_file}"

  rm -rf "${OUTPUT_DIR}/_stage_appimage"
}

# ---------------- Main ---------------- #

usage() {
  sed -n '2,/^set -euo/p' "$0" | head -n -1 | sed 's/^# \{0,1\}//; /^$/d'
}

main() {
  local target="${1:-all}"
  [ "${2:-}" = "devbuild" ] && DEVBUILD=true
  [ "$target" = "devbuild" ] && { DEVBUILD=true; target=all; }

  case "$target" in
    -h|--help|help) usage; exit 0 ;;
    all|tar|deb|appimage) ;;
    *) die "Unknown target '${target}'. Run '$0 --help'." ;;
  esac

  detect_versions
  check_common
  prepare_bin

  case "$target" in
    all)      build_appimage; build_deb; build_tar ;;
    tar)      build_tar ;;
    deb)      build_deb ;;
    appimage) build_appimage ;;
  esac

  ok "Done. Packages in ${OUTPUT_DIR}"
}

main "$@"
