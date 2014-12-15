import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "ptrial",
    version = "0.1",
    author = "Scott Lowrey",
    author_email = "sdlowrey@gmail.com",
    description = ("Performance trial management and measurement for software systems"),
    license = "BSD",
    keywords = "performance metrics distributed benchmark",
    url = "http://github.com/sdlowrey/ptrial",
    packages = ['ptrial', 'ptrial.observer'],
    scripts = ['bin/observe'],
    long_description = read('README'),
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
