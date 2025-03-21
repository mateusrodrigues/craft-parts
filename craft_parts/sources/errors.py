# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2017-2024 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Source handler error definitions."""

from collections.abc import Sequence

from craft_parts import errors
from craft_parts.utils import formatting_utils


class SourceError(errors.PartsError):
    """Base class for source handler errors."""


class InvalidSourceType(SourceError):
    """Failed to determine a source type.

    :param source: The source defined for the part.
    """

    def __init__(self, source: str, *, source_type: str | None = None) -> None:
        self.source = source
        self.source_type = source_type

        if source_type:
            message = f"unknown source-type {source_type!r}."
        else:
            message = f"unable to determine source type of {source!r}."

        super().__init__(brief=f"Failed to pull source: {message}")


class InvalidSourceOption(SourceError):
    """A source option is not allowed for the given source type.

    :param source_type: The part's source type.
    :param option: The invalid source option.
    """

    def __init__(self, *, source_type: str, option: str) -> None:
        self.source_type = source_type
        self.option = option
        brief = (
            f"Failed to pull source: {option!r} cannot be used "
            f"with a {source_type} source."
        )
        resolution = "Make sure sources are correctly specified."

        super().__init__(brief=brief, resolution=resolution)


# TODO: Merge this with InvalidSourceOption above
class InvalidSourceOptions(SourceError):
    """A source option is not allowed for the given source type.

    :param source_type: The part's source type.
    :param options: The invalid source options.
    """

    def __init__(self, *, source_type: str, options: list[str]) -> None:
        self.source_type = source_type
        self.options = options
        humanized_options = formatting_utils.humanize_list(options, "and")
        brief = (
            f"Failed to pull source: {humanized_options} cannot be used "
            f"with a {source_type} source."
        )
        resolution = "Make sure sources are correctly specified."

        super().__init__(brief=brief, resolution=resolution)


class IncompatibleSourceOptions(SourceError):
    """Source specified options that cannot be used at the same time.

    :param source_type: The part's source type.
    :param options: The list of incompatible source options.
    """

    def __init__(self, source_type: str, options: list[str]) -> None:
        self.source_type = source_type
        self.options = options
        humanized_options = formatting_utils.humanize_list(options, "and")
        brief = (
            f"Failed to pull source: cannot specify both {humanized_options} "
            f"for a {source_type} source."
        )
        resolution = "Make sure sources are correctly specified."

        super().__init__(brief=brief, resolution=resolution)


class ChecksumMismatch(SourceError):
    """A checksum doesn't match the expected value.

    :param expected: The expected checksum.
    :param obtained: The actual checksum.
    """

    def __init__(self, *, expected: str, obtained: str) -> None:
        self.expected = expected
        self.obtained = obtained
        brief = f"Expected digest {expected}, obtained {obtained}."

        super().__init__(brief=brief)


class SourceUpdateUnsupported(SourceError):
    """The source handler doesn't support updating.

    :param name: The source type.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        brief = f"Failed to update source: {name!r} sources don't support updating."

        super().__init__(brief=brief)


class NetworkRequestError(SourceError):
    """A network request operation failed.

    :param message: The error message.
    :param source: URL of unreachable source.
    """

    def __init__(self, message: str, *, source: str | None = None) -> None:
        self.message = message
        self.source = source
        brief = f"Network request error: {message}."
        resolution = "Check network connection and source, and try again."
        details = f"Source: {self.source!r}" if self.source is not None else None

        super().__init__(brief=brief, details=details, resolution=resolution)


class HttpRequestError(SourceError):
    """HTTP error occurred during request processing.

    :param status_code: Request status code.
    :param reason: Text explaining status code.
    :param source: The source defined for the part.
    """

    def __init__(self, *, status_code: int, reason: str, source: str) -> None:
        self.status_code = status_code
        self.reason = reason
        self.source = source
        brief = f"Cannot process request ({reason}: {status_code}): {source}"
        resolution = "Check your URL and permissions and try again."

        super().__init__(brief=brief, resolution=resolution)


class SourceNotFound(SourceError):
    """Failed to retrieve a source.

    :param source: The source defined for the part.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        brief = f"Failed to pull source: {source!r} not found."
        resolution = "Make sure the source path is correct and accessible."

        super().__init__(brief=brief, resolution=resolution)


class InvalidSnapPackage(SourceError):
    """A snap package is invalid.

    :param snap_file: The snap file name.
    """

    def __init__(self, snap_file: str) -> None:
        self.snap_file = snap_file
        brief = f"Snap {snap_file!r} does not contain valid data."
        resolution = "Ensure the source lists a proper snap file."

        super().__init__(brief=brief, resolution=resolution)


class InvalidRpmPackage(SourceError):
    """An rpm package is invalid.

    :param rpm_file: The filename.
    """

    def __init__(self, rpm_file: str) -> None:
        self.rpm_file = rpm_file
        brief = f"RPM file {rpm_file!r} could not be extracted."
        resolution = "Ensure the source lists a valid rpm file."

        super().__init__(brief=brief, resolution=resolution)


class PullError(SourceError):
    """Failed pulling source.

    :param command: The command used to pull the source.
    :param exit_code: The command exit code.
    """

    def __init__(
        self, *, command: Sequence, exit_code: int, resolution: str | None = None
    ) -> None:
        self.command = command
        self.exit_code = exit_code
        brief = (
            f"Failed to pull source: command {command!r} exited with code {exit_code}."
        )
        resolution = resolution or "Make sure sources are correctly specified."

        super().__init__(brief=brief, resolution=resolution)


class VCSError(SourceError):
    """A version control system command failed."""

    def __init__(self, message: str, resolution: str | None = None) -> None:
        self.message = message
        brief = message

        super().__init__(brief=brief, resolution=resolution)
