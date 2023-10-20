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
                                                                                                                                  
 Welcome to Onyx.                                                                                                                 
                                                                                                                                  
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config                    TEXT                             [env var: ONYX_CLIENT_CONFIG] [default: ~/.onyx]                  │
│ --domain                    TEXT                             [env var: ONYX_CLIENT_DOMAIN] [default: None]                     │
│ --token                     TEXT                             [env var: ONYX_CLIENT_TOKEN] [default: None]                      │
│ --version                                                    Show the client version number and exit.                          │
│ --install-completion        [bash|zsh|fish|powershell|pwsh]  Install completion for the specified shell. [default: None]       │
│ --show-completion           [bash|zsh|fish|powershell|pwsh]  Show completion for the specified shell, to copy it or customize  │
│                                                              the installation.                                                 │
│                                                              [default: None]                                                   │
│ --help                                                       Show this message and exit.                                       │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ init                           Create a config file.                                                                           │
│ register                       Register a new user.                                                                            │
│ login                          Log in to Onyx.                                                                                 │
│ logout                         Log out of Onyx.                                                                                │
│ logoutall                      Log out of Onyx everywhere.                                                                     │
│ waiting                        List users waiting for approval.                                                                │
│ approve                        Approve a user.                                                                                 │
│ siteusers                      List site users.                                                                                │
│ allusers                       List all users.                                                                                 │
│ projects                       View available projects.                                                                        │
│ fields                         View fields for a project.                                                                      │
│ choices                        View choices for a field.                                                                       │
│ get                            Get a record from a project.                                                                    │
│ filter                         Filter records from a project.                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Create a config
```
$ onyx init
```

## Register a user
```
$ onyx register
```

## View projects
#### View available projects
```
$ onyx projects
```

#### View fields within a project
```
$ onyx fields <project>
```

## Upload data
#### Create a single record
```
$ onyx create <project> --field <name> <value> --field <name> <value> ...
```
```python
from onyx import OnyxClient

with OnyxClient() as client:
    # Create a single record
    client.create(
        "project",
        fields={
            "name1": "value1",
            "name2": "value2",
            # ...
        },
    )
```

#### Create multiple records from a csv/tsv
```
$ onyx create <project> --csv <csv>
$ onyx create <project> --tsv <tsv>
```

##### From a path to a csv/tsv
```python
from onyx import OnyxClient

with OnyxClient() as client:
    # Iterating the function triggers the uploads
    for record in client.csv_create(
        "project",
        csv_path="/path/to/file.csv",
        # delimiter="\t", # For uploading from a tsv
    ):
        pass
```

##### From a file handle for a csv/tsv
```python
from onyx import OnyxClient

with OnyxClient() as client:
    with open("/path/to/file.csv") as csv_file:
        # Iterating the function triggers the uploads
        for record in client.csv_create(
            "project",
            csv_file=csv_file,
            # delimiter="\t", # For uploading from a tsv
        ):
            pass
```

## Retrieve data
#### The `get` endpoint
```
$ onyx get <project> <cid>
```
```python
from onyx import OnyxClient

with OnyxClient() as client:
    # Get the entire record
    record = client.get("project", "C-1234678")
    print(record)

    # Get only the cid and published_date of the record
    record = client.get("project", "C-12345678", include=["cid", "published_date"])
    print(record)
```

#### The `filter` endpoint
```
$ onyx filter <project> --field <name> <value> --field <name> <value> ...
```
```python
from onyx import OnyxClient

# Retrieve all records matching ALL of the field requirements
with OnyxClient() as client:
    for record in client.filter(
        "project",
        fields={
            "name1": "value1",
            "name2": "value2",
            "name3__startswith": "value3",
            "name4__range": "value4, value5",
            # ...
        },
    ):
        print(record)
```

#### The `query` endpoint 
```python
from onyx import OnyxClient, F

with OnyxClient() as client:
    # The python bitwise operators can be used in a query.
    # These are:
    # AND: &
    # OR:  |
    # XOR: ^
    # NOT: ~

    # Example query:
    # This query is asking for all records that:
    # Do NOT have a sample_type of 'swab', AND:
    # - Have a collection_month between Feb-Mar 2022
    # - OR have a collection_month between Jun-Sept 2022
    for record in client.query(
        "project",
        query=(~F(sample_type="swab"))
        & (
            F(collection_month__range=["2022-02", "2022-03"])
            | F(collection_month__range=["2022-06", "2022-09"])
        ),
    ):
        print(record)
```

#### Supported lookups for `filter` and `query`
| Lookup            | Numeric | Text | Date (YYYY-MM-DD) | Date (YYYY-MM) | True/False |
| ----------------- | :-----: | :--: | :---------------: | :------------: | :--------: |
| `exact`           | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `ne`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `lt`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `lte`             | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `gt`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `gte`             | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `in`              | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `range`           | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `isnull`          | ✓       | ✓    | ✓                 | ✓              | ✓          |
| `contains`        |         | ✓    |                   |                |            |
| `startswith`      |         | ✓    |                   |                |            | 
| `endswith`        |         | ✓    |                   |                |            | 
| `iexact`          |         | ✓    |                   |                |            |  
| `icontains`       |         | ✓    |                   |                |            | 
| `istartswith`     |         | ✓    |                   |                |            | 
| `iendswith`       |         | ✓    |                   |                |            | 
| `regex`           |         | ✓    |                   |                |            | 
| `iregex`          |         | ✓    |                   |                |            | 
| `year`            |         |      | ✓                 | ✓              |            |
| `year__in`        |         |      | ✓                 | ✓              |            |
| `year__range`     |         |      | ✓                 | ✓              |            |
| `iso_year`        |         |      | ✓                 |                |            |
| `iso_year__in`    |         |      | ✓                 |                |            |
| `iso_year__range` |         |      | ✓                 |                |            |
| `iso_week`        |         |      | ✓                 |                |            |
| `iso_week__in`    |         |      | ✓                 |                |            |
| `iso_week__range` |         |      | ✓                 |                |            |

Most of these lookups (excluding `ne`, which is a custom lookup meaning `not equal`) correspond directly to Django's built-in 'field lookups'. More information on what each lookup means can be found at: https://docs.djangoproject.com/en/4.1/ref/models/querysets/#field-lookups

## Update data
#### Update a single record
```
$ onyx update <project> <cid> --field <name> <value> --field <name> <value> ...
```
```python
from onyx import OnyxClient

with OnyxClient() as client:
    client.update(
        "project",
        "C-12345678",
        fields={
            "name1": "value1",
            "name2": "value2",
            # ...
        },
    )
```

#### Update multiple records from a csv/tsv
```
$ onyx update <project> --csv <csv>
$ onyx update <project> --tsv <tsv>
```

##### From a path to a csv/tsv
```python
from onyx import OnyxClient

with OnyxClient() as client:
    # Iterating the function triggers the uploads
    for record in client.csv_update(
        "project",
        csv_path="/path/to/file.csv",
        # delimiter="\t", # For uploading from a tsv
    ):
        pass
```

##### From a file handle for a csv/tsv
```python
from onyx import OnyxClient

with OnyxClient() as client:
    with open("/path/to/file.csv") as csv_file:
        # Iterating the function triggers the uploads
        for record in client.csv_update(
            "project",
            csv_file=csv_file,
            # delimiter="\t", # For uploading from a tsv
        ):
            pass
```

## Delete data
#### Delete a single record
```
$ onyx delete <project> <cid>
```
```python
from onyx import OnyxClient 

with OnyxClient() as client:
    client.delete("project", "C-12345678")
```

#### Delete multiple records from a csv/tsv
```
$ onyx delete <project> --csv <csv>
$ onyx delete <project> --tsv <tsv>
```

##### From a path to a csv/tsv
```python
from onyx import OnyxClient

with OnyxClient() as client:
    # Iterating the function triggers the uploads
    for record in client.csv_delete(
        "project",
        csv_path="/path/to/file.csv",
        # delimiter="\t", # For uploading from a tsv
    ):
        pass
```

##### From a file handle for a csv/tsv
```python
from onyx import OnyxClient

with OnyxClient() as client:
    with open("/path/to/file.csv") as csv_file:
        # Iterating the function triggers the uploads
        for record in client.csv_delete(
            "project",
            csv_file=csv_file,
            # delimiter="\t", # For uploading from a tsv
        ):
            pass
```
