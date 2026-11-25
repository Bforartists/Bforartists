# 🐧 Weekly Linux devbuilds from WSL · #7098

> 🧪 **Experimental** · Builds on the maintainer's Windows 11 PC in a **Rocky Linux 8** WSL distro, the same
> environment Blender uses for its official Linux builds (gcc-toolset-14, CUDA 12.8, ROCm/HIP 7.2.1).
> The tarball runs on old and new distros and includes the Cycles GPU kernels.

## 🧭 How it fits together

| Where | What | File |
|---|---|---|
| 🪟 Windows | WSL memory + swap, first setup, weekly task | `tools/utils/bforartists_wsl_builder.ps1` |
| 🐧 WSL: Rocky Linux 8 (`BfaBuild`) | Toolchain, source clone, build, tarballs, logs in `~/bfa` | `tools/utils/bforartists_linux_builder.sh` |
| 🧰 Toolchain | Blender's own setup script, run as-is | `build_files/build_environment/linux/linux_rocky8_setup.sh` |
| 🗂️ Packaging | `.tar.xz` (and `.deb` / `.AppImage` by hand) | `tools/utils/bforartists_package_linux.sh` (#7047) |

The builder picks **native** mode on Rocky 8. On any other distro it falls back to **container** mode
(the same Rocky 8 setup inside Podman).

```
~/bfa/Bforartists               source (its own clone, in the Linux file system: never /mnt/c)
~/bfa/bfa_build_linux_release   build
~/bfa/build_output/tar          tarballs (the newest 4 devbuilds are kept)
~/bfa/logs                      one log per run
~/bfa/bin                       the copy of the builder the weekly task runs
```

## ▶️ First time (everything on Z:)

In **PowerShell** (not admin). About 120 GB free on Z: is needed.

```powershell
# 1. WSL up to date
wsl --update

# 2. Rocky Linux 8 image (official Container Base, ~40 MB)
New-Item -ItemType Directory -Force Z:\WSL\BfaBuild, Z:\WSL\tools | Out-Null
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest https://dl.rockylinux.org/pub/rocky/8/images/x86_64/Rocky-8-Container-Base.latest.x86_64.tar.xz -OutFile Z:\WSL\rocky8.tar.xz

# 3. Create the build distro on Z: (it runs as root: it's only for builds)
wsl --import BfaBuild Z:\WSL\BfaBuild Z:\WSL\rocky8.tar.xz --version 2
wsl -d BfaBuild -- cat /etc/rocky-release

# 4. The two scripts (from this branch)
$b = 'https://raw.githubusercontent.com/Bforartists/Bforartists/7098-development---tools---linux---weekly-linux-devbuilds-from-wsl-in-the-rocky-8-build-environment/tools/utils'
Invoke-WebRequest "$b/bforartists_wsl_builder.ps1" -OutFile Z:\WSL\tools\bforartists_wsl_builder.ps1
Invoke-WebRequest "$b/bforartists_linux_builder.sh" -OutFile Z:\WSL\tools\bforartists_linux_builder.sh

# 5. Setup: WSL memory (75% RAM) + 32 GB swap on Z:, basic tools, clone the source
powershell -ExecutionPolicy Bypass -File Z:\WSL\tools\bforartists_wsl_builder.ps1 setup -Distro BfaBuild -SwapFile Z:\WSL\swap.vhdx

# 6. Blender's Rocky 8 toolchain (once, 30-60 min, ~25 GB)
powershell -ExecutionPolicy Bypass -File Z:\WSL\tools\bforartists_wsl_builder.ps1 image -Distro BfaBuild

# 7. First build (hours: GPU kernels)
powershell -ExecutionPolicy Bypass -File Z:\WSL\tools\bforartists_wsl_builder.ps1 run -Distro BfaBuild

# 8. Weekly task
powershell -ExecutionPolicy Bypass -File Z:\WSL\tools\bforartists_wsl_builder.ps1 schedule -Distro BfaBuild -Day Saturday -Time 18:00
```

If step 3 refuses the `.tar.xz`, unpack it first with your other WSL distro:
`wsl -- xz -dk /mnt/z/WSL/rocky8.tar.xz`, then import `Z:\WSL\rocky8.tar`.

Check anytime: `... bforartists_wsl_builder.ps1 status -Distro BfaBuild`.

🖥️ **Open a build on the Windows desktop:** `... bforartists_wsl_builder.ps1 open -Distro BfaBuild` (newest release
build, else the lite test build). It draws in software over X11, because WSLg's GPU driver (Mesa d3d12) isn't in
Rocky 8, so the viewport is slow: real GPU testing belongs on a real Linux machine. WSLg ignores Windows display
scaling; set Preferences > Interface > Resolution Scale once (e.g. 1.5–2), it's saved inside BfaBuild.
Tarballs in File Explorer: `\\wsl$\BfaBuild\root\bfa\build_output\tar`.

☁️ **Optional upload to devbuilds:** `wsl -d BfaBuild -- rclone config` once (R2 remote, key limited to
`bforartists-devbuilds`, never in Git or chat), then add `-DevbuildsRemote "remote:bforartists-devbuilds"` to
`run` / `schedule`. Uploads use `rclone copy`, never `sync`.

## 🔁 What the weekly run does

`update` (pull `master`, `make update`, with Python 3.9 because Rocky 8's default is 3.6) →
`build` (`make release` with gcc-toolset-14, CUDA and ROCm on the PATH) → `package`
(`linux-devbuild-DD-MM-YYYY.tar.xz`) → `upload` (only if a remote is set). One run at a time.
A failure stops the chain and the log in `~/bfa/logs` says where.

## 📦 Releases and Flathub

Flathub's [`de.bforartists.Bforartists`](https://github.com/flathub/de.bforartists.Bforartists) does not compile:
it repackages `Bforartists-X.Y.Z-Linux.tar.xz` from the GitHub release, and its bot opens an update PR when a new
release appears.

```powershell
powershell -ExecutionPolicy Bypass -File Z:\WSL\tools\bforartists_wsl_builder.ps1 release -Distro BfaBuild
```

One command builds and makes **all three release packages** with `bforartists_package_linux.sh all` (#7047):

| Package | Folder in `~/bfa/build_output` |
|---|---|
| `Bforartists-X.Y.Z-Linux.tar.xz` (also Flathub's input) | `tar/` |
| `bforartists_X.Y.Z.deb` | `deb/` |
| `Bforartists-X.Y.Z-x86_64.AppImage` | `appimage/` |

The first release run installs `dpkg` (EPEL) and downloads `appimagetool`; WSL has no FUSE, so AppImages run with
`APPIMAGE_EXTRACT_AND_RUN=1`. `BFA_RELEASE_FORMATS=tar` makes the tarball only.

The Flathub manifest expects, inside the tarball: a top folder `Bforartists*Linux*`, `bforartists.desktop`,
`bforartists-symbolic.svg` and `<version>/datafiles/locale`. Check those on the first release tarball.

## 💾 Disk and memory

- About **80–100 GB** inside `BfaBuild` (toolchain ~25 GB, source + libraries ~25 GB, build ~20–30 GB),
  all in `Z:\WSL\BfaBuild\ext4.vhdx`. Swap file: `Z:\WSL\swap.vhdx`.
- Jobs are capped by memory (2 GB per job). Override with `BFA_JOBS=8`.

## ✅ Test checklist

- [ ] `setup` and `image` finish
- [ ] First `run`: log ends with "Weekly Linux build done"
- [ ] CMake summary shows CUDA and HIP kernels enabled (OptiX / oneAPI may need extra SDKs)
- [ ] The tarball, .deb and AppImage start on a real Linux machine
- [ ] The weekly task ran on its own
- [ ] Optional: upload to devbuilds works
