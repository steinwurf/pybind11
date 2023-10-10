#! /usr/bin/env python
# encoding: utf-8

import os
from waflib.extras.wurf.directory import remove_directory

import importlib

APPNAME = "pybind11"
VERSION = "5.0.0"


def options(opt):
    if opt.is_toplevel():
        opt.load("python")

        opt.add_option(
            "--test_filter",
            default=None,
            action="store",
            help="Run all tests that include the substring specified."
            "Wildcards not allowed. (Used with --run_tests)",
        )


def configure(conf):
    conf.set_cxx_std(11)

    # Configure Python extension flags if necessary
    # (boost-python might have already completed the Python configuration)
    error_message = "Python was not configured properly"
    if "BUILD_PYTHON" not in conf.env:
        try:
            conf.load("python")
            conf.check_python_headers()
            conf.env["BUILD_PYTHON"] = True
        except Exception as e:
            conf.env["BUILD_PYTHON"] = False
            error_message += "\n" + str(e)

    # If the Python configuration failed, then we cannot continue
    if not conf.env["BUILD_PYTHON"]:
        conf.fatal(error_message)

    CXX = conf.env.get_flat("CXX")

    # Override python-config's compiler flags, because these are not
    # compatible with the common C++ flags defined in our waf-tools
    conf.env["DEFINES_PYEXT"] = []
    conf.env["CFLAGS_PYEXT"] = []
    conf.env["CXXFLAGS_PYEXT"] = []

    # Python extensions are shared libraries, so all the object files that
    # are included in the library must be compiled using the -fPIC flag
    # (position independent code). We can only guarantee this if the flag
    # is added globally in waf for compiling all C/C++ source files.
    if "g++" in CXX or "clang" in CXX:
        conf.env.append_value("CFLAGS", "-fPIC")
        conf.env.append_value("CXXFLAGS", "-fPIC")

    # Add some cxxflags to suppress some compiler-specific warnings
    cxxflags = []
    # The deprecated "register" keyword is present in some Python 2.7 headers,
    # so the following flags are used to suppress these warnings (which are
    # treated as errors in C++17 mode)
    if "g++" in CXX or "clang" in CXX:
        cxxflags += ["-Wno-register"]
    # For MSVC, disable the C5033 warning (deprecated register keyword)
    if "CL.exe" in CXX or "cl.exe" in CXX:
        cxxflags += ["/wd5033"]
    # Pybind11 is explicitly invoking sized deallocation:
    # https://github.com/pybind/pybind11/issues/1604
    # So this flag is needed for clang in C++17 mode:
    if "clang" in CXX:
        cxxflags += ["-fsized-deallocation"]

    conf.env["CXXFLAGS_PYBIND11"] = cxxflags


def build(bld):
    # Path to the source repo
    sources = bld.dependency_node("pybind11-source")
    includes = sources.find_dir("include")

    # Set the suffix for the built Python extensions
    bld.env["pyext_PATTERN"] = f"%s{importlib.machinery.EXTENSION_SUFFIXES[0]}"

    bld(name="pybind11_includes", export_includes=[includes], use=["PYBIND11"])

    if bld.is_toplevel():
        # The actual sources are stored outside this repo - so we manually
        # add them for the solution generator
        bld.msvs_extend_sources = [sources]

        # Only build tests when executed from the top-level wscript,
        # i.e. not when included as a dependency
        bld.recurse("test")

    if bld.is_toplevel():
        bld(
            features="cxx cxxshlib pyext",
            source=bld.path.ant_glob("example/hello_world.cpp"),
            target="hello_world",
            use=["pybind11_includes"],
        )

        if bld.has_tool_option("run_tests"):
            bld.add_post_fun(exec_test_python)


def exec_test_python(ctx):
    with ctx.create_virtualenv() as venv:
        venv.run('python -m pip install "pytest==7.3.2"')
        venv.run('python -m pip install "numpy==1.25.0"')

        testdir = ctx.dependency_node("pybind11-source").find_node("tests")

        # Use -B to avoid writing any .pyc files
        command = "python -B -m pytest {}".format(testdir.abspath())

        # Adds the test filter if specified
        if ctx.options.test_filter:
            command += ' -k "{}"'.format(ctx.options.test_filter)
        else:
            # By default, disable the tests are not supported by runners
            command += ' -k "'
            command += "not test_chrono and "
            command += "not test_iostream and "
            command += "not test_eigen and "
            command += "not test_cross_module_gil and "
            command += "not test_dtype and "
            command += "not test_recarray and "
            command += "not test_array_array and "
            command += "not test_cross_module_interleaved_error_already_set and "
            command += "not test_multi_acquire_release_cross_module and "
            command += "not test_run_in_process_direct"
            command += '"'

        venv.env["PYTHONPATH"] = os.path.join(ctx.out_dir, "test")
        venv.run(command)
