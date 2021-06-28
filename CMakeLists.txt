cmake_minimum_required(VERSION 3.12)
project(hello_world)

# Use waf to resolve dependencies
if(NOT DEFINED STEINWURF_RESOLVE)
  message(STATUS "Resolving dependencies...")
  execute_process(COMMAND python waf resolve
                  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
  set(STEINWURF_RESOLVE "${CMAKE_CURRENT_SOURCE_DIR}/resolve_symlinks")
  set(STEINWURF_TOP_NAME hello_world)
endif()

# Use position independent code in this library and all dependencies
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# pybind11 dependency
add_subdirectory("${STEINWURF_RESOLVE}/pybind11-source")

# Define library
file(GLOB_RECURSE hello_world_source ./example/hello_world.cpp)
pybind11_add_module(hello_world ${hello_world_source})
