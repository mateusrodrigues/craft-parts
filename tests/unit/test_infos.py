# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from craft_parts import errors
from craft_parts.dirs import ProjectDirs
from craft_parts.infos import PartInfo, ProjectInfo, StepInfo
from craft_parts.parts import Part
from craft_parts.steps import Step

_MOCK_NATIVE_ARCH = "aarch64"


@pytest.mark.parametrize(
    "tc_arch,tc_target_arch,tc_triplet,tc_cross",
    [
        ("aarch64", "arm64", "aarch64-linux-gnu", False),
        ("armv7l", "armhf", "arm-linux-gnueabihf", True),
        ("i686", "i386", "i386-linux-gnu", True),
        ("ppc", "powerpc", "powerpc-linux-gnu", True),
        ("ppc64le", "ppc64el", "powerpc64le-linux-gnu", True),
        ("riscv64", "riscv64", "riscv64-linux-gnu", True),
        ("s390x", "s390x", "s390x-linux-gnu", True),
        ("x86_64", "amd64", "x86_64-linux-gnu", True),
    ],
)
def test_project_info(mocker, new_dir, tc_arch, tc_target_arch, tc_triplet, tc_cross):
    mocker.patch("platform.machine", return_value=_MOCK_NATIVE_ARCH)

    x = ProjectInfo(
        application_name="test",
        arch=tc_arch,
        parallel_build_count=16,
        custom1="foobar",
        custom2=[1, 2],
    )

    assert x.application_name == "test"
    assert x.arch_triplet == tc_triplet
    assert x.is_cross_compiling == tc_cross
    assert x.parallel_build_count == 16
    assert x.target_arch == tc_target_arch
    assert x.project_options == {
        "application_name": "test",
        "arch_triplet": tc_triplet,
        "target_arch": tc_target_arch,
    }

    assert x.parts_dir == new_dir / "parts"
    assert x.stage_dir == new_dir / "stage"
    assert x.prime_dir == new_dir / "prime"


def test_project_info_work_dir(new_dir):
    info = ProjectInfo(project_dirs=ProjectDirs(work_dir="work_dir"))

    assert info.parts_dir == new_dir / "work_dir/parts"
    assert info.stage_dir == new_dir / "work_dir/stage"
    assert info.prime_dir == new_dir / "work_dir/prime"


def test_project_info_custom_args():
    info = ProjectInfo(custom1="foobar", custom2=[1, 2])

    assert info.custom_args == ["custom1", "custom2"]
    assert info.custom1 == "foobar"
    assert info.custom2 == [1, 2]


def test_project_info_invalid_custom_args():
    info = ProjectInfo()

    with pytest.raises(AttributeError) as raised:
        print(info.custom1)
    assert str(raised.value) == "'ProjectInfo' has no attribute 'custom1'"


def test_project_info_set_custom_args():
    info = ProjectInfo(custom="foo")

    info.set_custom_argument("custom", "bar")
    assert info.custom == "bar"


def test_project_info_set_invalid_custom_args():
    info = ProjectInfo()

    with pytest.raises(ValueError) as raised:
        info.set_custom_argument("custom", "bar")
    assert str(raised.value) == "'custom' not in project custom arguments"


def test_project_info_default():
    x = ProjectInfo()

    assert x.application_name == "craft_parts"
    assert x.parallel_build_count == 1


def test_invalid_arch():
    with pytest.raises(errors.InvalidArchitecture) as raised:
        ProjectInfo(arch="invalid")
    assert raised.value.arch_name == "invalid"


def test_part_info(new_dir):
    info = ProjectInfo(custom1="foobar", custom2=[1, 2])
    part = Part("foo", {})
    x = PartInfo(project_info=info, part=part)

    assert x.application_name == "craft_parts"
    assert x.parallel_build_count == 1

    assert x.part_name == "foo"
    assert x.part_src_dir == new_dir / "parts/foo/src"
    assert x.part_src_subdir == new_dir / "parts/foo/src"
    assert x.part_build_dir == new_dir / "parts/foo/build"
    assert x.part_build_subdir == new_dir / "parts/foo/build"
    assert x.part_install_dir == new_dir / "parts/foo/install"
    assert x.part_state_dir == new_dir / "parts/foo/state"
    assert x.stage_dir == new_dir / "stage"
    assert x.prime_dir == new_dir / "prime"

    assert x.custom_args == ["custom1", "custom2"]
    assert x.custom1 == "foobar"
    assert x.custom2 == [1, 2]


def test_part_info_invalid_custom_args():
    info = ProjectInfo()
    part = Part("foo", {})
    x = PartInfo(project_info=info, part=part)

    with pytest.raises(AttributeError) as raised:
        print(x.custom1)
    assert str(raised.value) == "'PartInfo' has no attribute 'custom1'"


def test_part_info_set_custom_args():
    info = ProjectInfo(custom="foo")
    part = Part("p1", {})
    x = PartInfo(project_info=info, part=part)

    x.set_custom_argument("custom", "bar")
    assert x.custom == "bar"


def test_part_info_set_invalid_custom_args():
    info = ProjectInfo()
    part = Part("p1", {})
    x = PartInfo(project_info=info, part=part)

    with pytest.raises(ValueError) as raised:
        x.set_custom_argument("custom", "bar")
    assert str(raised.value) == "'custom' not in project custom arguments"


def test_step_info(new_dir):
    info = ProjectInfo(custom1="foobar", custom2=[1, 2])
    part = Part("foo", {})
    part_info = PartInfo(project_info=info, part=part)
    x = StepInfo(part_info=part_info, step=Step.BUILD)

    assert x.application_name == "craft_parts"
    assert x.parallel_build_count == 1

    assert x.part_name == "foo"
    assert x.part_src_dir == new_dir / "parts/foo/src"
    assert x.part_src_subdir == new_dir / "parts/foo/src"
    assert x.part_build_dir == new_dir / "parts/foo/build"
    assert x.part_build_subdir == new_dir / "parts/foo/build"
    assert x.part_install_dir == new_dir / "parts/foo/install"
    assert x.stage_dir == new_dir / "stage"
    assert x.prime_dir == new_dir / "prime"

    assert x.step == Step.BUILD

    assert x.custom_args == ["custom1", "custom2"]
    assert x.custom1 == "foobar"
    assert x.custom2 == [1, 2]


def test_step_info_invalid_custom_args():
    info = ProjectInfo()
    part = Part("foo", {})
    part_info = PartInfo(project_info=info, part=part)
    x = StepInfo(part_info=part_info, step=Step.PULL)

    with pytest.raises(AttributeError) as raised:
        print(x.custom1)
    assert str(raised.value) == "'StepInfo' has no attribute 'custom1'"


def test_step_info_set_custom_args():
    info = ProjectInfo(custom="foo")
    part = Part("p1", {})
    part_info = PartInfo(project_info=info, part=part)
    x = StepInfo(part_info=part_info, step=Step.PULL)

    x.set_custom_argument("custom", "bar")
    assert x.custom == "bar"


def test_step_info_set_invalid_custom_args():
    info = ProjectInfo()
    part = Part("p1", {})
    part_info = PartInfo(project_info=info, part=part)
    x = StepInfo(part_info=part_info, step=Step.PULL)

    with pytest.raises(ValueError) as raised:
        x.set_custom_argument("custom", "bar")
    assert str(raised.value) == "'custom' not in project custom arguments"
