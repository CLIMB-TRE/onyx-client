# `onyx`

Client Version: 2.0.0

**[WARNING]**: THIS DOCUMENTATION IS NOT UP TO DATE.

## Uploading data
#### Create a single record
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

## Retrieving data
#### The `get` endpoint
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
from onyx import OnyxClient, OnyxField

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

## Updating data
#### Update a single record
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
```python
from onyx import OnyxClient 

with OnyxClient() as client:
    client.delete("project", "C-12345678")
```

#### Delete multiple records from a csv/tsv
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
