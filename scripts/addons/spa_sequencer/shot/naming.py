# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from enum import Enum
import re
import string
from typing import NamedTuple, Optional, Union

import bpy

from spa_sequencer.utils import register_classes, unregister_classes


class ShotPrefix(Enum):
    """Internal presets for shot prefixes."""

    PREVIZ = "PSH"
    SHOT = "SH"


class ShotNameData(NamedTuple):
    """Simple data structure to hold shot name components."""

    prefix: str
    number: int
    take: str


class ShotNaming:
    """
    ShotNaming centralizes the logic for shot naming convention.
    """

    # Shot prefixes.
    prefixes: list[str] = [item.value for item in ShotPrefix]
    # Shot number digits count
    number_digits: int = 4
    # Shot default number
    number_default: int = 10
    # Shot number default increment
    number_spacing: int = 10
    # Shot takes count
    takes_count: int = 6  # [0-26]
    # Shot name components separator
    separator: str = ""

    # Shot "no-take" value
    _take_none: str = ""

    @property
    def prefix_default(self):
        """Get default prefix (first item in prefixes)."""
        return self.prefixes[0] if self.prefixes else ""

    @property
    def number_max(self):
        """Get maximal shot number."""
        return 10**self.number_digits - 1

    @property
    def take_values(self) -> list[str]:
        """Get the list of acceptable take values."""
        return [self._take_none] + list(string.ascii_uppercase[: self.takes_count])

    def validate(self):
        """Ensure the current configuration is valid, raise Value error if not."""
        if self.takes_count < 0 or self.takes_count > 26:
            raise ValueError("Invalid take_count value")
        if self.number_digits < 1:
            raise ValueError("Invalid number_digits value")
        if self.number_default < 0 or self.number_default > self.number_max:
            raise ValueError("Invalid number_default value")
        if self.number_spacing < 1:
            raise ValueError("Invalid number_spacing value")

    @property
    def take_regex_str(self):
        """Regex pattern for take values."""
        return f"[A-{self.take_values[-1]}]?" if self.takes_count > 0 else ""

    @property
    def prefix_regex_str(self):
        """Regex pattern for prefix values."""
        return "|".join((item for item in self.prefixes))

    @property
    def number_regex_str(self):
        """Regex pattern for number values."""
        return rf"\d{{{self.number_digits}}}"

    @staticmethod
    def validate_value(pattern: str, value: str):
        """Ensure `value` matches `pattern`, raise ValueError otherwise."""
        if not re.fullmatch(pattern, value):
            raise ValueError("Value does not match pattern")

    def shot_regex(self):
        """Returns the regex defining the shot naming convention."""

        # Escape string attributes
        sep = re.escape(self.separator)

        return (
            rf"^"
            rf"(?P<prefix>{self.prefix_regex_str})({sep})"
            rf"(?P<number>{self.number_regex_str})({sep})?"
            rf"(?P<take>{self.take_regex_str})"
            rf"$"
        )

    def build_shot_name(
        self, number: int, prefix: Optional[str] = None, take: Optional[str] = None
    ) -> str:
        """Build a shot name using given shot name data values.

        :param number: The shot number.
        :param prefix: The shot prefix, default prefix is used if None.
        :param take: The shot take, default take used if None.
        :return: The shot name.
        """
        if prefix:
            self.validate_value(self.prefix_regex_str, prefix)
        if take:
            self.validate_value(self.take_regex_str, take)

        return (
            f"{prefix or self.prefix_default}{self.separator}"
            f"{number:0{self.number_digits}}{self.separator if take else ''}"
            f"{take or self._take_none}"
        )

    def default_shot_name(self):
        """Get the default shot name based on current configuration."""
        return self.build_shot_name(self.number_default, self.prefix_default)

    def match_name(self, name: str) -> Union[re.Match, None]:
        """Match `name` to internal shot naming regexp.

        :param name: The name to consider.
        :return: The Match object on success, None otherwise.
        """
        return re.fullmatch(self.shot_regex(), name)

    def shot_data_from_name(self, name: str, strict: bool = True) -> ShotNameData:
        """Extract shot name data components from `name`.

        :param name: The name to extract data from.
        :param strict: Whether the name matching should be strict.
        :return: The extracted shot name data.
        """
        prefix = self.prefix_default
        number = self.number_default
        take = self._take_none

        # Try full match with regex
        match = self.match_name(name)
        if match:
            prefix = match.group("prefix")
            number = int(match.group("number"))
            take = match.group("take")
        # If not strict, try to find at least a number to initialize from
        elif not strict:
            match = re.search(r"\d+", name)
            if match and int(match.group()) < self.number_max:
                number = int(match.group())
        # Throw otherwise
        else:
            raise ValueError("Invalid shot name")
        return ShotNameData(prefix, number, take)

    def get_next_number(self, number: int) -> int:
        """Get next shot number snapped to spacing.

        :param number: The shot number to start from.
        :return: The next shot number snapped to spacing.
        """
        # Add spacing.
        number += self.number_spacing
        # Snap to previous spacing value.
        return number - (number % self.number_spacing)

    def next_shot_name_from_name(
        self, shot_name: str, custom_increment: Optional[int] = None
    ) -> str:
        """Get the next shot name from `shot_name`."""
        shot_data = self.shot_data_from_name(shot_name)
        number = self.shot_data_from_name(shot_name).number
        if custom_increment:
            number += custom_increment
        else:
            number = self.get_next_number(number)
        if number > self.number_max:
            raise ValueError(f"Cannot have more than {self.number_max} shots")
        return self.build_shot_name(number, shot_data.prefix, shot_data.take)

    def get_all_shot_scenes(self) -> list[bpy.types.Scene]:
        """Get all scenes in the current file matching the shot naming convention.

        :return: The list of scenes.
        """
        return [s for s in bpy.data.scenes if self.match_name(s.name)]

    def next_shot_name_from_scenes(self, custom_increment: Optional[int] = None) -> str:
        """
        Get the next available shot name (incremented number) based on existing scenes.

        :return: The next available shot name.
        """
        shots = sorted([s.name for s in self.get_all_shot_scenes()])
        if not shots:
            return self.default_shot_name()
        return self.next_shot_name_from_name(shots[-1], custom_increment)

    def get_all_shot_strips(
        self, sed: bpy.types.SequenceEditor
    ) -> list[bpy.types.SceneSequence]:
        """
        Get all scene strips in the given sequence editor matching the shot naming
        convention.

        :param sed: The sequence editor.
        :return: The list of Scene strips.
        """
        return [
            s
            for s in sed.sequences
            if isinstance(s, bpy.types.SceneSequence) and self.match_name(s.name)
        ]

    def next_shot_name_from_sequences(
        self, sed: bpy.types.SequenceEditor, custom_increment: Optional[int] = None
    ) -> str:
        """Get next shot name from the sequences contained in the given sequence editor.

        :param sed: The sequence editor.
        :param custom_increment: Optional custom increment.
        :return: The next shot name.
        """
        shots = sorted([s.name for s in self.get_all_shot_strips(sed)])
        if not shots:
            return self.default_shot_name()
        return self.next_shot_name_from_name(shots[-1], custom_increment)

    def next_take_name(self, shot_name: str) -> str:
        """
        Get the next available take name (incremented take) for `shot_name` based on
        existing scenes.

        :param shot_name: The name of the shot.
        :return: The next available take name.
        """
        if not self.takes_count:
            raise RuntimeError("Shot takes are not supported")

        take_values = self.take_values
        shot_data = self.shot_data_from_name(shot_name)
        new_take = take_values.index(shot_data.take) + 1
        if new_take >= len(take_values):
            raise ValueError(f"Cannot have more than {self.takes_count} takes")
        return self.build_shot_name(
            number=shot_data.number,
            prefix=shot_data.prefix,
            take=take_values[new_take],
        )


# Global ShotNaming instance
shot_naming = ShotNaming()


class ShotNamingProperty(bpy.types.PropertyGroup):
    def get_prefix_enum(self, ctx):
        return [(item.value, item.value, item.name) for item in ShotPrefix]

    prefix: bpy.props.EnumProperty(
        name="Prefix",
        description="Shot Prefix",
        items=get_prefix_enum,
        default=0,
        options={"SKIP_SAVE"},
    )

    number: bpy.props.IntProperty(
        name="Number",
        description="Shot Number",
        default=shot_naming.number_default,
        min=shot_naming.number_default,
        max=shot_naming.number_max,
        options={"SKIP_SAVE"},
    )

    # Adapter enum value for default empty take (enum values cannot be empty strings)
    default_take_enum_value: str = "-"

    @classmethod
    def take_to_enum(cls, take):
        """Convert take name to enum value."""
        return take or cls.default_take_enum_value

    @classmethod
    def enum_to_take(cls, enum_value):
        """Convert enum value to take name."""
        return enum_value if enum_value != cls.default_take_enum_value else ""

    def get_takes(self, ctx):
        """Build the enum take values from shot_naming."""
        return (
            (self.take_to_enum(c), self.take_to_enum(c), c or "Default Take")
            for c in shot_naming.take_values
        )

    take: bpy.props.EnumProperty(
        name="Take",
        description="Shot Take",
        items=get_takes,
        default=0,
        options={"SKIP_SAVE"},
    )

    def set_use_next_shot_name(self, val):
        """Update naming to use next available shot name."""
        sed = bpy.context.scene.sequence_editor
        self.init_from_name(shot_naming.next_shot_name_from_sequences(sed))

    # Helper "function-property" with a set method that makes naming use next shot name
    use_next_shot_name: bpy.props.BoolProperty(
        name="Use Next Available Shot Name",
        description="Update naming to use the next available shot name",
        set=set_use_next_shot_name,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def init_from_name(self, name: str):
        """Initialize properties from `name`."""
        shot_data = shot_naming.shot_data_from_name(name, strict=False)
        self.prefix = shot_data.prefix
        self.number = shot_data.number
        self.take = self.take_to_enum(shot_data.take)

    def to_string(self) -> str:
        """Return the shot name based on current properties values."""
        return shot_naming.build_shot_name(
            self.number, self.prefix, self.enum_to_take(self.take)
        )

    def draw(
        self,
        layout: bpy.types.UILayout,
        text: str = "Shot Name",
        show_init_from_next: bool = False,
    ):
        """Helper function to draw this PropertyGroup."""
        main_row = layout.row(align=True)
        main_row.label(text=text)
        row = main_row.row(align=True)
        row.use_property_split = False
        # Disable prefix field by default
        prefix = row.row(align=True)
        prefix.prop(self, "prefix", text="")

        row.prop(self, "number", text="")
        if shot_naming.takes_count > 0:
            row.prop(self, "take", text="")

        if show_init_from_next:
            main_row.prop(self, "use_next_shot_name", icon="FRAME_NEXT", icon_only=True)


classes = (ShotNamingProperty,)


def register():
    shot_naming.validate()
    register_classes(classes)


def unregister():
    unregister_classes(classes)
