from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "memory_search",
        ["utils/memory_search.cpp"],
        include_dirs=[pybind11.get_include()],
        language='c++',
    ),
]

setup(
    name="memory_search",
    ext_modules=ext_modules,
)