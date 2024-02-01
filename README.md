# `onyx-client`

## Setup

#### Install via pip

```
$ pip install climb-onyx-client
```

#### Build from source

Download and install the client into a Python virtual environment:

```
$ git clone https://github.com/CLIMB-COVID/onyx-client.git
$ cd onyx-client/
$ python -m venv env
$ source env/bin/activate
$ pip install .
```

Check it works:

```
$ onyx
                                                                                             
 Usage: onyx [OPTIONS] COMMAND [ARGS]...                                                     
                                                                                             
 API for pathogen metadata.                                                                  
                                                                                             
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
│ projects       View available projects.                                                   │
│ fields         View the field specification for a project.                                │
│ choices        View options for a choice field.                                           │
│ get            Get a record from a project.                                               │
│ filter         Filter multiple records from a project.                                    │
│ identify       Get the anonymised identifier for a value on a field.                      │
│ profile        View profile information.                                                  │
│ siteusers      View users from the same site.                                             │
│ auth           Authentication commands.                                                   │
│ admin          Admin commands.                                                            │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
```

For more information, check out the [documentation](https://climb-tre.github.io/onyx-client/).
