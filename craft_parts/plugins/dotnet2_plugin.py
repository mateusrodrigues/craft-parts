# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021,2024 Canonical Ltd.
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

"""The .NET plugin."""

import logging
from typing import Literal, cast

from overrides import override

from . import validator
from .base import Plugin
from .properties import PluginProperties

logger = logging.getLogger(__name__)


class Dotnet2PluginProperties(PluginProperties, frozen=True):
    """The part properties used by the .NET plugin."""

    plugin: Literal["dotnet2"] = "dotnet2"

    dotnet_configuration: str = "Release"
    dotnet_project: str | None = None
    dotnet_self_contained: bool = False
    dotnet_verbosity: str = "normal"
    dotnet_version: str = "8.0"

    # part properties required by the plugin
    source: str  # pyright: ignore[reportGeneralTypeIssues]


class Dotnet2PluginEnvironmentValidator(validator.PluginEnvironmentValidator):
    """Check the execution environment for the .NET plugin.

    :param part_name: The part whose build environment is being validated.
    :param env: A string containing the build step environment setup.
    """

    @override
    def validate_environment(
        self, *, part_dependencies: list[str] | None = None
    ) -> None:
        """Ensure the environment contains dependencies needed by the plugin.

        :param part_dependencies: A list of the parts this part depends on.
        """
        self.validate_dependency(
            dependency="dotnet",
            plugin_name="dotnet",
            part_dependencies=part_dependencies,
        )


class Dotnet2Plugin(Plugin):
    """A plugin for .NET projects.

    The .NET plugin requires .NET installed on your system. This can
    be achieved by adding the appropriate .NET snap package to ``build-snaps``,
    or to have it installed or built in a different part. In this case, the
    name of the part supplying the .NET compiler must be ".NET".

    The .NET plugin uses the common plugin keywords as well as those for "sources".
    Additionally, the following plugin-specific keywords can be used:

    - ``.NET-build-configuration``
      (string)
      The .NET build configuration to use. The default is "Release".

    - ``.NET-self-contained-runtime-identifier``
      (string)
      Create a self contained .NET application using the specified RuntimeIdentifier.
    """

    properties_class = Dotnet2PluginProperties
    validator_class = Dotnet2PluginEnvironmentValidator

    @override
    def get_build_snaps(self) -> set[str]:
        """Return a set of required snaps to install in the build environment."""
        options = cast(Dotnet2PluginProperties, self._options)

        build_snaps = set()
        build_snaps.add(f"dotnet-sdk-{options.dotnet_version.replace('.', '')}")

        return build_snaps

    @override
    def get_build_packages(self) -> set[str]:
        """Return a set of required packages to install in the build environment."""
        return set()

    @override
    def get_build_environment(self) -> dict[str, str]:
        """Return a dictionary with the environment to use in the build step."""
        return {}

    @override
    def get_build_commands(self) -> list[str]:
        """Return a list of commands to run during the build step."""
        options = cast(Dotnet2PluginProperties, self._options)

        snap_location = f"/snap/dotnet-sdk-{options.dotnet_version.replace('.', '')}/current"
        dotnet_exe = f"{snap_location}/usr/lib/dotnet/dotnet"

        build_cmd = f"{dotnet_exe} build -c {options.dotnet_build_configuration}"
        publish_cmd = (
            "{dotnet_exe} publish "
            f"-c {options.dotnet_build_configuration} "
            f"-o {self._part_info.part_install_dir}"
        )
        if options.dotnet_self_contained_runtime_identifier:
            publish_cmd += (
                " --self-contained "
                f"-r {options.dotnet_self_contained_runtime_identifier}"
            )

        return [build_cmd, publish_cmd]
