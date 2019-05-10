#! /usr/bin/env python
# encoding: utf-8

import os

APPNAME = 'pybind11'
VERSION = '2.0.0'


def options(opt):

    if opt.is_toplevel():

        opt.load('python')

        opt.add_option(
            "--test_filter",
            default=None,
            action="store",
            help="Run all tests that include the substring specified."
            "Wildcards not allowed. (Used with --run_tests)",
        )

        opt.add_option(
            "--pytest_basetemp",
            default="pytest_temp",
            help="Set the basetemp folder where pytest executes the tests",
        )


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

    # Add some cxxflags to suppress some compiler-specific warnings
    cxxflags = []
    CXX = conf.env.get_flat("CXX")
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
    venv.run('python -m pip install pytest')

    # We override the pytest temp folder with the basetemp option,
    # so the test folders will be available at the specified location
    # on all platforms.
    basetemp = os.path.abspath(os.path.expanduser(
        bld.options.pytest_basetemp))

    # We need to manually remove the previously created basetemp folder,
    # because pytest uses os.listdir in the removal process, and that fails
    # if there are any broken symlinks in that folder.
    if os.path.exists(basetemp):
        waflib.extras.wurf.directory.remove_directory(path=basetemp)

    testdir = bld.dependency_node("pybind11-source").find_node('tests')

    # Use -B to avoid writing any .pyc files
    command = 'python -B -m pytest {} --basetemp {}'.format(
        testdir.abspath(), basetemp)

    # Adds the test filter if specified
    if bld.options.test_filter:
        command += ' -k "{}"'.format(bld.options.test_filter)

    venv.run(command)

#    python = bld.env['PYTHON'][0]
#    env = dict(os.environ)
#    env['PYTHONPATH'] = os.path.join(bld.out_dir, 'test')

    # Run some unit tests in the 'tests' folder
#    tests = os.path.join(bld.dependency_path('pybind11-source'), 'tests')
#    if os.path.exists(tests):
        #for f in sorted(os.listdir('tests')):
#        for f in ['test_class.py']:
#            if f.endswith('.py'):
#                test = os.path.join(tests, f)
#                bld.cmd_and_log('{0} {1}\n'.format(python, test), env=env)


