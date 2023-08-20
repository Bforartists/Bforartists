#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2020-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime


# Used date format: "September 30, 2020"
DATE_FORMAT = "%B %d, %Y"


class Version:
    """
    Version class that extracts the major, minor and build from
    a version string
    """

    def __init__(self, version: str):
        self.version = version
        v = version.split(".")
        self.major = v[0]
        self.minor = v[1]
        self.build = v[2]

    def __str__(self) -> str:
        return self.version


def get_download_file_names(version: Version):
    yield (f"blender-{version}-linux-x64.tar.xz", "Linux")
    yield (f"blender-{version}-macos-x64.dmg", "macOS - Intel")
    yield (f"blender-{version}-macos-arm64.dmg", "macOS - Apple Silicon")
    yield (f"blender-{version}-windows-x64.msi", "Windows - Installer")
    yield (f"blender-{version}-windows-x64.zip", "Windows - Portable (.zip)")


def get_download_url(version: Version, file_name: str) -> str:
    """
    Get the download url for the given version and file_name
    """
    return (f"https://www.blender.org/download/release/Blender{version.major}"
            f".{version.minor}/{file_name}")


def generate_html(version: Version) -> str:
    """
    Generate download urls and format them into an HTML string
    """
    today = datetime.date.today()
    lines = []
    lines.append(f"Released on {today.strftime(DATE_FORMAT)}.")
    lines.append("")
    lines.append("<ul>")
    for file_name, display_name in get_download_file_names(version):
        download_url = get_download_url(version, file_name)
        lines.append(f"  <li><a href=\"{download_url}\">{display_name}</a></li>")
    lines.append("</ul>")

    return "\n".join(lines)


def print_urls(version: str):
    """
    Generate the download urls and print them to the console.
    """
    print(generate_html(Version(version)))
