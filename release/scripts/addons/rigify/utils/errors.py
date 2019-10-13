#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

#=======================================================================
# Error handling
#=======================================================================


class MetarigError(Exception):
    """ Exception raised for errors.
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class RaiseErrorMixin(object):
    def raise_error(self, message, *args, **kwargs):
        from .naming import strip_org

        message = message.format(*args, **kwargs)

        if hasattr(self, 'base_bone'):
            message = "Bone '%s': %s" % (strip_org(self.base_bone), message)

        raise MetarigError("RIGIFY ERROR: " + message)
