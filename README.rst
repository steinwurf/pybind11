========
pybind11
========

.. image:: https://travis-ci.org/steinwurf/pybind11.svg?branch=master
    :target: https://travis-ci.org/steinwurf/pybind11
    
This repository contains waf build scripts for https://github.com/pybind/pybind11
that are necessary for integration with other Steinwurf libraries.

.. contents:: Table of Contents:
   :local:

Quick Start
-----------

If you already installed a C++14 compiler, git and python on your system,
then you can clone this repository to a suitable folder::

    git clone git@github.com:steinwurf/pybind11.git

Configure and build the project::

    cd pybind11
    python waf configure
    python waf build

Run the unit tests::

    python waf --run_tests
