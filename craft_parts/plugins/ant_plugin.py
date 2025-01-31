# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022,2024 Canonical Ltd.
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

"""The Ant plugin."""

import logging
import os
import shlex
from collections.abc import Iterator
from typing import Literal, cast
from urllib.parse import urlsplit

from overrides import override

from craft_parts import errors

from . import validator
from .java_plugin import JavaPlugin
from .properties import PluginProperties

logger = logging.getLogger(__name__)


class AntPluginProperties(PluginProperties, frozen=True):
    """The part properties used by the Ant plugin."""

    plugin: Literal["ant"] = "ant"

    ant_build_targets: list[str] = []
    ant_build_file: str | None = None
    ant_properties: dict[str, str] = {}

    source: str  # pyright: ignore[reportGeneralTypeIssues]


class AntPluginEnvironmentValidator(validator.PluginEnvironmentValidator):
    """Check the execution environment for the Ant plugin.

    :param part_name: The part whose build environment is being validated.
    :param env: A string containing the build step environment setup.
    """

    @override
    def validate_environment(
        self, *, part_dependencies: list[str] | None = None
    ) -> None:
        """Ensure the environment contains dependencies needed by the plugin.

        :param part_dependencies: A list of the parts this part depends on.

        :raises PluginEnvironmentValidationError: If ``ant`` is invalid
          and there are no parts named ant.
        """
        version = self.validate_dependency(
            dependency="ant",
            plugin_name="ant",
            part_dependencies=part_dependencies,
            argument="-version",
        )
        if not version.startswith("Apache Ant") and (
            part_dependencies is None or "ant-deps" not in part_dependencies
        ):
            raise errors.PluginEnvironmentValidationError(
                part_name=self._part_name,
                reason=f"invalid ant version {version!r}",
            )


class AntPlugin(JavaPlugin):
    """A plugin for Apache Ant projects.

    The plugin requires the ``ant`` tool installed on the system. This can
    be achieved by adding the appropriate declarations to ``build-packages``
    or ``build-snaps``, or by having it installed or built in a different
    part. In this case, the name of the part supplying ``ant`` must be
    "ant-deps".

    Additionally, Java projects need a dev kit (jdk) to build and a runtime
    environment (jre) to run. There are multiple choices here, but frequently
    adding ``default-jdk-headless`` to ``build-packages`` and
    ``default-jre-headless`` to ``stage-packages`` is enough.

    Once built, the plugin will create the following structure in the part's
    install dir (which will later be staged/primed/packaged):

    - A ``bin/java`` symlink pointing to the actual ``java`` binary provided
      by the jre;
    - A ``jar/`` directory containing the .jar files generated by the build.

    The ant plugin uses the common plugin keywords, plus the following ant-
    specific keywords:

    - ``ant-build-targets``
      (list of strings)
      The ant targets to build. These are directly passed to the ``ant``
      command line.
    - ``ant-build-file``
      (str)
      The name of the main ant build file. Defaults to ``build.xml``.
    - ``ant-properties``
      (dict of strings to strings)
      A series of key: value pairs that are passed to ant as properties
      (using the ``-D{key}={value}`` notation).
    """

    properties_class = AntPluginProperties
    validator_class = AntPluginEnvironmentValidator

    @override
    def get_build_snaps(self) -> set[str]:
        """Return a set of required snaps to install in the build environment."""
        return set()

    @override
    def get_build_packages(self) -> set[str]:
        """Return a set of required packages to install in the build environment."""
        return set()

    @override
    def get_build_environment(self) -> dict[str, str]:
        """Return a dictionary with the environment to use in the build step."""
        env = super().get_build_environment()
        # Getting ant to use a proxy requires a little work; the JRE doesn't
        # help as much as it should.  (java.net.useSystemProxies=true ought
        # to do the trick, but it relies on desktop configuration rather
        # than using the standard environment variables.)
        ant_opts: list[str] = []
        ant_opts.extend(_get_proxy_options("http"))
        ant_opts.extend(_get_proxy_options("https"))
        if ant_opts:
            env["ANT_OPTS"] = _shlex_join(ant_opts)
        return env

    @override
    def get_build_commands(self) -> list[str]:
        """Return a list of commands to run during the build step."""
        options = cast(AntPluginProperties, self._options)

        command = ["ant"]

        if options.ant_build_file:
            command.extend(["-f", options.ant_build_file])

        for prop_name, prop_value in options.ant_properties.items():
            command.append(f"-D{prop_name}={prop_value}")

        command.extend(options.ant_build_targets)

        return [" ".join(command), *self._get_java_post_build_commands()]


def _get_proxy_options(scheme: str) -> Iterator[str]:
    proxy = os.environ.get(f"{scheme}_proxy")
    if proxy:
        parsed = urlsplit(proxy)
        if parsed.hostname is not None:
            yield f"-D{scheme}.proxyHost={parsed.hostname}"
        if parsed.port is not None:
            yield f"-D{scheme}.proxyPort={parsed.port}"
        if parsed.username is not None:
            yield f"-D{scheme}.proxyUser={parsed.username}"
        if parsed.password is not None:
            yield f"-D{scheme}.proxyPassword={parsed.password}"


def _shlex_join(elements: list[str]) -> str:
    try:
        return shlex.join(elements)
    except AttributeError:
        # Python older than 3.8 does not have shlex.join
        return " ".join(elements)
