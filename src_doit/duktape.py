from pathlib import Path

from hat.doit import common


__all__ = ['task_duktape',
           'task_duktape_obj',
           'task_duktape_dep']


build_dir = Path('build')
src_c_dir = Path('src_c')
src_py_dir = Path('src_py')

duktape_path = src_py_dir / f'hat/duktape/duktape{common.lib_suffix}'


def task_duktape():
    """Build duktape"""
    return _build.get_task_lib(duktape_path)


def task_duktape_obj():
    """Build duktape .o files"""
    yield from _build.get_task_objs()


def task_duktape_dep():
    """Build duktape .d files"""
    yield from _build.get_task_deps()


_build = common.CBuild(
    src_paths=[*(src_c_dir / 'duktape').rglob('*.c')],
    src_dir=src_c_dir,
    build_dir=build_dir / 'duktape',
    cc_flags=['-fPIC', '-O2'])
