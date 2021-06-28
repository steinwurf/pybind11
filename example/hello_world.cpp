#include <pybind11/pybind11.h>

PYBIND11_MODULE(hello_world, m)
{
    m.def("hello", []() { return "Hello World!"; });
}
