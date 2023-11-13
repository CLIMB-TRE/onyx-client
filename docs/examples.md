# Examples

## Retrieving data
#### The `get` endpoint
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
    # Get a single record
    record = client.get("project", "C-012346789")
    print(record)

    # Get only the cid and published_date of the record
    record = client.get(
        "project",
        "C-0123456789",
        include=["cid", "published_date"],
    )
    print(record)
```

#### The `filter` endpoint
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
    # Retrieve all records matching ALL of the field requirements
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
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient, OnyxField

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
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
        query=(~OnyxField(sample_type="swab"))
        & (
            OnyxField(collection_month__range=["2022-02", "2022-03"])
            | OnyxField(collection_month__range=["2022-06", "2022-09"])
        ),
    ):
        print(record)
```

## Uploading data
#### Create a record directly
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
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

#### Create records from a csv/tsv
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
    with open("/path/to/file.csv") as csv_file:
        # Create a single record
        client.csv_create(
            "project",
            csv_file=csv_file,
            # delimiter="\t", # If the file is a tsv
        )

    with open("/path/to/anotherfile.csv") as csv_file:
        # Create multiple records
        client.csv_create(
            "project",
            csv_file=csv_file,
            multiline=True,
            # delimiter="\t", # If the file is a tsv
        )
```

## Updating data
#### Update a record directly
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
    # Update a single record
    client.update(
        "project",
        "C-0123456789",
        fields={
            "name1": "value1",
            "name2": "value2",
            # ...
        },
    )
```

#### Update records from a csv/tsv
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
    with open("/path/to/file.csv") as csv_file:
        # Update a single record
        client.csv_update(
            "project",
            csv_file=csv_file,
            # delimiter="\t", # If the file is a tsv
        )

    with open("/path/to/anotherfile.csv") as csv_file:
        # Update multiple records
        client.csv_update(
            "project",
            csv_file=csv_file,
            multiline=True,
            # delimiter="\t", # If the file is a tsv
        )
```

## Delete data
#### Delete a record directly
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
    # Delete a single record
    client.delete("project", "C-0123456789")
```

#### Delete records from a csv/tsv
```python
import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)

with OnyxClient(config) as client:
    with open("/path/to/file.csv") as csv_file:
        # Delete a single record
        client.csv_delete(
            "project",
            csv_file=csv_file,
            # delimiter="\t", # If the file is a tsv
        )

    with open("/path/to/anotherfile.csv") as csv_file:
        # Delete multiple records
        client.csv_delete(
            "project",
            csv_file=csv_file,
            multiline=True,
            # delimiter="\t", # If the file is a tsv
        )
```
