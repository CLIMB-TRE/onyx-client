---
hide:
  - navigation
---

# Onyx-client

## Introduction

This site documents usage of [Onyx-client](https://github.com/CLIMB-TRE/onyx-client), a program designed for interacting with the [Onyx](https://github.com/CLIMB-TRE/onyx/) database. 

Onyx-client and Onyx are being developed as part of the [CLIMB-TRE](https://climb-tre.github.io/) project. 

![Onyx](img/onyx.png)

## Installation

### Install from conda-forge (recommended)

```
$ conda create --name onyx --channel conda-forge climb-onyx-client
```

This installs the latest version of the Onyx-Client from [conda-forge](https://anaconda.org/conda-forge/climb-onyx-client).

### Install from PyPI

```
$ pip install climb-onyx-client
```

This installs the latest version of the Onyx-Client from [PyPI](https://pypi.org/project/climb-onyx-client/).

### Build from source

Download the source code from Github:

```
$ git clone https://github.com/CLIMB-COVID/onyx-client.git
```

Run installation from within the source code directory:

```
$ cd onyx-client/
$ pip install .
```

## Accessibility

### Enable/disable colours

Colours are enabled by default in the output of the Onyx-Client. To disable them, create an environment variable `ONYX_COLOURS` with the value `NONE`:

```
$ export ONYX_COLOURS=NONE
```

To re-enable colours, unset the environment variable:

```
$ unset ONYX_COLOURS
```