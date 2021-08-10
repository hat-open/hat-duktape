from pathlib import Path

from hat.doit import common
from hat.doit.py import (build_wheel,
                         run_pytest,
                         run_flake8)
from hat.doit.docs import (SphinxOutputType,
                           build_sphinx,
                           build_pdoc)

from .duktape import *  # NOQA
from . import duktape


__all__ = ['task_clean_all',
           'task_build',
           'task_check',
           'task_test',
           'task_docs',
           *duktape.__all__]


build_dir = Path('build')
src_py_dir = Path('src_py')
pytest_dir = Path('test_pytest')
docs_dir = Path('docs')

build_py_dir = build_dir / 'py'
build_docs_dir = build_dir / 'docs'


def task_clean_all():
    """Clean all"""
    return {'actions': [(common.rm_rf, [build_dir,
                                        duktape.duktape_path])]}


def task_build():
    """Build"""

    def build():
        build_wheel(
            src_dir=src_py_dir,
            dst_dir=build_py_dir,
            src_paths=list(common.path_rglob(src_py_dir,
                                             blacklist={'__pycache__'})),
            name='hat-duktape',
            description='Hat Python Duktape JS wrapper',
            url='https://github.com/hat-open/hat-duktape',
            license=common.License.APACHE2,
            packages=['hat'],
            platform_specific=True)

    return {'actions': [build],
            'task_dep': ['duktape']}


def task_check():
    """Check with flake8"""
    return {'actions': [(run_flake8, [src_py_dir]),
                        (run_flake8, [pytest_dir])]}


def task_test():
    """Test"""
    return {'actions': [lambda args: run_pytest(pytest_dir, *(args or []))],
            'pos_arg': 'args',
            'task_dep': ['duktape']}


def task_docs():
    """Docs"""
    return {'actions': [(build_sphinx, [SphinxOutputType.HTML,
                                        docs_dir,
                                        build_docs_dir]),
                        (build_pdoc, ['hat.duktape',
                                      build_docs_dir / 'py_api'])],
            'task_dep': ['duktape']}
