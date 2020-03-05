import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme_file:
    README = readme_file.read()

setup(
    name="autograder-contrib",
    description="Community-written scrips that utilize the autograder.io API",
    long_description=README,
    version="1.0.0",
    author="James Perretta",
    author_email="jameslp@umich.edu",
    url="https://github.com/eecs-autograder/autograder-contrib",
    license="GNU Lesser General Public License v3",
    packages=["ag_contrib"],
    keywords=["autograder"],
    install_requires=[
        "requests"
    ],
    classifiers=['Programming Language :: Python :: 3.6'],

    # Python command line utilities will be installed in a PATH-accessible bin/
    entry_points={
        'console_scripts': [
            'ag-clone-course = ag_contrib.ag_roster:main',
        ]
    },
)
