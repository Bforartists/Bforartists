#!/usr/bin/env python
# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Sub-commands:

Running a Repo
   - `server-generate` generate repository from a list of packages.

Developing a Package
   - `pkg-build` build a package.
   - `pkg-check` check the package state (warn of any issues).

Using a Package
   - `repo-add`
   - `repo-remove`
   - `install` takes a name, optionally repo+name.
   - `uninstall`
   - `update` (defaults to all local repo).
   - `check` (defaults to all local repo).
   - `list` list all known remote, both local & remote (defaults to all local repos).
"""


import argparse
import contextlib
import hashlib  # for SHA1 check-summing files.
import io
import json
import os
import re
import shutil
import signal  # Override `Ctrl-C`.
import sys
import tarfile
import tomllib
import urllib.error  # For `URLError`.
import urllib.parse  # For `urljoin`.
import urllib.request  # For accessing remote `https://` paths.


from typing import (
    Any,
    Dict,
    Generator,
    IO,
    Optional,
    Sequence,
    List,
    Tuple,
    Callable,
    NamedTuple,
    Union,
)

REQUEST_EXIT = False

# Expect the remote URL to contain JSON (don't append the JSON name to the path).
# File-system still append the expected JSON filename.
REMOTE_REPO_HAS_JSON_IMPLIED = True


def signal_handler_sigint(_sig: int, _frame: Any) -> None:
    # pylint: disable-next=global-statement
    global REQUEST_EXIT
    REQUEST_EXIT = True


signal.signal(signal.SIGINT, signal_handler_sigint)


# A primitive type that can be communicated via message passing.
PrimType = Union[int, str]
PrimTypeOrSeq = Union[PrimType, Sequence[PrimType]]

MessageFn = Callable[[str, PrimTypeOrSeq], bool]

# Name is a bit odd, a new convention could be used here.
PkgManifest_RepoDict = Dict[str, Any]

VERSION = "0.1"

PKG_EXT = ".txz"
# PKG_JSON_INFO = "bl_ext_repo.json"

PKG_REPO_LIST_FILENAME = "bl_ext_repo.json"

# Only for building.
PKG_MANIFEST_FILENAME_TOML = "bl_manifest.toml"

# This directory is in the local repository.
REPO_LOCAL_PRIVATE_DIR = ".blender_ext"

MESSAGE_TYPES = {'STATUS', 'PROGRESS', 'WARN', 'ERROR', 'DONE'}

RE_MANIFEST_SEMVER = re.compile(
    r'^'
    r'(?P<major>0|[1-9]\d*)\.'
    r'(?P<minor>0|[1-9]\d*)\.'
    r'(?P<patch>0|[1-9]\d*)'
    r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
    r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)

# Small value (in bytes).
CHUNK_SIZE_DEFAULT = 32  # 16

# Standard out may be communicating with a parent process,
# arbitrary prints are NOT acceptable.


# pylint: disable-next=redefined-builtin
def print(*args: Any, **kw: Dict[str, Any]) -> None:
    raise Exception("Illegal print(*({!r}), **{{{!r}}})".format(args, kw))


def message_done(msg_fn: MessageFn) -> bool:
    """
    Print a non-fatal warning.
    """
    return msg_fn("DONE", "")


def message_warn(msg_fn: MessageFn, s: str) -> bool:
    """
    Print a non-fatal warning.
    """
    return msg_fn("WARN", s)


def message_error(msg_fn: MessageFn, s: str) -> bool:
    """
    Print a fatal error.
    """
    return msg_fn("ERROR", s)


def message_status(msg_fn: MessageFn, s: str) -> bool:
    """
    Print a status message.
    """
    return msg_fn("STATUS", s)


def message_progress(msg_fn: MessageFn, s: str, progress: int, progress_range: int, unit: str) -> bool:
    """
    Print a progress update.
    """
    assert unit == 'BYTE'
    return msg_fn("PROGRESS", (s, unit, progress, progress_range))


# -----------------------------------------------------------------------------
# Generic Functions

def read_with_timeout(fh: IO[bytes], size: int, *, timeout_in_seconds: float) -> Optional[bytes]:
    # TODO: implement timeout (TimeoutError).
    return fh.read(size)


class CleanupPathsContext:
    __slots__ = (
        "files",
        "directories",
    )

    def __init__(self, *, files: Sequence[str], directories: Sequence[str]) -> None:
        self.files = files
        self.directories = directories

    def __enter__(self) -> "CleanupPathsContext":
        return self

    def __exit__(self, _ty: Any, _value: Any, _traceback: Any) -> None:
        for f in self.files:
            if not os.path.exists(f):
                continue
            try:
                os.unlink(f)
            except Exception:
                pass

        for d in self.directories:
            if not os.path.exists(d):
                continue
            try:
                shutil.rmtree(d)
            except Exception:
                pass


# -----------------------------------------------------------------------------
# Generic Functions


class PkgManifest(NamedTuple):
    """Package Information."""
    id: str
    name: str
    description: str
    version: str
    type: str


class PkgManifest_Archive(NamedTuple):
    """Package Information with archive information."""
    manifest: PkgManifest
    archive_size: int
    archive_hash: str
    archive_url: str


# -----------------------------------------------------------------------------
# Generic Functions

def random_acii_lines(*, seed: Union[int, str], width: int) -> Generator[str, None, None]:
    """
    Generate random ASCII text [A-Za-z0-9].
    Intended not to compress well, it's possible to simulate downloading a large package.
    """
    import random
    import string

    chars_init = string.ascii_letters + string.digits
    chars = chars_init
    while len(chars) < width:
        chars = chars + chars_init

    r = random.Random(seed)
    chars_list = list(chars)
    while True:
        r.shuffle(chars_list)
        yield "".join(chars_list[:width])


def sha256_from_file(filepath: str, block_size: int = 1 << 20, hash_prefix: bool = False) -> Tuple[int, str]:
    """
    Returns an arbitrary sized unique ASCII string based on the file contents.
    (exact hashing method may change).
    """
    with open(filepath, 'rb') as fh:
        size = 0
        sha256 = hashlib.new('sha256')
        while True:
            data = fh.read(block_size)
            if not data:
                break
            sha256.update(data)
            size += len(data)
        # Skip the `0x`.
        return size, ("sha256:" + sha256.hexdigest()) if hash_prefix else sha256.hexdigest()


def scandir_recursive_impl(
        base_path: str,
        path: str,
        *,
        filter_fn: Callable[[str], bool],
) -> Generator[Tuple[str, str], None, None]:
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        if entry.is_symlink():
            continue

        entry_path = entry.path
        entry_path_relateive = os.path.relpath(entry_path, base_path)

        if not filter_fn(entry_path_relateive):
            continue

        if entry.is_dir():
            yield from scandir_recursive_impl(
                base_path,
                entry_path,
                filter_fn=filter_fn,
            )
        elif entry.is_file():
            yield entry_path, entry_path_relateive


def scandir_recursive(
        path: str,
        filter_fn: Callable[[str], bool],
) -> Generator[Tuple[str, str], None, None]:
    yield from scandir_recursive_impl(path, path, filter_fn=filter_fn)


def pkg_manifest_from_dict_and_validate(pkg_idname: str, data: Dict[Any, Any]) -> Union[PkgManifest, str]:
    values: List[str] = []
    for key in PkgManifest._fields:
        if key == "id":
            values.append(pkg_idname)
            continue
        val = data.get(key, ...)
        if val is ...:
            return "key \"{:s}\" expected but not found".format(key)
        if not isinstance(val, str):
            return "key \"{:s}\" expected string type for".format(key)
        values.append(val)

    manifest = PkgManifest(**dict(zip(PkgManifest._fields, values, strict=True)))

    if (error_msg := pkg_idname_is_valid_or_error(manifest.id)) is not None:
        return "key \"id\": \"{:s}\" invalid, {:s}".format(manifest.id, error_msg)

    # From https://semver.org
    if not RE_MANIFEST_SEMVER.match(manifest.version):
        return "key \"version\" doesn't match SEMVER format, see: https://semver.org"

    # There could be other validation, leave these as-is.

    return manifest


def pkg_manifest_archive_from_dict_and_validate(
        pkg_idname: str, data: Dict[Any, Any]) -> Union[PkgManifest_Archive, str]:
    manifest = pkg_manifest_from_dict_and_validate(pkg_idname, data)
    if isinstance(manifest, str):
        return manifest

    return PkgManifest_Archive(
        manifest=manifest,
        # TODO: check these ID's exist.
        archive_size=data["archive_size"],
        archive_hash=data["archive_hash"],
        archive_url=data["archive_url"],
    )


def pkg_manifest_from_toml_and_validate(filepath: str) -> Union[PkgManifest, str]:
    """
    This function is responsible for not letting invalid manifest from creating packages with ID names
    or versions that would not properly install.

    The caller is expected to use exception handling and forward any errors to the user.
    """
    try:
        with open(filepath, "rb") as fh:
            data = tomllib.load(fh)
    except Exception as ex:
        return str(ex)

    pkg_idname = data.pop("id")
    return pkg_manifest_from_dict_and_validate(pkg_idname, data)


def remote_url_from_repo_url(url: str) -> str:
    if REMOTE_REPO_HAS_JSON_IMPLIED:
        return url
    return urllib.parse.urljoin(url, PKG_REPO_LIST_FILENAME)


# -----------------------------------------------------------------------------
# URL Downloading

# Originally based on `urllib.request.urlretrieve`.


def url_retrieve_to_data_iter(
        url: str,
        *,
        data: Optional[Any] = None,
        chunk_size: int,
        timeout_in_seconds: float,
) -> Generator[Tuple[bytes, int, Any], None, None]:
    """
    Retrieve a URL into a temporary location on disk.

    Requires a URL argument. If a filename is passed, it is used as
    the temporary file location. The reporthook argument should be
    a callable that accepts a block number, a read size, and the
    total file size of the URL target. The data argument should be
    valid URL encoded data.

    If a filename is passed and the URL points to a local resource,
    the result is a copy from local file to new file.

    Returns a tuple containing the path to the newly created
    data file as well as the resulting HTTPMessage object.
    """
    from urllib.error import ContentTooShortError
    from urllib.request import urlopen

    with contextlib.closing(urlopen(
            url,
            data,
            timeout=timeout_in_seconds,
    )) as fp:
        headers = fp.info()

        size = -1
        read = 0
        if "content-length" in headers:
            size = int(headers["Content-Length"])

        yield (b'', size, headers)

        if timeout_in_seconds == -1.0:
            while True:
                block = fp.read(chunk_size)
                if not block:
                    break
                read += len(block)
                yield (block, size, headers)
        else:
            while True:
                block = read_with_timeout(fp, chunk_size, timeout_in_seconds=timeout_in_seconds)
                if not block:
                    break
                read += len(block)
                yield (block, size, headers)

    if size >= 0 and read < size:
        raise ContentTooShortError("retrieval incomplete: got only %i out of %i bytes" % (read, size), headers)


def url_retrieve_to_filepath_iter(
        url: str,
        filepath: str,
        *,
        data: Optional[Any] = None,
        chunk_size: int,
        timeout_in_seconds: float,
) -> Generator[Tuple[int, int, Any], None, None]:
    # Handle temporary file setup.
    with open(filepath, 'wb') as fh_output:
        for block, size, headers in url_retrieve_to_data_iter(
                url,
                data=data,
                chunk_size=chunk_size,
                timeout_in_seconds=timeout_in_seconds,
        ):
            fh_output.write(block)
            yield (len(block), size, headers)


def filepath_retrieve_to_filepath_iter(
        filepath_src: str,
        filepath: str,
        *,
        chunk_size: int,
        timeout_in_seconds: float,
) -> Generator[Tuple[int, int], None, None]:
    # TODO: `timeout_in_seconds`.
    # Handle temporary file setup.
    with open(filepath_src, 'rb') as fh_input:
        size = os.fstat(fh_input.fileno()).st_size
        with open(filepath, 'wb') as fh_output:
            while (block := fh_input.read(chunk_size)):
                fh_output.write(block)
                yield (len(block), size)


def url_retrieve_to_data_iter_or_filesystem(
        path: str,
        is_filesystem: bool,
        chunk_size: int,
        timeout_in_seconds: float,
) -> Generator[bytes, None, None]:
    if is_filesystem:
        with open(path, "rb") as fh_source:
            while (block := fh_source.read(chunk_size)):
                yield block
    else:
        for (
                block,
                _size,
                _headers,
        ) in url_retrieve_to_data_iter(
            path,
            chunk_size=chunk_size,
            timeout_in_seconds=timeout_in_seconds,
        ):
            yield block


def url_retrieve_to_filepath_iter_or_filesystem(
        path: str,
        filepath: str,
        is_filesystem: bool,
        chunk_size: int,
        timeout_in_seconds: float,
) -> Generator[Tuple[int, int], None, None]:
    if is_filesystem:
        yield from filepath_retrieve_to_filepath_iter(
            path,
            filepath,
            chunk_size=chunk_size,
            timeout_in_seconds=timeout_in_seconds,
        )
    else:
        for (read, size, _headers) in url_retrieve_to_filepath_iter(
            path,
            filepath,
            chunk_size=chunk_size,
            timeout_in_seconds=timeout_in_seconds,
        ):
            yield (read, size)


# -----------------------------------------------------------------------------
# Standalone Utilities


def pkg_idname_is_valid_or_error(pkg_idname: str) -> Optional[str]:
    if not pkg_idname.isidentifier():
        return "Not a valid identifier"
    if "__" in pkg_idname:
        return "Only single separators are supported"
    if pkg_idname.startswith("_"):
        return "Names must not start with a \"_\""
    if pkg_idname.endswith("_"):
        return "Names must not end with a \"_\""
    return None


def pkg_manifest_is_valid_or_error(value: Dict[str, Any], *, from_repo: bool) -> Optional[str]:
    import string

    if not isinstance(value, dict):
        return "Expected value to be a dict, not a {!r}".format(type(value))

    known_keys_and_types = (
        ("name", str),
        ("description", str),
        ("version", str),
        ("type", str),

        ("archive_size", int),
        ("archive_hash", str),
        ("archive_url", str),
    ) if from_repo else (
        ("name", str),
        ("description", str),
        ("version", str),
        ("type", str),
    )

    value_extract = {}
    for x_key, x_ty in known_keys_and_types:
        x_val = value.get(x_key, ...)
        if x_val is ...:
            return "Missing \"{:s}\"".format(x_key)

        if x_ty is None:
            pass
        elif isinstance(x_val, x_ty):
            pass
        else:
            return "Expected \"{:s}\" to be a string, not a {!r}".format(x_key, type(x_val))

        value_extract[x_key] = x_val

    x_key = "version"
    x_val = value_extract[x_key]
    if not RE_MANIFEST_SEMVER.match(x_val):
        return "Expected key {!r}: to be a semantic-version, found {!r}".format(x_key, x_val)

    if from_repo:
        x_key = "archive_hash"
        x_val = value_extract[x_key]
        # Expect: `sha256:{HASH}`.
        # In the future we may support multiple hash types.
        x_val_hash_type, x_val_sep, x_val_hash_data = x_val.partition(":")
        if not x_val_sep:
            return "Expected key {!r}: to have a \":\" separator {!r}".format(x_key, x_val)
        del x_val_sep
        if x_val_hash_type == "sha256":
            if len(x_val_hash_data) != 64 or x_val_hash_data.strip(string.hexdigits):
                return "Expected key {!r}: to be 64 hex-digits, found {!r}".format(x_key, x_val)
        else:
            return "Expected key {!r}: to use a prefix in [\"sha256\"], found {!r}".format(x_key, x_val_hash_type)
        del x_val_hash_type, x_val_hash_data

        x_key = "archive_size"
        x_val = value_extract[x_key]
        if x_val <= 0:
            return "Expected key {!r}: to be a positive integer, found {!r}".format(x_key, x_val)

    return None


def repo_json_is_valid_or_error(filepath: str) -> Optional[str]:
    if not os.path.exists(filepath):
        return "File missing: " + filepath

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            result = json.load(fh)
    except BaseException as ex:
        return str(ex)

    if not isinstance(result, dict):
        return "Expected a dictionary, not a {!r}".format(type(result))

    for i, (key, value) in enumerate(result.items()):
        if not isinstance(key, str):
            return "Expected key at index {:d} to be a string, not a {!r}".format(i, type(key))

        if (error_msg := pkg_idname_is_valid_or_error(key)) is not None:
            return "Expected key at index {:d} to be an identifier, \"{:s}\" failed: {:s}".format(i, key, error_msg)

        if (error_msg := pkg_manifest_is_valid_or_error(value, from_repo=True)) is not None:
            return "Error at index {:d}: {:s}".format(i, error_msg)

    return None


def pkg_manifest_toml_is_valid_or_error(filepath: str) -> Tuple[Optional[str], Dict[str, Any]]:
    if not os.path.exists(filepath):
        return "File missing: " + filepath, {}

    try:
        with open(filepath, "rb") as fh:
            result = tomllib.load(fh)
    except BaseException as ex:
        return str(ex), {}

    error = pkg_manifest_is_valid_or_error(result, from_repo=False)
    if error is not None:
        return error, {}
    return None, result


def extract_metadata_from_data(data: bytes) -> Optional[Dict[str, Any]]:
    result = tomllib.loads(data.decode('utf-8'))
    assert isinstance(result, dict)
    return result


def extract_metadata_from_filepath(filepath: str) -> Optional[Dict[str, Any]]:
    with open(filepath, "rb") as fh:
        data = fh.read()
    result = extract_metadata_from_data(data)
    return result


def extract_metadata_from_archive(filepath: str) -> Optional[Dict[str, Any]]:
    with tarfile.open(filepath, "r:xz") as tar_fh:
        try:
            file_content = tar_fh.extractfile(PKG_MANIFEST_FILENAME_TOML)
        except KeyError:
            # TODO: check if there is a nicer way to handle this?
            # From a quick look there doesn't seem to be a good way
            # to do this using public methods.
            file_content = None

        if file_content is None:
            return None

        result = extract_metadata_from_data(file_content.read())
        assert isinstance(result, dict)
        return result


def repo_local_private_dir(*, local_dir: str) -> str:
    """
    Ensure the repos hidden directory exists.
    """
    return os.path.join(local_dir, REPO_LOCAL_PRIVATE_DIR)


def repo_local_private_dir_ensure(*, local_dir: str) -> str:
    """
    Ensure the repos hidden directory exists.
    """
    local_private_dir = repo_local_private_dir(local_dir=local_dir)
    if not os.path.isdir(local_private_dir):
        os.mkdir(local_private_dir)
    return local_private_dir


def repo_local_private_dir_ensure_with_subdir(*, local_dir: str, subdir: str) -> str:
    """
    Return a local directory used to cache package downloads.
    """
    local_private_subdir = os.path.join(repo_local_private_dir_ensure(local_dir=local_dir), subdir)
    if not os.path.isdir(local_private_subdir):
        os.mkdir(local_private_subdir)
    return local_private_subdir


def repo_sync_from_remote(*, msg_fn: MessageFn, repo_dir: str, local_dir: str, timeout_in_seconds: float) -> bool:
    """
    Load package information into the local path.
    """
    request_exit = False
    request_exit |= message_status(msg_fn, "Sync repo: {:s}".format(repo_dir))
    if request_exit:
        return False

    is_repo_filesystem = repo_is_filesystem(repo_dir=repo_dir)
    if is_repo_filesystem:
        remote_json_path = os.path.join(repo_dir, PKG_REPO_LIST_FILENAME)
    else:
        remote_json_path = remote_url_from_repo_url(repo_dir)

    local_private_dir = repo_local_private_dir_ensure(local_dir=local_dir)
    local_json_path = os.path.join(local_private_dir, PKG_REPO_LIST_FILENAME)
    local_json_path_temp = local_json_path + "@"

    if os.path.exists(local_json_path_temp):
        os.unlink(local_json_path_temp)

    with CleanupPathsContext(files=(local_json_path_temp,), directories=()):
        # TODO: time-out.
        request_exit |= message_status(msg_fn, "Sync downloading remote data")
        if request_exit:
            return False

        # No progress for file copying, assume local file system is fast enough.
        # `shutil.copyfile(remote_json_path, local_json_path_temp)`.
        try:
            read_total = 0
            for (read, size) in url_retrieve_to_filepath_iter_or_filesystem(
                    remote_json_path,
                    local_json_path_temp,
                    is_filesystem=is_repo_filesystem,
                    chunk_size=CHUNK_SIZE_DEFAULT,
                    timeout_in_seconds=timeout_in_seconds,
            ):
                request_exit |= message_progress(msg_fn, "Downloading...", read_total, size, 'BYTE')
                if request_exit:
                    break
                read_total += read
            del read_total

        except FileNotFoundError as ex:
            message_error(msg_fn, "sync: file-not-found ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False
        except TimeoutError as ex:
            message_error(msg_fn, "sync: timeout ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False
        except urllib.error.URLError as ex:
            message_error(msg_fn, "sync: URL error ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False
        except BaseException as ex:
            message_error(msg_fn, "sync: unexpected error ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False

        if request_exit:
            return False

        error_msg = repo_json_is_valid_or_error(local_json_path_temp)
        if error_msg is not None:
            message_error(msg_fn, "sync: invalid json ({!r}) reading {!r}!".format(error_msg, repo_dir))
            return False
        del error_msg

        request_exit |= message_status(msg_fn, "Sync complete: {:s}".format(repo_dir))
        if request_exit:
            return False

        if os.path.exists(local_json_path):
            os.unlink(local_json_path)

        # If this is a valid JSON, overwrite the existing file.
        os.rename(local_json_path_temp, local_json_path)

    return True


def repo_pkginfo_from_local(*, local_dir: str) -> Optional[Dict[str, Any]]:
    """
    Load package cache.
    """
    local_private_dir = repo_local_private_dir(local_dir=local_dir)
    local_json_path = os.path.join(local_private_dir, PKG_REPO_LIST_FILENAME)
    if not os.path.exists(local_json_path):
        return None

    with open(local_json_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)
        assert isinstance(result, dict)

    return result


def repo_pkginfo_from_local_with_idname_as_key(*, local_dir: str) -> Optional[PkgManifest_RepoDict]:
    result = repo_pkginfo_from_local(local_dir=local_dir)
    if result is None:
        return None

    result_new: PkgManifest_RepoDict = {}
    for key, value in result.items():
        result_new[key] = value
    return result_new


def repo_is_filesystem(*, repo_dir: str) -> bool:
    if repo_dir.startswith(("https://", "http://")):
        return False
    return True


# -----------------------------------------------------------------------------
# Generate Argument Handlers

def arg_handle_int_as_bool(value: str) -> bool:
    result = int(value)
    if result not in {0, 1}:
        raise argparse.ArgumentTypeError("Expected a 0 or 1")
    return bool(result)


def arg_handle_str_as_package_names(value: str) -> Sequence[str]:
    result = value.split(",")
    for pkg_idname in result:
        if (error_msg := pkg_idname_is_valid_or_error(pkg_idname)) is not None:
            raise argparse.ArgumentTypeError("Invalid name \"{:s}\". {:s}".format(pkg_idname, error_msg))
    return result


# -----------------------------------------------------------------------------
# Generate Repository


def generic_arg_package_list_positional(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        dest="packages",
        type=str,
        help=(
            "The packages to operate on (separated by \",\" without spaces)."
        ),
    )


def generic_arg_repo_dir(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--repo-dir",
        dest="repo_dir",
        type=str,
        help=(
            "The remote repository directory."
        ),
        required=True,
    )


def generic_arg_local_dir(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--local-dir",
        dest="local_dir",
        type=str,
        help=(
            "The local checkout."
        ),
        required=True,
    )


# Only for authoring.
def generic_arg_pkg_source_dir(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--pkg-source-dir",
        dest="pkg_source_dir",
        type=str,
        help=(
            "The package source directory."
        ),
        default=".",
    )


def generic_arg_pkg_output_dir(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--pkg-output-dir",
        dest="pkg_output_dir",
        type=str,
        help=(
            "The package output directory."
        ),
        default=".",
    )


def generic_arg_pkg_output_filepath(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--pkg-output-filepath",
        dest="pkg_output_filepath",
        type=str,
        help=(
            "The package output filepath."
        ),
        default=".",
    )


def generic_arg_output_type(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--output-type",
        dest="output_type",
        type=str,
        choices=('TEXT', 'JSON', 'JSON_0'),
        default='TEXT',
        help=(
            "The output type:\n"
            "- TEXT: Plain text.\n"
            "- JSON: Separated by new-lines.\n"
            "- JSON_0: Separated null bytes.\n"
        ),
        required=False,
    )


def generic_arg_local_cache(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--local-cache",
        dest="local_cache",
        type=arg_handle_int_as_bool,
        help=(
            "Use local cache, when disabled packages always download from remote."
        ),
        default=True,
        required=False,
    )


def generic_arg_timeout(subparse: argparse.ArgumentParser) -> None:
    subparse.add_argument(
        "--timeout",
        dest="timeout",
        type=float,
        help=(
            "Timeout when reading from remote location."
        ),
        default=10.0,
        required=False,
    )


class subcmd_server:

    def __new__(cls) -> Any:
        raise RuntimeError("{:s} should not be instantiated".format(cls))

    @staticmethod
    def generate(
            msg_fn: MessageFn,
            *,
            repo_dir: str,
    ) -> bool:

        is_repo_filesystem = repo_is_filesystem(repo_dir=repo_dir)
        if not is_repo_filesystem:
            message_error(msg_fn, "Directory: {!r} must be local!".format(repo_dir))
            return False

        if not os.path.isdir(repo_dir):
            message_error(msg_fn, "Directory: {!r} not found!".format(repo_dir))
            return False

        # Write package meta-data into each directory.
        repo_gen_dict = {}
        for entry in os.scandir(repo_dir):
            if not entry.name.endswith(PKG_EXT):
                continue

            # Harmless, but skip directories.
            if entry.is_dir():
                message_warn(msg_fn, "found unexpected directory {!r}".format(entry.name))
                continue

            filename = entry.name
            filepath = os.path.join(repo_dir, filename)
            manifest_dict = extract_metadata_from_archive(filepath)

            if manifest_dict is None:
                message_warn(msg_fn, "failed to extract meta-data from {!r}".format(filepath))
                continue

            pkg_idname = manifest_dict.pop("id")
            manifest = pkg_manifest_from_dict_and_validate(pkg_idname, manifest_dict)
            if isinstance(manifest, str):
                message_warn(msg_fn, "malformed meta-data from {!r}, error: {:s}".format(filepath, manifest))
                continue
            manifest_dict = manifest._asdict()
            # TODO: we could have a method besides `_asdict` that excludes the ID.
            del manifest_dict["id"]

            # These are added, ensure they don't exist.
            has_key_error = False
            for key in ("archive_url", "archive_size", "archive_hash"):
                if key not in manifest_dict:
                    continue
                message_warn(
                    msg_fn,
                    "malformed meta-data from {!r}, contains key it shouldn't: {:s}".format(filepath, key),
                )
                has_key_error = True
            if has_key_error:
                continue

            # A relative URL.
            manifest_dict["archive_url"] = "./" + filename

            # Add archive variables, see: `PkgManifest_Archive`.
            (
                manifest_dict["archive_size"],
                manifest_dict["archive_hash"],
            ) = sha256_from_file(filepath, hash_prefix=True)

            repo_gen_dict[pkg_idname] = manifest_dict

        filepath_repo_json = os.path.join(repo_dir, PKG_REPO_LIST_FILENAME)

        with open(filepath_repo_json, "w", encoding="utf-8") as fh:
            json.dump(repo_gen_dict, fh, indent=2)
        message_status(msg_fn, "found {:d} packages.".format(len(repo_gen_dict)))

        return True


class subcmd_client:

    def __new__(cls) -> Any:
        raise RuntimeError("{:s} should not be instantiated".format(cls))

    @staticmethod
    def list_packages(
            msg_fn: MessageFn,
            repo_dir: str,
            timeout_in_seconds: float,
    ) -> bool:
        is_repo_filesystem = repo_is_filesystem(repo_dir=repo_dir)
        if is_repo_filesystem:
            if not os.path.isdir(repo_dir):
                message_error(msg_fn, "Directory: {!r} not found!".format(repo_dir))
                return False

        if is_repo_filesystem:
            filepath_repo_json = os.path.join(repo_dir, PKG_REPO_LIST_FILENAME)
            if not os.path.exists(filepath_repo_json):
                message_error(msg_fn, "File: {!r} not found!".format(filepath_repo_json))
                return False
        else:
            filepath_repo_json = remote_url_from_repo_url(repo_dir)

        # TODO: validate JSON content.
        try:
            result = io.BytesIO()
            for block in url_retrieve_to_data_iter_or_filesystem(
                    filepath_repo_json,
                    is_filesystem=is_repo_filesystem,
                    timeout_in_seconds=timeout_in_seconds,
                    chunk_size=CHUNK_SIZE_DEFAULT,
            ):
                result.write(block)

        except FileNotFoundError as ex:
            message_error(msg_fn, "list: file-not-found ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False
        except TimeoutError as ex:
            message_error(msg_fn, "list: timeout ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False
        except urllib.error.URLError as ex:
            message_error(msg_fn, "list: URL error ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False
        except BaseException as ex:
            message_error(msg_fn, "list: unexpected error ({:s}) reading {!r}!".format(str(ex), repo_dir))
            return False

        result_str = result.getvalue().decode("utf-8")
        del result
        repo_gen_dict = json.loads(result_str)

        items: List[Tuple[str, Dict[str, Any]]] = list(repo_gen_dict.items())
        items.sort(key=lambda elem: elem[0])

        request_exit = False
        for pkg_idname, elem in items:
            request_exit |= message_status(
                msg_fn,
                "{:s}({:s}): {:s}".format(pkg_idname, elem.get("version"), elem.get("name")),
            )
            if request_exit:
                return False

        return True

    @staticmethod
    def sync(
            msg_fn: MessageFn,
            *,
            repo_dir: str,
            local_dir: str,
            timeout_in_seconds: float,
    ) -> bool:
        success = repo_sync_from_remote(
            msg_fn=msg_fn,
            repo_dir=repo_dir,
            local_dir=local_dir,
            timeout_in_seconds=timeout_in_seconds,
        )
        return success

    @staticmethod
    def install_packages(
            msg_fn: MessageFn,
            *,
            repo_dir: str,
            local_dir: str,
            local_cache: bool,
            packages: Sequence[str],
            timeout_in_seconds: float,
    ) -> bool:
        # Extract...
        is_repo_filesystem = repo_is_filesystem(repo_dir=repo_dir)
        json_data = repo_pkginfo_from_local_with_idname_as_key(local_dir=local_dir)
        if json_data is None:
            # TODO: raise warning.
            return False

        # Most likely this doesn't have duplicates,but any errors procured by duplicates
        # are likely to be obtuse enough that it's better to guarantee there are none.
        packages = tuple(sorted(set(packages)))

        # Ensure a private directory so a local cache can be created.
        local_cache_dir = repo_local_private_dir_ensure_with_subdir(local_dir=local_dir, subdir="cache")

        has_error = False
        packages_info: List[PkgManifest_Archive] = []
        for pkg_idname in packages:
            pkg_info = json_data.get(pkg_idname)
            if pkg_info is None:
                message_error(msg_fn, "Package \"{:s}\", not found".format(pkg_idname))
                has_error = True
                continue
            manifest_archive = pkg_manifest_archive_from_dict_and_validate(pkg_idname, pkg_info)
            if isinstance(manifest_archive, str):
                message_error(msg_fn, "Package malformed meta-data for \"{:s}\", error: {:s}".format(
                    pkg_idname,
                    manifest_archive,
                ))
                has_error = True
                continue

            packages_info.append(manifest_archive)

        if has_error:
            return False
        del has_error

        request_exit = False

        for manifest_archive in packages_info:
            pkg_idname = manifest_archive.manifest.id
            # Archive name.
            archive_size_expected = manifest_archive.archive_size
            archive_hash_expected = manifest_archive.archive_hash
            pkg_archive_url = manifest_archive.archive_url

            # Local path.
            filepath_local_cache_archive = os.path.join(local_cache_dir, pkg_idname + PKG_EXT)

            # Remote path.
            if pkg_archive_url.startswith("./"):
                if is_repo_filesystem:
                    filepath_remote_archive = os.path.join(repo_dir, pkg_archive_url[2:])
                else:
                    if REMOTE_REPO_HAS_JSON_IMPLIED:
                        # TODO: use `urllib.parse.urlsplit(..)`.
                        # NOTE: strip the path until the directory.
                        # Convert: `https://foo.bar/bl_ext_repo.json` -> https://foo.bar/ARCHIVE_NAME
                        filepath_remote_archive = urllib.parse.urljoin(repo_dir.rpartition("/")[0], pkg_archive_url[2:])
                    else:
                        filepath_remote_archive = urllib.parse.urljoin(repo_dir, pkg_archive_url[2:])
                is_pkg_filesystem = is_repo_filesystem
            else:
                filepath_remote_archive = pkg_archive_url
                is_pkg_filesystem = repo_is_filesystem(repo_dir=pkg_archive_url)

            # Check if the cache should be used.
            found = False
            if os.path.exists(filepath_local_cache_archive):
                if (
                        local_cache and (
                            archive_size_expected,
                            archive_hash_expected,
                        ) == sha256_from_file(filepath_local_cache_archive, hash_prefix=True)
                ):
                    found = True
                else:
                    os.unlink(filepath_local_cache_archive)

            if not found:
                # Create `filepath_local_cache_archive`.
                filename_archive_size_test = 0
                sha256 = hashlib.new('sha256')

                # NOTE(@ideasman42): There is more logic in the try/except block than I'd like.
                # Refactoring could be done to avoid that but it ends up making logic difficult to follow.
                try:
                    with open(filepath_local_cache_archive, "wb") as fh_cache:
                        for block in url_retrieve_to_data_iter_or_filesystem(
                                filepath_remote_archive,
                                is_filesystem=is_pkg_filesystem,
                                chunk_size=CHUNK_SIZE_DEFAULT,
                                timeout_in_seconds=timeout_in_seconds,
                        ):
                            request_exit |= message_progress(
                                msg_fn,
                                "Downloading \"{:s}\"".format(pkg_idname),
                                filename_archive_size_test,
                                archive_size_expected,
                                'BYTE',
                            )
                            if request_exit:
                                break
                            fh_cache.write(block)
                            sha256.update(block)
                            filename_archive_size_test += len(block)

                except FileNotFoundError as ex:
                    message_error(
                        msg_fn,
                        "install: file-not-found ({:s}) reading {!r}!".format(str(ex), filepath_remote_archive),
                    )
                    return False
                except TimeoutError as ex:
                    message_error(
                        msg_fn,
                        "install: timeout ({:s}) reading {!r}!".format(str(ex), filepath_remote_archive),
                    )
                    return False
                except urllib.error.URLError as ex:
                    message_error(
                        msg_fn,
                        "install: URL error ({:s}) reading {!r}!".format(str(ex), filepath_remote_archive),
                    )
                    return False
                except BaseException as ex:
                    message_error(
                        msg_fn,
                        "install: unexpected error ({:s}) reading {!r}!".format(str(ex), filepath_remote_archive),
                    )
                    return False

                if request_exit:
                    return False

                # Validate:
                if filename_archive_size_test != archive_size_expected:
                    message_warn(msg_fn, "Archive size mismatch \"{:s}\", expected {:d}, was {:d}".format(
                        pkg_idname,
                        archive_size_expected,
                        filename_archive_size_test,
                    ))
                    return False
                filename_archive_hash_test = "sha256:" + sha256.hexdigest()
                if filename_archive_hash_test != archive_hash_expected:
                    message_warn(msg_fn, "Archive checksum mismatch \"{:s}\", expected {:s}, was {:s}".format(
                        pkg_idname,
                        archive_hash_expected,
                        filename_archive_hash_test,
                    ))
                    return False
                del filename_archive_size_test
                del filename_archive_hash_test
            del found
            del filepath_local_cache_archive

        # All packages have been downloaded, install them.
        for manifest_archive in packages_info:
            pkg_idname = manifest_archive.manifest.id
            pkg_version = manifest_archive.manifest.version

            # We have the cache, extract it to a directory.
            # This will be a directory.
            filepath_local_pkg = os.path.join(local_dir, pkg_idname)
            filepath_local_cache_archive = os.path.join(local_cache_dir, pkg_idname + PKG_EXT)

            # First extract into a temporary directory, validate the package is not corrupt,
            # then move the package to it's expected location.
            filepath_local_pkg_temp = filepath_local_pkg + "@"

            # It's unlikely this exist, nevertheless if it does - it must be removed.
            if os.path.isdir(filepath_local_pkg_temp):
                shutil.rmtree(filepath_local_pkg_temp)

            # Remove `filepath_local_pkg_temp` if this block exits or continues.
            with CleanupPathsContext(files=(), directories=(filepath_local_pkg_temp,)):
                with tarfile.open(filepath_local_cache_archive, mode="r:xz") as tar_fh:
                    tar_fh.extractall(filepath_local_pkg_temp)

                # TODO: assume the package is OK.
                filepath_local_manifest_toml = os.path.join(filepath_local_pkg_temp, PKG_MANIFEST_FILENAME_TOML)
                if not os.path.exists(filepath_local_manifest_toml):
                    message_warn(msg_fn, "Package manifest not found: {:s}".format(filepath_local_manifest_toml))
                    continue

                # Check the package manifest is valid.
                error_msg, manifest_from_archive = pkg_manifest_toml_is_valid_or_error(filepath_local_manifest_toml)
                if error_msg is not None:
                    message_warn(msg_fn, "Package manifest invalid: {:s}".format(error_msg))
                    continue

                # The archive ID name must match the server name,
                # otherwise the package will install but not be able to collate
                # the installed package with the remote ID.
                if pkg_idname != manifest_from_archive["id"]:
                    message_warn(
                        msg_fn,
                        "Package ID mismatch (remote: \"{:s}\", archive: \"{:s}\")".format(
                            pkg_idname,
                            manifest_from_archive["id"],
                        )
                    )
                    continue
                if pkg_version != manifest_from_archive["version"]:
                    message_warn(
                        msg_fn,
                        "Package version mismatch (remote: \"{:s}\", archive: \"{:s}\")".format(
                            pkg_version,
                            manifest_from_archive["version"],
                        )
                    )
                    continue

                is_reinstall = False
                if os.path.isdir(filepath_local_pkg):
                    shutil.rmtree(filepath_local_pkg)
                    is_reinstall = True

                os.rename(filepath_local_pkg_temp, filepath_local_pkg)

            # TODO: think of how to handle messages & progress.
            if is_reinstall:
                message_status(msg_fn, "Re-Installed \"{:s}\"".format(pkg_idname))
            else:
                message_status(msg_fn, "Installed \"{:s}\"".format(pkg_idname))

        return True

    @staticmethod
    def uninstall_packages(
            msg_fn: MessageFn,
            *,
            local_dir: str,
            packages: Sequence[str],
    ) -> bool:
        if not os.path.isdir(local_dir):
            message_error(msg_fn, "Missing local \"{:s}\"".format(local_dir))
            return False

        # Most likely this doesn't have duplicates,but any errors procured by duplicates
        # are likely to be obtuse enough that it's better to guarantee there are none.
        packages = tuple(sorted(set(packages)))

        packages_valid = []

        error = False
        for pkg_idname in packages:
            # As this simply removes the directories right now,
            # validate this path cannot be used for an unexpected outcome,
            # or using `../../` to remove directories that shouldn't.
            if (pkg_idname in {"", ".", ".."}) or ("\\" in pkg_idname or "/" in pkg_idname):
                message_error(msg_fn, "Package name invalid \"{:s}\"".format(pkg_idname))
                error = True
                continue

            # This will be a directory.
            filepath_local_pkg = os.path.join(local_dir, pkg_idname)
            if not os.path.isdir(filepath_local_pkg):
                message_error(msg_fn, "Package not found \"{:s}\"".format(pkg_idname))
                error = True
                continue

            packages_valid.append(pkg_idname)
        del filepath_local_pkg

        if error:
            return False

        for pkg_idname in packages_valid:
            filepath_local_pkg = os.path.join(local_dir, pkg_idname)
            try:
                shutil.rmtree(filepath_local_pkg)
            except BaseException as ex:
                message_error(msg_fn, "Failure to remove \"{:s}\" with error ({:s})".format(pkg_idname, str(ex)))
                continue

            message_status(msg_fn, "Removed \"{:s}\"".format(pkg_idname))

        return True


class subcmd_author:

    @staticmethod
    def pkg_build(
            msg_fn: MessageFn,
            *,
            pkg_source_dir: str,
            pkg_output_dir: str,
            pkg_output_filepath: str,
    ) -> bool:
        if not os.path.isdir(pkg_source_dir):
            message_error(msg_fn, "Missing local \"{:s}\"".format(pkg_source_dir))
            return False

        if pkg_output_dir != "." and pkg_output_filepath != ".":
            message_error(msg_fn, "Both output directory & output filepath set, set one or the other")
            return False

        pkg_manifest_filepath = os.path.join(pkg_source_dir, PKG_MANIFEST_FILENAME_TOML)

        if not os.path.exists(pkg_manifest_filepath):
            message_error(msg_fn, "File \"{:s}\" not found!".format(pkg_manifest_filepath))
            return False

        manifest = pkg_manifest_from_toml_and_validate(pkg_manifest_filepath)
        if isinstance(manifest, str):
            message_error(msg_fn, "Error parsing TOML \"{:s}\" {:s}".format(pkg_manifest_filepath, manifest))
            return False

        pkg_filename = manifest.id + PKG_EXT

        if pkg_output_filepath != ".":
            outfile = pkg_output_filepath
        else:
            outfile = os.path.join(pkg_output_dir, pkg_filename)

        outfile_temp = outfile + "@"

        filenames_root_exclude = {
            pkg_filename,
            # This is added, converted from the TOML.
            PKG_REPO_LIST_FILENAME,

            # We could exclude the manifest: `PKG_MANIFEST_FILENAME_TOML`
            # but it's now used so a generation step isn't needed.
        }

        request_exit = False

        request_exit |= message_status(msg_fn, "Building {:s}".format(pkg_filename))
        if request_exit:
            return False

        with CleanupPathsContext(files=(outfile_temp,), directories=()):
            with tarfile.open(outfile_temp, "w:xz") as tar:
                for filepath_abs, filepath_rel in scandir_recursive(
                        pkg_source_dir,
                        # Be more advanced in the future, for now ignore dot-files (`.git`) .. etc.
                        filter_fn=lambda x: not x.startswith(".")
                ):
                    if filepath_rel in filenames_root_exclude:
                        continue

                    with open(filepath_abs, 'rb') as fh:
                        size = os.fstat(fh.fileno()).st_size
                        message_status(msg_fn, "add \"{:s}\", {:d}".format(filepath_rel, size))
                        info = tarfile.TarInfo(filepath_rel)
                        info.size = size
                        del size
                        tar.addfile(info, fh)

                request_exit |= message_status(msg_fn, "complete")
                if request_exit:
                    return False

            if os.path.exists(outfile):
                os.unlink(outfile)
            os.rename(outfile_temp, outfile)

        message_status(msg_fn, "created \"{:s}\", {:d}".format(outfile, os.path.getsize(outfile)))
        return True


class subcmd_dummy:

    @staticmethod
    def repo(
            msg_fn: MessageFn,
            *,
            repo_dir: str,
            package_names: Sequence[str],
    ) -> bool:

        def msg_fn_no_done(ty: str, data: PrimTypeOrSeq) -> bool:
            if ty == 'DONE':
                return False
            return msg_fn(ty, data)

        # Ensure package names are valid.
        package_names = tuple(set(package_names))
        for pkg_idname in package_names:
            if (error_msg := pkg_idname_is_valid_or_error(pkg_idname)) is None:
                continue
            message_error(
                msg_fn,
                "key \"id\", \"{:s}\" doesn't match expected format, \"{:s}\"".format(pkg_idname, error_msg),
            )
            return False

        if not repo_is_filesystem(repo_dir=repo_dir):
            message_error(msg_fn, "Generating a repository on a remote path is not supported")
            return False

        # Unlike most other commands, create the repo_dir it doesn't already exist.
        if not os.path.exists(repo_dir):
            try:
                os.makedirs(repo_dir)
            except BaseException as ex:
                message_error(msg_fn, "Failed to create \"{:s}\" with error: {!r}".format(repo_dir, ex))
                return False

        import tempfile
        for pkg_idname in package_names:
            with tempfile.TemporaryDirectory(suffix="pkg-repo") as temp_dir_source:
                pkg_src_dir = os.path.join(temp_dir_source, pkg_idname)
                os.makedirs(pkg_src_dir)
                pkg_name = pkg_idname.replace("_", " ").title()
                with open(os.path.join(pkg_src_dir, PKG_MANIFEST_FILENAME_TOML), "w", encoding="utf-8") as fh:
                    fh.write("""# Example\n""")
                    fh.write("""id = "{:s}"\n""".format(pkg_idname))
                    fh.write("""name = "{:s}"\n""".format(pkg_name))
                    fh.write("""type = "addon"\n""")
                    fh.write("""author = "Developer Name"\n""")
                    fh.write("""version = "1.0.0"\n""")
                    fh.write("""description = "This is a package"\n""")

                with open(os.path.join(pkg_src_dir, "__init__.py"), "w", encoding="utf-8") as fh:
                    fh.write("""
def register():
    print("Register:", __name__)

def unregister():
    print("Unregister:", __name__)
""")

                    fh.write("""# Dummy.\n""")
                    # Generate some random ASCII-data.
                    for i, line in enumerate(random_acii_lines(seed=pkg_idname, width=80)):
                        if i > 1000:
                            break
                        fh.write("# {:s}\n".format(line))

                # `{cmd} pkg-build --pkg-source-dir {pkg_src_dir} --pkg-output-dir {repo_dir}`.
                if not subcmd_author.pkg_build(
                    msg_fn_no_done,
                    pkg_source_dir=pkg_src_dir,
                    pkg_output_dir=repo_dir,
                    pkg_output_filepath=".",
                ):
                    # Error running command.
                    return False

        # `{cmd} server-generate --repo-dir {repo_dir}`.
        if not subcmd_server.generate(
            msg_fn_no_done,
            repo_dir=repo_dir,
        ):
            # Error running command.
            return False

        message_done(msg_fn)
        return True

    @staticmethod
    def progress(
            msg_fn: MessageFn,
            *,
            time_duration: float,
            time_delay: float,
    ) -> bool:
        import time
        request_exit = False
        time_start = time.time() if (time_duration > 0.0) else 0.0
        size_beg = 0
        size_end = 100
        while time_duration == 0.0 or (time.time() - time_start < time_duration):
            request_exit |= message_progress(msg_fn, "Demo", size_beg, size_end, 'BYTE')
            if request_exit:
                break
            size_beg += 1
            if size_beg > size_end:
                size_beg = 0
            time.sleep(time_delay)
        if request_exit:
            message_done(msg_fn)
            return False

        message_done(msg_fn)
        return True


# -----------------------------------------------------------------------------
# Server Manipulating Actions


def argparse_create_server_generate(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "server-generate",
        help="Create a listing from all packages.",
        description="Test.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    generic_arg_repo_dir(subparse)
    generic_arg_output_type(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_server.generate(
            msg_fn_from_args(args),
            repo_dir=args.repo_dir,
        ),
    )


# -----------------------------------------------------------------------------
# Client Queries

def argparse_create_client_list(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "list",
        help="List all available packages.",
        description="List all available packages.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    generic_arg_repo_dir(subparse)
    generic_arg_local_dir(subparse)
    generic_arg_output_type(subparse)
    generic_arg_timeout(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_client.list_packages(
            msg_fn_from_args(args),
            args.repo_dir,
            timeout_in_seconds=args.timeout,
        ),
    )


# -----------------------------------------------------------------------------
# Client Manipulating Actions

def argparse_create_client_sync(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "sync",
        help="Refresh from the remote repository.",
        description="Refresh from remote repository (sync).",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    generic_arg_repo_dir(subparse)
    generic_arg_local_dir(subparse)
    generic_arg_output_type(subparse)
    generic_arg_timeout(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_client.sync(
            msg_fn_from_args(args),
            repo_dir=args.repo_dir,
            local_dir=args.local_dir,
            timeout_in_seconds=args.timeout,
        ),
    )


def argparse_create_client_install(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "install",
        help="Install package.",
        description="Install the package.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    generic_arg_package_list_positional(subparse)

    generic_arg_repo_dir(subparse)
    generic_arg_local_dir(subparse)
    generic_arg_local_cache(subparse)
    generic_arg_output_type(subparse)
    generic_arg_timeout(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_client.install_packages(
            msg_fn_from_args(args),
            repo_dir=args.repo_dir,
            local_dir=args.local_dir,
            local_cache=args.local_cache,
            packages=args.packages.split(","),
            timeout_in_seconds=args.timeout,
        ),
    )


def argparse_create_client_uninstall(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "uninstall",
        help="Uninstall a package.",
        description="Uninstall the package.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    generic_arg_package_list_positional(subparse)

    generic_arg_local_dir(subparse)
    generic_arg_output_type(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_client.uninstall_packages(
            msg_fn_from_args(args),
            local_dir=args.local_dir,
            packages=args.packages.split(","),
        ),
    )


# -----------------------------------------------------------------------------
# Authoring Actions

def argparse_create_author_build(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "pkg-build",
        help="Build a package.",
        description="Build a packaging in the current directory.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    generic_arg_pkg_source_dir(subparse)
    generic_arg_pkg_output_dir(subparse)
    generic_arg_pkg_output_filepath(subparse)

    generic_arg_output_type(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_author.pkg_build(
            msg_fn_from_args(args),
            pkg_source_dir=args.pkg_source_dir,
            pkg_output_dir=args.pkg_output_dir,
            pkg_output_filepath=args.pkg_output_filepath,
        ),
    )


# -----------------------------------------------------------------------------
# Dummy Repo


def argparse_create_dummy_repo(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "dummy-repo",
        help="Create a dummy repository.",
        description="Create a dummy repository, intended for testing.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparse.add_argument(
        "--package-names",
        dest="package_names",
        type=arg_handle_str_as_package_names,
        help=(
            "Comma separated list of package names to create (no-spaces)."
        ),
        required=True,
    )

    generic_arg_output_type(subparse)
    generic_arg_repo_dir(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_dummy.repo(
            msg_fn_from_args(args),
            repo_dir=args.repo_dir,
            package_names=args.package_names,
        ),
    )

# -----------------------------------------------------------------------------
# Dummy Output


def argparse_create_dummy_progress(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparse = subparsers.add_parser(
        "dummy-progress",
        help="Dummy progress output.",
        description="Demo output.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparse.add_argument(
        "--time-duration",
        dest="time_duration",
        type=float,
        help=(
            "How long to run the demo for (zero to run forever)."
        ),
        default=0.0,
    )
    subparse.add_argument(
        "--time-delay",
        dest="time_delay",
        type=float,
        help=(
            "Delay between updates."
        ),
        default=0.05,
    )

    generic_arg_output_type(subparse)

    subparse.set_defaults(
        func=lambda args: subcmd_dummy.progress(
            msg_fn_from_args(args),
            time_duration=args.time_duration,
            time_delay=args.time_delay,
        ),
    )


def argparse_create() -> argparse.ArgumentParser:

    usage_text = "blender_ext!\n" + __doc__

    parser = argparse.ArgumentParser(
        prog="blender_ext",
        description=usage_text,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        help='additional help',
    )

    argparse_create_server_generate(subparsers)

    # Queries.
    argparse_create_client_list(subparsers)

    # Manipulating Actions.
    argparse_create_client_sync(subparsers)
    argparse_create_client_install(subparsers)
    argparse_create_client_uninstall(subparsers)

    # Authoring Commands.
    argparse_create_author_build(subparsers)

    # Dummy commands.
    argparse_create_dummy_repo(subparsers)
    argparse_create_dummy_progress(subparsers)

    return parser


# -----------------------------------------------------------------------------
# Message Printing Functions

# Follows `MessageFn` convention.
def msg_print_text(ty: str, data: PrimTypeOrSeq) -> bool:
    assert ty in MESSAGE_TYPES
    if isinstance(data, (list, tuple)):
        sys.stdout.write("{:s}: {:s}\n".format(ty, ", ".join(str(x) for x in data)))
    else:
        sys.stdout.write("{:s}: {:s}\n".format(ty, str(data)))
    return REQUEST_EXIT


def msg_print_json_impl(ty: str, data: PrimTypeOrSeq) -> bool:
    assert ty in MESSAGE_TYPES
    sys.stdout.write(json.dumps([ty, data]))
    return REQUEST_EXIT


def msg_print_json(ty: str, data: PrimTypeOrSeq) -> bool:
    msg_print_json_impl(ty, data)
    sys.stdout.write("\n")
    sys.stdout.flush()
    return REQUEST_EXIT


def msg_print_json_0(ty: str, data: PrimTypeOrSeq) -> bool:
    msg_print_json_impl(ty, data)
    sys.stdout.write("\0")
    sys.stdout.flush()
    return REQUEST_EXIT


def msg_fn_from_args(args: argparse.Namespace) -> MessageFn:
    match args.output_type:
        case 'JSON':
            return msg_print_json
        case 'JSON_0':
            return msg_print_json_0
        case 'TEXT':
            return msg_print_text

    raise Exception("Unknown output!")


def main(argv: Optional[List[str]] = None) -> bool:
    if "--version" in sys.argv:
        sys.stdout.write("{:s}\n".format(VERSION))
        return True

    parser = argparse_create()
    args = parser.parse_args(argv)
    # Call sub-parser callback.
    if not hasattr(args, "func"):
        parser.print_help()
        return True

    result = args.func(args)
    assert isinstance(result, bool)
    return result


if __name__ == "__main__":
    # TODO: `sys.exit(..)` exit-code.
    main()
