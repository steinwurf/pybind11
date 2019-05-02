#! /usr/bin/env python
# encoding: utf-8

import os

APPNAME = 'pybind11'
VERSION = '2.0.0'


def options(opt):

    if opt.is_toplevel():
        opt.load('python')


def configure(conf):

    # If the Python extension flags are empty, then detect the Python config
    # (boost-python might have already completed the Python configuration)
    if not conf.env['BUILD_PYTHON']:
        try:
            conf.load('python')
            conf.check_python_headers()
            conf.env['BUILD_PYTHON'] = True
        except:
            conf.env['BUILD_PYTHON'] = False


def build(bld):

    # Ensure that Python was configured properly in the configure step of
    # the boost wscript
    if not bld.env['BUILD_PYTHON']:
        bld.fatal('Python was not configured properly')

    bld.env.append_unique(
        'DEFINES_STEINWURF_VERSION',
        'STEINWURF_PYBIND11_VERSION="{}"'.format(
            VERSION))

    # Path to the source repo
    sources = bld.dependency_node("pybind11-source")
    includes = sources.find_dir('include')

    bld(name='pybind11_includes',
        export_includes=[includes])

    if bld.is_toplevel():

        # The actual sources are stored outside this repo - so we manually
        # add them for the solution generator
        bld.msvs_extend_sources = [sources]

        # Only build tests when executed from the top-level wscript,
        # i.e. not when included as a dependency
        bld.recurse('test')

        if bld.has_tool_option('run_tests'):
            bld.add_post_fun(exec_test_pybind11)


def exec_test_pybind11(bld):
    python = bld.env['PYTHON'][0]
    env = dict(os.environ)
    env['PYTHONPATH'] = os.path.join(bld.out_dir, 'test')

    # Run some unit tests in the 'tests' folder
    tests = os.path.join(bld.dependency_path('pybind11-source'), 'tests')
    if os.path.exists(tests):
        #for f in sorted(os.listdir('tests')):
        for f in ['test_class.py']:
            if f.endswith('.py'):
                test = os.path.join(tests, f)
                bld.cmd_and_log('{0} {1}\n'.format(python, test), env=env)


