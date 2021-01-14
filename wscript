#! /usr/bin/env python
# encoding: utf-8

import os
from waflib.extras.wurf.directory import remove_directory

APPNAME = 'pybind11'
VERSION = '1.0.0'


def options(opt):

    if opt.is_toplevel():

        opt.load('python')

        opt.add_option(
            "--test_filter",
            default=None,
            action="store",
            help="Run all tests that include the substring specified."
            "Wildcards not allowed. (Used with --run_tests)")


def configure(conf):

    # Configure Python extension flags if necessary
    # (boost-python might have already completed the Python configuration)
    if 'BUILD_PYTHON' not in conf.env:
        try:
            conf.load('python')
            conf.check_python_headers()
            conf.env['BUILD_PYTHON'] = True
        except:
            conf.env['BUILD_PYTHON'] = False

    # If the Python configuration failed, then we cannot continue
    if not conf.env['BUILD_PYTHON']:
        conf.fatal('Python was not configured properly')

    CXX = conf.env.get_flat("CXX")

    # Override python-config's compiler flags, because these are not
    # compatible with the common C++ flags defined in our waf-tools
    conf.env['DEFINES_PYEXT'] = []
    conf.env['CFLAGS_PYEXT'] = []
    conf.env['CXXFLAGS_PYEXT'] = []

    # Python extensions are shared libraries, so all the object files that
    # are included in the library must be compiled using the -fPIC flag
    # (position independent code). We can only guarantee this if the flag
    # is added globally in waf for compiling all C/C++ source files.
    if 'g++' in CXX or 'clang' in CXX:
        conf.env.append_value('CFLAGS', '-fPIC')
        conf.env.append_value('CXXFLAGS', '-fPIC')

    # Add some cxxflags to suppress some compiler-specific warnings
    cxxflags = []
    # The deprecated "register" keyword is present in some Python 2.7 headers,
    # so the following flags are used to suppress these warnings (which are
    # treated as errors in C++17 mode)
    if 'g++' in CXX or 'clang' in CXX:
        cxxflags += ['-Wno-register']
    # For MSVC, disable the C5033 warning (deprecated register keyword)
    if 'CL.exe' in CXX or 'cl.exe' in CXX:
        cxxflags += ['/wd5033']
    # Pybind11 is explicitly invoking sized deallocation:
    # https://github.com/pybind/pybind11/issues/1604
    # So this flag is needed for clang in C++17 mode:
    if 'clang' in CXX:
        cxxflags += ['-fsized-deallocation']

    conf.env['CXXFLAGS_PYBIND11'] = cxxflags

    if conf.is_toplevel():

        # Remove the virtualenv folder when we (re-)configure
        venv_path = os.path.join(
            conf.path.abspath(), 'build', 'virtualenv-tests')

        if os.path.isdir(venv_path):
            remove_directory(venv_path)


def build(bld):

    bld.env.append_unique(
        'DEFINES_STEINWURF_VERSION',
        'STEINWURF_PYBIND11_VERSION="{}"'.format(
            VERSION))

    # Path to the source repo
    sources = bld.dependency_node("pybind11-source")
    includes = sources.find_dir('include')

    bld(name='pybind11_includes',
        export_includes=[includes],
        use=['PYBIND11'])

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

    build_path = os.path.join(bld.path.abspath(), 'build')
    venv = bld.create_virtualenv(
        cwd=build_path, name="virtualenv-tests", overwrite=False)

    # Install pytest in the virtualenv
    # The pybind11 tests are not compatible with this ExceptionInfo change:
    # https://github.com/pytest-dev/pytest/pull/5413
    # that was added in pytest 5.0.0, so we must use an earlier version
    venv.run('python -m pip install "pytest<5.0.0"')
    venv.run('python -m pip install "numpy"')

    testdir = bld.dependency_node("pybind11-source").find_node('tests')

    # Use -B to avoid writing any .pyc files
    command = 'python -B -m pytest {}'.format(testdir.abspath())

    # Adds the test filter if specified
    if bld.options.test_filter:
        command += ' -k "{}"'.format(bld.options.test_filter)
    else:
        # By default, disable the tests are not supported on our buildslaves
        command += ' -k "not test_iostream and not test_eigen"'

    venv.env['PYTHONPATH'] = os.path.join(bld.out_dir, 'test')
    venv.run(command)
