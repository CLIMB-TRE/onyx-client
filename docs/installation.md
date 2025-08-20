# Installation

Guidance for installing the Onyx client, or building it manually for development.

!!! info "Usage within CLIMB JupyterLab Servers"
    If you are running a CLIMB JupyterLab server, you **do not** need to install the client, as it comes pre-configured in your environment.

    If you cannot see the most up-to-date version of the Onyx client, this is because you will have previously installed your own version manually.

    To revert your Onyx client to the managed up-to-date version, navigate to your terminal and run:

    ```
    $ pip uninstall climb-onyx-client
    ```

    And restart your JupyterLab server.

## Install from conda-forge

```
$ conda create --name onyx --channel conda-forge climb-onyx-client
```

This installs the latest version of the client from [conda-forge](https://anaconda.org/conda-forge/climb-onyx-client).

## Install from PyPI

```
$ pip install climb-onyx-client
```

This installs the latest version of the client from [PyPI](https://pypi.org/project/climb-onyx-client/).

## Build from source

Clone the source code from GitHub:

```
$ git clone https://github.com/CLIMB-TRE/onyx-client.git
```

Run installation from within the source code directory:

```
$ cd onyx-client/
$ pip install .
```

### Developing the Client

If you wish to develop the client, ensure you have followed the above steps to build it.

From there, you can simply modify the client code and dependencies, and rebuild by executing:

```
$ pip install .
```
