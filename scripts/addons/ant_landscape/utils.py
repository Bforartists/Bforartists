# SPDX-License-Identifier: GPL-2.0-or-later

numexpr_available = False
try:
    import numexpr
    numexpr_available = True
except ImportError:
    pass
