from pathlib import Path

from hat.doit.c import (local_platform,
                        get_lib_suffix,
                        Platform,
                        CBuild)


__all__ = ['task_duktape',
           'task_duktape_obj',
           'task_duktape_dep']


build_dir = Path('build')
src_c_dir = Path('src_c')
src_py_dir = Path('src_py')

platforms = [local_platform]
if local_platform == Platform.LINUX:
    platforms.append(Platform.WINDOWS)

builds = [CBuild(src_paths=[*(src_c_dir / 'duktape').rglob('*.c')],
                 build_dir=build_dir / 'duktape' / platform.name.lower(),
                 platform=platform,
                 cc_flags=['-fPIC', '-O2'])
          for platform in platforms]

duktape_paths = [src_py_dir / f'hat/duktape/duktape{get_lib_suffix(platform)}'
                 for platform in platforms]


def task_duktape():
    """Build duktape"""
    for build, duktape_path in zip(builds, duktape_paths):
        yield build.get_task_lib(duktape_path)


def task_duktape_obj():
    """Build duktape .o files"""
    for build in builds:
        yield from build.get_task_objs()


def task_duktape_dep():
    """Build duktape .d files"""
    for build in builds:
        yield from build.get_task_deps()
