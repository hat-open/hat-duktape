from .duktape import *  # NOQA

from pathlib import Path

from hat.doit import common
from hat.doit.docs import (build_sphinx,
                           build_pdoc)
from hat.doit.py import (get_task_build_wheel,
                         get_task_run_pytest,
                         get_task_run_pip_compile,
                         run_flake8)

from . import duktape


__all__ = ['task_clean_all',
           'task_build',
           'task_check',
           'task_test',
           'task_docs',
           'task_pip_compile',
           *duktape.__all__]


build_dir = Path('build')
src_py_dir = Path('src_py')
pytest_dir = Path('test_pytest')
docs_dir = Path('docs')

build_py_dir = build_dir / 'py'
build_docs_dir = build_dir / 'docs'


def task_clean_all():
    """Clean all"""
    return {'actions': [(common.rm_rf, [
        build_dir,
        *(src_py_dir / 'hat/duktape').glob('duktape.*')])]}


def task_build():
    """Build"""
    return get_task_build_wheel(src_dir=src_py_dir,
                                build_dir=build_py_dir,
                                platform=common.target_platform,
                                is_purelib=False,
                                task_dep=['duktape'])


def task_check():
    """Check with flake8"""
    return {'actions': [(run_flake8, [src_py_dir]),
                        (run_flake8, [pytest_dir])]}


def task_test():
    """Test"""
    return get_task_run_pytest(task_dep=['duktape'])


def task_docs():
    """Docs"""

    def build():
        build_sphinx(src_dir=docs_dir,
                     dst_dir=build_docs_dir,
                     project='hat-duktape')
        build_pdoc(module='hat.duktape',
                   dst_dir=build_docs_dir / 'py_api',
                   exclude=['hat.duktape.duktape'])

    return {'actions': [build],
            'task_dep': ['duktape']}


def task_pip_compile():
    """Run pip-compile"""
    return get_task_run_pip_compile()
