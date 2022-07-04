# SPDX-License-Identifier: GPL-2.0-or-later

import os


def blend_list(path):
    for dirpath, dirnames, filenames in os.walk(path):
        # skip '.git'
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if filename.lower().endswith(".blend"):
                filepath = os.path.join(dirpath, filename)
                yield filepath


def generate(dirpath, random_order, **kwargs):
    files = list(blend_list(dirpath))
    if random_order:
        import random
        random.shuffle(files)
    else:
        files.sort()

    config = []
    for f in files:
        defaults = kwargs.copy()
        defaults["file"] = f
        config.append(defaults)

    return config, dirpath


def as_string(dirpath, random_order, exit, **kwargs):
    """ Config loader is in demo_mode.py
    """
    cfg, dirpath = generate(dirpath, random_order, **kwargs)

    # hint for reader, can be used if files are not found.
    cfg_str = [
        "# generated file\n",
        "\n",
        "# edit the search path so other systems may find the files below\n",
        "# based on name only if the absolute paths cannot be found\n",
        "# Use '//' for current blend file path.\n",
        "\n",
        "search_path = %r\n" % dirpath,
        "\n",
        "exit = %r\n" % exit,
        "\n",
    ]

    # All these work but use nicest formatting!
    if 0:  # works but not nice to edit.
        cfg_str += ["config = %r" % cfg]
    elif 0:
        import pprint
        cfg_str += ["config = %s" % pprint.pformat(cfg, indent=0, width=120)]
    elif 0:
        cfg_str += [("config = %r" % cfg).replace("{", "\n    {")]
    else:
        import pprint

        def dict_as_kw(d):
            return "dict(%s)" % ", ".join(("%s=%s" % (k, pprint.pformat(v))) for k, v in sorted(d.items()))
        ident = "    "
        cfg_str += ["config = [\n"]
        for cfg_item in cfg:
            cfg_str += ["%s%s,\n" % (ident, dict_as_kw(cfg_item))]
        cfg_str += ["%s]\n\n" % ident]

    return "".join(cfg_str), dirpath
