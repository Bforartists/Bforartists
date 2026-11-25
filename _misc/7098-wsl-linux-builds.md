# 🐧 Weekly Linux devbuilds from WSL · #7098

> 🧪 **Experimental** · Builds on the maintainer's Windows 11 PC, in WSL, inside Blender's official
> **Rocky Linux 8** build environment, with the Cycles GPU kernels (CUDA 12.8 + HIP/ROCm 7.2.1).

## 🧭 How it fits together

| Where | What | File |
|---|---|---|
| 🪟 Windows | WSL memory + swap, first setup, weekly task | `tools/utils/bforartists_wsl_builder.ps1` |
| 🐧 WSL (Ubuntu/Debian) | Source clone, Podman, tarballs, logs in `~/bfa` | `tools/utils/bforartists_linux_builder.sh` |
| 📦 Rocky 8 container | `make release` + packaging, same toolchain as Blender's builds | built from `build_files/build_environment/linux/linux_rocky8_setup.sh` |
| 🗂️ Packaging | `.tar.xz` (and `.deb` / `.AppImage` by hand) | `tools/utils/bforartists_package_linux.sh` (#7047) |

```
~/bfa/Bforartists               source (its own clone, in the Linux file system: never /mnt/c)
~/bfa/bfa_build_linux_release   build
~/bfa/build_output/tar          tarballs (the newest 4 devbuilds are kept)
~/bfa/logs                      one log per run
~/bfa/bin                       the copy of the builder the weekly task runs
```

## ▶️ First time (about 1 hour of your time, plus waiting)

Run in **PowerShell** from the repo (`C:\3D_Stuff\Bforartists_sync`), on this branch:

1. 🧠 **Setup:** sizes WSL (memory = 75% of RAM, 32 GB swap, existing `.wslconfig` backed up), restarts WSL,
   installs the tools in WSL (asks for your Linux password) and clones the source into `~/bfa`.
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\utils\bforartists_wsl_builder.ps1 setup
   ```
2. 📦 **Build image** (once, about 30–60 min, ~25 GB: gcc-toolset-14, CUDA, ROCm):
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\utils\bforartists_wsl_builder.ps1 image
   ```
3. 🔨 **First build** (hours the first time; GPU kernels are the slow part):
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\utils\bforartists_wsl_builder.ps1 run
   ```
4. ⏰ **Weekly task** (runs while you're signed in; default Saturday 18:00):
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\utils\bforartists_wsl_builder.ps1 schedule -Day Saturday -Time 18:00
   ```
5. ☁️ **Optional upload to devbuilds:** in WSL run `rclone config` once and add an R2 remote with a key limited
   to `bforartists-devbuilds` (never in Git or chat). Then add `-DevbuildsRemote "bfa-devbuilds:bforartists-devbuilds"`
   to `run` / `schedule`. Uploads use `rclone copy`, never `sync`, so nothing on the server gets deleted.

Check anytime: `powershell -ExecutionPolicy Bypass -File tools\utils\bforartists_wsl_builder.ps1 status`

## 🔁 What the weekly run does

`update` (pull `master`, `make update`) → `build` (`make release` in the container) →
`package` (`linux-devbuild-DD-MM-YYYY.tar.xz`) → `upload` (only if a remote is set).
One run at a time (lock file). A failure stops the chain and the log says where.

## 📦 Releases and Flathub

Flathub's [`de.bforartists.Bforartists`](https://github.com/flathub/de.bforartists.Bforartists) does not compile:
it repackages `Bforartists-X.Y.Z-Linux.tar.xz` from the GitHub release, and its bot opens an update PR when a new
release appears. For a release, in WSL:

```sh
BFA_BRANCH=master BFA_PACKAGE=release ~/bfa/bin/bforartists_linux_builder.sh weekly
# -> ~/bfa/build_output/tar/Bforartists-X.Y.Z-Linux.tar.xz : attach it to the GitHub release
```

The Flathub manifest expects, inside the tarball: a top folder `Bforartists*Linux*`, `bforartists.desktop`,
`bforartists-symbolic.svg` and `<version>/datafiles/locale`. Check those on the first release tarball.

## 💾 Disk and memory

- About **80–100 GB** in WSL: image ~25 GB, source + libraries ~25 GB, build ~20–30 GB.
  WSL lives on C: by default; to move it to D: use `wsl --export` / `wsl --import`.
- Jobs are capped by memory (2 GB per job). Override with `BFA_JOBS=8`.

## ✅ Test checklist

- [ ] `setup` and `image` finish
- [ ] First `run`: log ends with "Weekly Linux build done"
- [ ] CMake summary shows CUDA, HIP (and OptiX/oneAPI) kernels enabled; adjust if the first build reports missing SDKs
- [ ] The tarball starts on a real Linux machine (and in WSLg: `~/bfa/bfa_build_linux_release/bin/bforartists`)
- [ ] The weekly task ran on its own
- [ ] Optional: upload to devbuilds works
