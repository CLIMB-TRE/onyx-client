![](images/banner.png)

# Onyx-client

## Overview

A command-line interface and Python API for interacting with the [Onyx](https://github.com/CLIMB-TRE/onyx) database. Onyx-client provides both CLI commands and Python methods for:

- Viewing projects, and their field specifications
- Creating/updating/deleting project records and analyses
- Retrieving full details and change history of an individual record/analysis
- Granular filtering/aggregation functionality across multiple records and analyses
- Exporting of data in JSON/CSV/TSV formats
- Matching anonymised identifiers to their original values

For more information, check out the [documentation](https://climb-tre.github.io/onyx-client/).

## Setup

### Install from [conda-forge](https://anaconda.org/conda-forge/climb-onyx-client)

```
$ conda create --name onyx --channel conda-forge climb-onyx-client
```

### Install from [PyPI](https://pypi.org/project/climb-onyx-client/)

```
$ pip install climb-onyx-client
```

### Build from source

Download and install the client into a Python virtual environment:

```
$ git clone https://github.com/CLIMB-TRE/onyx-client.git
$ cd onyx-client/
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install .
```

Check it works:

```
$ onyx
                                                                                             
 Usage: onyx [OPTIONS] COMMAND [ARGS]...                                                     
                                                                                             
 API for Pathogen Metadata.                                                                  
 For documentation, see: https://climb-tre.github.io/onyx-client/                            
                                                                                             
╭─ Options ─────────────────────────────────────────────────────────────────────────────────╮
│ --domain    -d      TEXT  Domain name for connecting to Onyx. [env var: ONYX_DOMAIN]      │
│                           [default: None]                                                 │
│ --token     -t      TEXT  Token for authenticating with Onyx. [env var: ONYX_TOKEN]       │
│                           [default: None]                                                 │
│ --username  -u      TEXT  Username for authenticating with Onyx. [env var: ONYX_USERNAME] │
│                           [default: None]                                                 │
│ --password  -p      TEXT  Password for authenticating with Onyx. [env var: ONYX_PASSWORD] │
│                           [default: None]                                                 │
│ --version   -v            Show the client version number and exit.                        │
│ --help      -h            Show this message and exit.                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────────╮
│ auth               Authentication commands.                                               │
│ admin              Admin commands.                                                        │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Info ────────────────────────────────────────────────────────────────────────────────────╮
│ projects           View available projects.                                               │
│ types              View available field types.                                            │
│ lookups            View available lookups.                                                │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Records ─────────────────────────────────────────────────────────────────────────────────╮
│ fields             View the field specification for a project.                            │
│ choices            View options for a choice field in a project.                          │
│ get                Get a record from a project.                                           │
│ filter             Filter multiple records from a project.                                │
│ history            View the history of a record in a project.                             │
│ analyses           View analyses of a record in a project.                                │
│ identify           Get the anonymised identifier for a value on a field.                  │
│ create             Create a record in a project.                                          │
│ update             Update a record in a project.                                          │
│ delete             Delete a record in a project.                                          │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Analyses ────────────────────────────────────────────────────────────────────────────────╮
│ analysis-fields    View the analysis field specification for a project.                   │
│ analysis-choices   View options for an analysis choice field.                             │
│ get-analysis       Get an analysis from a project.                                        │
│ filter-analysis    Filter multiple analyses from a project.                               │
│ analysis-history   View the history of an analysis in a project.                          │
│ analysis-records   View records involved in an analysis in a project.                     │
│ create-analysis    Create an analysis in a project.                                       │
│ update-analysis    Update an analysis in a project.                                       │
│ delete-analysis    Delete an analysis in a project.                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Accounts ────────────────────────────────────────────────────────────────────────────────╮
│ profile            View profile information.                                              │
│ activity           View latest profile activity.                                          │
│ siteusers          View users from the same site.                                         │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
```
