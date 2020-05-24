#
# Copyright (C) 2016-2019 by Razvan Radulescu, Nathan Lovato, and contributors
#
# This file is part of Power Sequencer.
#
# Power Sequencer is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Sequencer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Power Sequencer. If
# not, see <https://www.gnu.org/licenses/>.
#
from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


if __name__ == "__main__":
    setup(
        name="bpsproxy",
        version="0.2.1",
        description="Blender Power Sequencer proxy generator tool",
        long_description=readme(),
        long_description_content_type="text/markdown",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Environment :: Console",
            "Intended Audience :: End Users/Desktop",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Natural Language :: English",
            "Programming Language :: Python :: 3.3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3",
            "Topic :: Multimedia :: Video",
            "Topic :: Utilities",
        ],
        url="https://github.com/GDquest/BPSProxy",
        keywords="blender proxy vse sequence editor productivity",
        author="Răzvan C. Rădulescu",
        author_email="razcore.art@gmail.com",
        license="GPLv3",
        packages=["bpsproxy"],
        install_requires=["tqdm"],
        zip_safe=False,
        entry_points={"console_scripts": ["bpsproxy=bpsproxy.__main__:main"]},
        include_package_data=True,
    )
