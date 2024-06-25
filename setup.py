import setuptools

with open("onyx/version.py") as version_file:
    version = version_file.read().split('"')[1]
    assert len(version.split(".")) == 3

with open("README.md") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="climb-onyx-client",
    version=version,
    author="Thomas Brier",
    author_email="t.o.brier@bham.ac.uk",
    description="CLI and Python library for Onyx",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CLIMB-TRE/onyx-client",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": "onyx = onyx.cli:main"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    install_requires=[
        "requests",
        "typer>=0.12.3",
        "rich",
    ],
)
