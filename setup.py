import setuptools

exec(open("onyx/version.py").read())

setuptools.setup(
    name="climb-onyx-client",
    author="Thomas Brier",
    version=__version__,  # type: ignore
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": "onyx = onyx.cli:main"},
    install_requires=[
        "requests",
        "django-query-tools",
    ],
)
