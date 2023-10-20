import setuptools

exec(open("onyx/version.py").read())

setuptools.setup(
    name="climb-onyx-client",
    author="Thomas Brier",
    version=__version__,  # type: ignore
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": "onyx = onyx.cli2:main"},
    install_requires=[
        "requests",
        "typer",
        "rich",
        "django-query-tools>=0.3.3",
    ],
)
