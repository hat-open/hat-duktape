from pathlib import Path

from hat.doit import common
from hat.doit.c import (target_lib_suffix,
                        CBuild)


__all__ = ['task_duktape',
           'task_duktape_obj',
           'task_duktape_dep',
           'task_duktape_cleanup']


build_dir = Path('build')
src_c_dir = Path('src_c')
src_py_dir = Path('src_py')

duktape_path = src_py_dir / f'hat/duktape/duktape{target_lib_suffix}'

build = CBuild(src_paths=[*(src_c_dir / 'duktape').rglob('*.c')],
               build_dir=(build_dir / 'duktape' /
                          f'{common.target_platform.name.lower()}'),
               c_flags=['-fPIC', '-O2'],
               task_dep=['duktape_cleanup'])


def task_duktape():
    """Build duktape"""
    yield build.get_task_lib(duktape_path)


def task_duktape_obj():
    """Build duktape .o files"""
    yield from build.get_task_objs()


def task_duktape_dep():
    """Build duktape .d files"""
    yield from build.get_task_deps()


def task_duktape_cleanup():
    """Cleanup duktape"""

    def cleanup():
        for path in duktape_path.parent.glob('duktape.*'):
            if path == duktape_path:
                continue
            common.rm_rf(path)

    return {'actions': [cleanup]}
