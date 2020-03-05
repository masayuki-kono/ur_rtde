import os
import re
import sys
import platform
import subprocess

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion

with open("README.md", "r") as fh:
    long_description = fh.read()

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < '3.1.0':
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    @staticmethod
    def which(program, env=os.environ):
        def isExe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        fpath, fname = os.path.split(program)
        if fpath:
            if isExe(program):
                return program
        else:
            for path in env.get("PATH", "").split(os.pathsep):
                path = path.strip("\"")
                exe = os.path.join(path, program)
                if isExe(exe):
                    return exe
        return None

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())

        if self.which('ninja', env) is not None:
            cmake_args += ['-GNinja']

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)


setup(
    name="ur_rtde",
    version="0.0.9",
    author="Anders Prier Lindvig",
    author_email="anpl@mmmi.sdu.dk",
    description="Python interface for sending and receiving data to/from a UR robot using the Real-Time Data Exchange (RTDE) interface of the robot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    ext_modules=[CMakeExtension('ur_rtde')],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
    setup_requires=['setuptools_scm'],
    options={'build': {'build_base': 'build-setuptools'}},
    url="https://gitlab.com/sdurobotics/ur_rtde",
    classifiers=[
	"Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
