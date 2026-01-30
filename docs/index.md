---
hide:
  - toc
---

# CLI & Python API for Onyx

## Introduction

This is the documentation for [Onyx-client](https://github.com/CLIMB-TRE/onyx-client), a program that provides a command-line interface and Python API for interacting with the [Onyx](https://github.com/CLIMB-TRE/onyx/) database.

Onyx is being developed as part of the [CLIMB-TRE](https://climb-tre.github.io/) project.

A PDF of this documentation can be found [here](/onyx-client/onyx-client.pdf).

![](img/cli.png)

## Contents

[Installation](installation.md)<br>
Learn how to install the client, or build it manually for development.

[Accessibility](accessibility.md)<br>
Learn how to enable/disable colours in the CLI.

### Command-line Interface

[Getting Started](cli/getting-started.md)<br>
Get started with filtering data on the command-line with Onyx.

[Documentation](cli/documentation.md)<br>
Documentation on all command-line functionality.

### Python API

[OnyxClient](api/documentation/client.md)<br>
Documentation on the `OnyxClient` class, used for interacting with Onyx.

[OnyxConfig](api/documentation/config.md)<br>
Documentation on the `OnyxConfig` class, used to provide credentials to `OnyxClient`.

[OnyxEnv](api/documentation/config.md)<br>
Documentation on the `OnyxEnv` class, used as a shortcut to environment variable credentials.

[OnyxField](api/documentation/field.md)<br>
Documentation on the `OnyxField` class, used to represent fields in an `OnyxClient` query.

[Exceptions](api/documentation/exceptions.md)<br>
Documentation on the possible exceptions raised by the `OnyxClient`.
