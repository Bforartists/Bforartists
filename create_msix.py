# Based on https://archive.blender.org/developer/D8310

import subprocess as sp
from pathlib import Path
import sys
from shutil import rmtree, copytree
from enum import Enum, auto
from typing import Sequence, Union, Optional


def run_command(command: Sequence[Union[str, Path]], cwd: Optional[Path] = None):
    return sp.run(command, stdin=sys.stdin, cwd=cwd, stdout=sys.stdout, stderr=sys.stderr, encoding="UTF-8")


class Config(Enum):
    Store = auto()
    Local = auto()


if len(sys.argv) < 3:
    print("Usage: create_msix.py <build dir> <version> <local_or_store>")
    print("build dir: path to build dir")
    print("version: version number, example 4.1.1")
    print("local_or_store: local or store")
    sys.exit(1)

build_dir = sys.argv[1]
version = sys.argv[2]
config = {"local": Config.Local, "store": Config.Store}[sys.argv[3]]

if config == Config.Store:
    # Windows Store ID
    publisher = "CN=4052CBE2-0610-49C7-81AB-D673FA51DA33"
elif config == Config.Local:
    # https://community.qlik.com/t5/Official-Support-Articles/How-to-find-certificates-by-thumbprint-or-name-with-powershell/ta-p/1711332
    # https://techcommunity.microsoft.com/t5/msix/msix-packageing-tool-signtool-certificate-issues/m-p/2133583/highlight/true#M78
    # https://stackoverflow.com/a/3961530/8094047
    certificate_subject_line = (
        'CN="Open Source Developer, Trinumedia", O=Open Source Developer, L=Bogota, S=Bogota, C=CO'
    )
    publisher = certificate_subject_line.replace('"', "&quot;")
else:
    assert False


# BFA does not maintain LTS versions yet
##
LTSORNOT = ""
PACKAGETYPE = ""
##

working_dir = Path(__file__).parent.parent / "msix"
if working_dir.exists() and working_dir.is_dir():
    rmtree(working_dir)
elif working_dir.is_file():
    print('Found unexpected file called "msix"', file=sys.stderr)
    exit(1)
working_dir.mkdir()

content_folder = working_dir / "Content"
content_folder.mkdir()

copytree(Path(__file__).parent / "release/windows/msix/Assets", content_folder / "Assets")

content_bfa_folder = content_folder / "Bforartists"
content_bfa_folder.mkdir()

cmake_install_command = [
    "cmake",
    "--install",
    ".",
    "--prefix",
    content_bfa_folder.absolute(),
]

run_command(cmake_install_command, cwd=Path(build_dir))


pri_config_file = Path(__file__).parent / "release/windows/msix/priconfig.xml"
pri_resources_file = content_folder / "resources.pri"

pri_command = [
    "makepri",
    "new",
    "/pr",
    f"{content_folder.absolute()}",
    "/cf",
    f"{pri_config_file.absolute()}",
    "/of",
    f"{pri_resources_file.absolute()}",
]

run_command(pri_command)


manifest_text = (Path(__file__).parent / "release/windows/msix/AppxManifest.xml.template").read_text()
manifest_text = manifest_text.replace("[VERSION]", version + ".0")
manifest_text = manifest_text.replace("[PUBLISHER]", publisher)
manifest_text = manifest_text.replace("[LTSORNOT]", LTSORNOT)
manifest_text = manifest_text.replace("[PACKAGETYPE]", PACKAGETYPE)
(content_folder / "AppxManifest.xml").write_text(manifest_text)

output_msix = working_dir / f"Bforartists_{version}.msix"


msix_command = [
    "makeappx",
    "pack",
    "/h",
    "SHA256",
    "/d",
    f"{content_folder.absolute()}",
    "/p",
    output_msix,
]

run_command(msix_command)

signtool_command = [
    "signtool",
    "sign",
    "/sha1",
    "4ae3d89dc7440d4533b99fb4977e114e4a0f052d",
    "/tr",
    "http://time.certum.pl/",
    "/td",
    "sha256",
    "/fd",
    "sha256",
    "/v",
    output_msix,
]

if config == Config.Local:
    run_command(signtool_command)
