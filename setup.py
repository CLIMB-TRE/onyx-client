import setuptools

exec(open("onyx_client/version.py").read())

setuptools.setup(
    name="onyx",
    author="Thomas Brier",
    version=__version__,  # type: ignore
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": "onyx = onyx_client.cli:main"},
)
