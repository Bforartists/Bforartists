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

import collections

from types import FunctionType
from itertools import chain


#=============================================
# Class With Stages
#=============================================


def rigify_stage(stage):
    """Decorates the method with the specified stage."""
    def process(method):
        if not isinstance(method, FunctionType):
            raise ValueError("Stage decorator must be applied to a method definition")
        method._rigify_stage = stage
        return method
    return process


class StagedMetaclass(type):
    """
    Metaclass for rigs that manages assignment of methods to stages via @stage.* decorators.

    Using define_stages=True in the class definition will register all non-system
    method names from that definition as valid stages. After that, subclasses can
    register methods to those stages, to be called via rigify_invoke_stage.
    """
    def __new__(metacls, class_name, bases, namespace, define_stages=None, **kwds):
        # suppress keyword args to avoid issues with __init_subclass__
        return super().__new__(metacls, class_name, bases, namespace, **kwds)

    def __init__(self, class_name, bases, namespace, define_stages=None, **kwds):
        super().__init__(class_name, bases, namespace, **kwds)

        # Compute the set of stages defined by this class
        if not define_stages:
            define_stages = []

        elif define_stages is True:
            define_stages = [
                name for name, item in namespace.items()
                if name[0] != '_' and isinstance(item, FunctionType)
            ]

        self.rigify_own_stages = frozenset(define_stages)

        # Compute complete set of inherited stages
        staged_bases = [ cls for cls in reversed(self.__mro__) if isinstance(cls, StagedMetaclass) ]

        self.rigify_stages = stages = frozenset(chain.from_iterable(
            cls.rigify_own_stages for cls in staged_bases
        ))

        # Compute the inherited stage to method mapping
        stage_map = collections.defaultdict(collections.OrderedDict)
        own_stage_map = collections.defaultdict(collections.OrderedDict)
        method_map = {}

        self.rigify_own_stage_map = own_stage_map

        for base in staged_bases:
            for stage_name, methods in base.rigify_own_stage_map.items():
                for method_name, method_class in methods.items():
                    if method_name in stages:
                        raise ValueError("Stage method '%s' inherited @stage.%s in class %s (%s)" %
                                         (method_name, stage_name, class_name, self.__module__))

                    # Check consistency of inherited stage assignment to methods
                    if method_name in method_map:
                        if method_map[method_name] != stage_name:
                            print("RIGIFY CLASS %s (%s): method '%s' has inherited both @stage.%s and @stage.%s\n" %
                                  (class_name, self.__module__, method_name, method_map[method_name], stage_name))
                    else:
                        method_map[method_name] = stage_name

                    stage_map[stage_name][method_name] = method_class

        # Scan newly defined methods for stage decorations
        for method_name, item in namespace.items():
            if isinstance(item, FunctionType):
                stage = getattr(item, '_rigify_stage', None)

                if stage and method_name in stages:
                    print("RIGIFY CLASS %s (%s): cannot use stage decorator on the stage method '%s' (@stage.%s ignored)" %
                            (class_name, self.__module__, method_name, stage))
                    continue

                # Ensure that decorators aren't lost when redefining methods
                if method_name in method_map:
                    if not stage:
                        stage = method_map[method_name]
                        print("RIGIFY CLASS %s (%s): missing stage decorator on method '%s' (should be @stage.%s)" %
                              (class_name, self.__module__, method_name, stage))
                    # Check that the method is assigned to only one stage
                    elif stage != method_map[method_name]:
                        print("RIGIFY CLASS %s (%s): method '%s' has decorator @stage.%s, but inherited base has @stage.%s" %
                              (class_name, self.__module__, method_name, stage, method_map[method_name]))

                # Assign the method to the stage, verifying that it's valid
                if stage:
                    if stage not in stages:
                        raise ValueError("Invalid stage name '%s' for method '%s' in class %s (%s)" %
                                         (stage, method_name, class_name, self.__module__))
                    else:
                        stage_map[stage][method_name] = self
                        own_stage_map[stage][method_name] = self

        self.rigify_stage_map = stage_map

    def make_stage_decorators(self):
        return [(name, rigify_stage(name)) for name in self.rigify_stages]


class BaseStagedClass(object, metaclass=StagedMetaclass):
    rigify_sub_objects = tuple()
    rigify_sub_object_run_late = False

    def rigify_invoke_stage(self, stage):
        """Call all methods decorated with the given stage, followed by the callback."""
        cls = self.__class__
        assert isinstance(cls, StagedMetaclass)
        assert stage in cls.rigify_stages

        getattr(self, stage)()

        for sub in self.rigify_sub_objects:
            if not sub.rigify_sub_object_run_late:
                sub.rigify_invoke_stage(stage)

        for method_name in cls.rigify_stage_map[stage]:
            getattr(self, method_name)()

        for sub in self.rigify_sub_objects:
            if sub.rigify_sub_object_run_late:
                sub.rigify_invoke_stage(stage)


#=============================================
# Per-owner singleton class
#=============================================


class SingletonPluginMetaclass(StagedMetaclass):
    """Metaclass for maintaining one instance per owner object per constructor arg set."""
    def __call__(cls, owner, *constructor_args):
        key = (cls, *constructor_args)
        try:
            return owner.plugin_map[key]
        except KeyError:
            new_obj = super().__call__(owner, *constructor_args)
            owner.plugin_map[key] = new_obj
            owner.plugin_list.append(new_obj)
            owner.plugin_list.sort(key=lambda obj: obj.priority, reverse=True)
            return new_obj
