# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENSE BLOCK *****

# <pep8 compliant>

# Global settings used by all scripts in this dir.
# XXX Before any use of the tools in this dir, please make a copy of this file
#     named "setting.py"
# XXX This is a template, most values should be OK, but some you’ll have to
#     edit (most probably, BLENDER_EXEC and SOURCE_DIR).

import os.path


###############################################################################
# MISC
###############################################################################

# The languages defined in Blender.
LANGUAGES_CATEGORIES = (
    # Min completeness level, UI english label.
    ( 0.95, "Complete"),
    ( 0.33, "In Progress"),
    ( -1.0, "Starting"),
)
LANGUAGES = (
    # ID, UI english label, ISO code.
    ( 0, "Default (Default)", "DEFAULT"),
    ( 1, "English (English)", "en_US"),
    ( 2, "Japanese (日本語)", "ja_JP"),
    ( 3, "Dutch (Nederlandse taal)", "nl_NL"),
    ( 4, "Italian (Italiano)", "it_IT"),
    ( 5, "German (Deutsch)", "de_DE"),
    ( 6, "Finnish (Suomi)", "fi_FI"),
    ( 7, "Swedish (Svenska)", "sv_SE"),
    ( 8, "French (Français)", "fr_FR"),
    ( 9, "Spanish (Español)", "es"),
    (10, "Catalan (Català)", "ca_AD"),
    (11, "Czech (Český)", "cs_CZ"),
    (12, "Portuguese (Português)", "pt_PT"),
    (13, "Simplified Chinese (简体中文)", "zh_CN"),
    (14, "Traditional Chinese (繁體中文)", "zh_TW"),
    (15, "Russian (Русский)", "ru_RU"),
    (16, "Croatian (Hrvatski)", "hr_HR"),
    (17, "Serbian (Српски)", "sr_RS"),
    (18, "Ukrainian (Український)", "uk_UA"),
    (19, "Polish (Polski)", "pl_PL"),
    (20, "Romanian (Român)", "ro_RO"),
    # Using the utf8 flipped form of Arabic (العربية).
    (21, "Arabic (ﺔﻴﺑﺮﻌﻟﺍ)", "ar_EG"),
    (22, "Bulgarian (Български)", "bg_BG"),
    (23, "Greek (Ελληνικά)", "el_GR"),
    (24, "Korean (한국 언어)", "ko_KR"),
    (25, "Nepali (नेपाली)", "ne_NP"),
    # Using the utf8 flipped form of Persian (فارسی).
    (26, "Persian (ﯽﺳﺭﺎﻓ)", "fa_IR"),
    (27, "Indonesian (Bahasa indonesia)", "id_ID"),
    (28, "Serbian Latin (Srpski latinica)", "sr_RS@latin"),
    (29, "Kyrgyz (Кыргыз тили)", "ky_KG"),
    (30, "Turkish (Türkçe)", "tr_TR"),
    (31, "Hungarian (Magyar)", "hu_HU"),
    (32, "Brazilian Portuguese (Português do Brasil)", "pt_BR"),
    # Using the utf8 flipped form of Hebrew (עִבְרִית)).
    (33, "Hebrew (תירִבְעִ)", "he_IL"),
    (34, "Estonian (Eestlane)", "et_EE"),
    (35, "Esperanto (Esperanto)", "eo"),
    (36, "Spanish from Spain (Español de España)", "es_ES"),
)

# Name of language file used by Blender to generate translations' menu.
LANGUAGES_FILE = "languages"

# The min level of completeness for a po file to be imported from /branches
# into /trunk, as a percentage. -1 means "import everything".
IMPORT_MIN_LEVEL = -1

# Languages in /branches we do not want to import in /trunk currently...
IMPORT_LANGUAGES_SKIP = {'bg', 'ca', 'fi', 'el', 'ko', 'ne', 'pl', 'ro'}

# The comment prefix used in generated messages.txt file.
COMMENT_PREFIX = "#~ "

# The comment prefix used to mark sources of msgids, in po's.
COMMENT_PREFIX_SOURCE = "#: "

# The comment prefix used in generated messages.txt file.
CONTEXT_PREFIX = "MSGCTXT:"

# Default context.
CONTEXT_DEFAULT = ""

# Undocumented operator placeholder string.
UNDOC_OPS_STR = "(undocumented operator)"

# The gettext domain.
DOMAIN = "blender"

# Our own "gettext" stuff.
# File type (ext) to parse.
PYGETTEXT_ALLOWED_EXTS = {".c", ".cpp", ".cxx", ".hpp", ".hxx", ".h"}

# Where to search contexts definitions, relative to SOURCE_DIR (defined below).
PYGETTEXT_CONTEXTS_DEFSRC = os.path.join("source", "blender", "blenfont",
                                         "BLF_translation.h")

# Regex to extract contexts defined in BLF_translation.h
# XXX Not full-proof, but should be enough here!
PYGETTEXT_CONTEXTS = "#define\\s+(BLF_I18NCONTEXT_[A-Z_0-9]+)\\s+\"([^\"]*)\""

# Keywords' regex.
# XXX Most unfortunately, we can't use named backreferences inside character sets,
#     which makes the regexes even more twisty... :/
_str_base = (
    # Match void string
    "(?P<{_}1>[\"'])(?P={_}1)"  # Get opening quote (' or "), and closing immediately.
    "|"
    # Or match non-void string
    "(?P<{_}2>[\"'])"  # Get opening quote (' or ").
        "(?{capt}(?:"
            # This one is for crazy things like "hi \\\\\" folks!"...
            r"(?:(?!<\\)(?:\\\\)*\\(?=(?P={_}2)))|"
            # The most common case.
            ".(?!(?P={_}2))"
        ")+.)"  # Don't forget the last char!
    "(?P={_}2)"  # And closing quote.
)
str_clean_re = _str_base.format(_="g", capt="P<clean>")
# Here we have to consider two different cases (empty string and other).
_str_whole_re = (
    _str_base.format(_="{_}1_", capt=":") +
    # Optional loop start, this handles "split" strings...
    "(?:(?<=[\"'])\\s*(?=[\"'])(?:"
        + _str_base.format(_="{_}2_", capt=":") +
    # End of loop.
    "))*"
)
_ctxt_re = r"(?P<ctxt_raw>(?:" + _str_whole_re.format(_="_ctxt") + r")|(?:[A-Z_0-9]+))"
_msg_re = r"(?P<msg_raw>" + _str_whole_re.format(_="_msg") + r")"
PYGETTEXT_KEYWORDS = (() +
    tuple((r"{}\(\s*" + _msg_re + r"\s*\)").format(it)
          for it in ("IFACE_", "TIP_", "N_")) +

    tuple((r"{}\(\s*" + _ctxt_re + r"\s*,\s*" + _msg_re + r"\s*\)").format(it)
          for it in ("CTX_IFACE_", "CTX_TIP_", "CTX_N_")) + 

    tuple(("{}\\((?:[^\"',]+,){{1,2}}\\s*" + _msg_re + r"\s*(?:\)|,)").format(it)
          for it in ("BKE_report", "BKE_reportf", "BKE_reports_prepend", "BKE_reports_prependf")) +

    tuple(("{}\\((?:[^\"',]+,){{3}}\\s*" + _msg_re + r"\s*,").format(it)
          for it in ("BMO_error_raise",)) +

    tuple(("{}\\((?:[^\"',]+,)\\s*" + _msg_re + r"\s*(?:\)|,)").format(it)
          for it in ("modifier_setError",))
)

ESCAPE_RE = (
    (r'((?<!\\)"|(?<!\\)\\(?!\\|"))', r"\\\1"),
    ('\t', r"\\t"),
)

# Should po parser warn when finding a first letter not capitalized?
WARN_MSGID_NOT_CAPITALIZED = True

# Strings that should not raise above warning!
WARN_MSGID_NOT_CAPITALIZED_ALLOWED = {
    "",  # Simplifies things... :p
    "sin(x) / x",
    "fBM",
    "sqrt(x*x+y*y+z*z)",
    "iTaSC",
    "bItasc",
    "px",
    "mm",
    "fStop",
    "sRGB",
    "iso-8859-15",
    "utf-8",
    "ascii",
    "re",
    "y",
    "ac3",
    "flac",
    "mkv",
    "mp2",
    "mp3",
    "ogg",
    "wav",
    "iTaSC parameters",
    "vBVH",
    "rv",
    "et_EE",
    "eo",
    "available with",                # Is part of multi-line msg.
    "virtual parents",               # Is part of multi-line msg.
    "description",                   # Addons' field. :/
    "location",                      # Addons' field. :/
    "author",                        # Addons' field. :/
    "in memory to enable editing!",  # Is part of multi-line msg.
    "iScale",
    "dx",
    "p0",
    "res",
}
WARN_MSGID_NOT_CAPITALIZED_ALLOWED |= set(lng[2] for lng in LANGUAGES)


###############################################################################
# PATHS
###############################################################################

# The tools path, should be OK.
TOOLS_DIR = os.path.join(os.path.dirname(__file__))

# The Python3 executable.You’ll likely have to edit it in your user_settings.py
# if you’re under Windows.
PYTHON3_EXEC = "python3"

# The Blender executable!
# This is just an example, you’ll most likely have to edit it in your user_settings.py!
BLENDER_EXEC = os.path.abspath(os.path.join(TOOLS_DIR, "..", "..", "..", "..", "blender"))

# The xgettext tool. You’ll likely have to edit it in your user_settings.py if you’re under Windows.
GETTEXT_XGETTEXT_EXECUTABLE = "xgettext"

# The gettext msgmerge tool. You’ll likely have to edit it in your user_settings.py if you’re under Windows.
GETTEXT_MSGMERGE_EXECUTABLE = "msgmerge"

# The gettext msgfmt "compiler". You’ll likely have to edit it in your user_settings.py if you’re under Windows.
GETTEXT_MSGFMT_EXECUTABLE = "msgfmt"

# The svn binary... You’ll likely have to edit it in your user_settings.py if you’re under Windows.
SVN_EXECUTABLE = "svn"

# The FriBidi C compiled library (.so under Linux, .dll under windows...).
# You’ll likely have to edit it in your user_settings.py if you’re under Windows., e.g. using the included one:
#     FRIBIDI_LIB = os.path.join(TOOLS_DIR, "libfribidi.dll")
FRIBIDI_LIB = "libfribidi.so.0"

# The name of the (currently empty) file that must be present in a po's directory to enable rtl-preprocess.
RTL_PREPROCESS_FILE = "is_rtl"

# The Blender source root path.
# This is just an example, you’ll most likely have to override it in your user_settings.py!
SOURCE_DIR = os.path.abspath(os.path.join(TOOLS_DIR, "..", "..", "..", "..", "..", "..", "blender_msgs"))

# The bf-translation repository (you'll likely have to override this in your user_settings.py).
I18N_DIR = os.path.abspath(os.path.join(TOOLS_DIR, "..", "..", "..", "..", "..", "..", "i18n"))

# The /branches path (overriden in bf-translation's i18n_override_settings.py).
BRANCHES_DIR = os.path.join(I18N_DIR, "branches")

# The /trunk path (overriden in bf-translation's i18n_override_settings.py).
TRUNK_DIR = os.path.join(I18N_DIR, "trunk")

# The /trunk/po path (overriden in bf-translation's i18n_override_settings.py).
TRUNK_PO_DIR = os.path.join(TRUNK_DIR, "po")

# The /trunk/mo path (overriden in bf-translation's i18n_override_settings.py).
TRUNK_MO_DIR = os.path.join(TRUNK_DIR, "locale")

# The file storing Blender-generated messages.
FILE_NAME_MESSAGES = os.path.join(TRUNK_PO_DIR, "messages.txt")

# The Blender source path to check for i18n macros.
POTFILES_SOURCE_DIR = os.path.join(SOURCE_DIR, "source")

# The "source" file storing which files should be processed by xgettext, used to create FILE_NAME_POTFILES
FILE_NAME_SRC_POTFILES = os.path.join(TRUNK_PO_DIR, "_POTFILES.in")

# The final (generated) file storing which files should be processed by xgettext.
FILE_NAME_POTFILES = os.path.join(TRUNK_PO_DIR, "POTFILES.in")

# The template messages file.
FILE_NAME_POT = os.path.join(TRUNK_PO_DIR, ".".join((DOMAIN, "pot")))

# Other py files that should be searched for ui strings, relative to SOURCE_DIR.
# Needed for Cycles, currently...
CUSTOM_PY_UI_FILES = [os.path.join("intern", "cycles", "blender", "addon", "ui.py"),]


# A cache storing validated msgids, to avoid re-spellchecking them.
SPELL_CACHE = os.path.join("/tmp", ".spell_cache")


# Custom override settings must be one dir above i18n tools itself!
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from bl_i18n_override_settings import *
except ImportError:  # If no i18n_override_settings available, it’s no error!
    pass

# Override with custom user settings, if available.
try:
    from user_settings import *
except ImportError:  # If no user_settings available, it’s no error!
    pass
