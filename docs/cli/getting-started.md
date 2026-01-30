[](){#cli-getting-started}
# Getting Started

This guide walks through getting started with the Onyx-client command-line interface.

The guide assumes an environment where authentication credentials are pre-configured.

![Image of the Onyx command-line interface](../img/cli.png)

## Profile information

```
$ onyx profile
```

## Available projects

```
$ onyx projects
```

If you cannot see the project(s) that you require access to, contact an admin.

## Project fields

```
$ onyx fields PROJECT
```

This returns the fields specification for the given `PROJECT`.

## Project data

```
$ onyx filter PROJECT
```

This returns all records from the given `PROJECT`.

The data can be exported to various file formats:

```
$ onyx filter PROJECT --format json > data.json
$ onyx filter PROJECT --format csv > data.csv
$ onyx filter PROJECT --format tsv > data.tsv
```

### Filtering

A project's data can be filtered to return records that match certain conditions.

Filtering on the CLI uses a `field=value` syntax, where `field` is the name of a field in the project, and `value` is the value you want to match.

Multiple filters can be provided, and only the records that satisfy *all* these filters will be returned.

### Advanced filtering using lookups

The data can be filtered in more complex ways using [lookups](https://climb-tre.github.io/onyx/fields/lookups/). These use a `field.lookup=value` syntax (or alternatively, `field__lookup=value`), and different ones are available depending on a field's [data type](https://climb-tre.github.io/onyx/fields/types/) (e.g. [`text`](https://climb-tre.github.io/onyx/fields/types/#text), [`integer`](https://climb-tre.github.io/onyx/fields/types/#integer)). There are lookups for searching between a range of values on a field ([`range`](https://climb-tre.github.io/onyx/fields/lookups/#range)), whether a field's value is empty ([`isnull`](https://climb-tre.github.io/onyx/fields/lookups/#isnull)), whether a field case-insensitively contains some text ([`icontains`](https://climb-tre.github.io/onyx/fields/lookups/#icontains)), and [more](https://climb-tre.github.io/onyx/fields/lookups/). 

### Examples

To filter for all records in a `PROJECT` published on a specific date (e.g. `2023-09-18`):

```
$ onyx filter PROJECT --field published_date=2023-09-18
```

To filter for all records in a `PROJECT` published on the current date, a special `today` keyword can be used:

```
$ onyx filter PROJECT --field published_date=today
```

To filter for all records in a `PROJECT` with a `published_date` from `2023-09-01` to `2023-09-18`, the `range` lookup can be used: 

```
$ onyx filter PROJECT --field published_date.range=2023-09-01,2023-09-18
```

Assuming that `PROJECT` has a `sample_type` field, then all records with `sample_type = "swab"` that were published from `2023-09-01` to `2023-09-18` can be obtained with: 

```
$ onyx filter PROJECT --field published_date.range=2023-09-01,2023-09-18 --field sample_type=swab
```

## Further guidance

For further guidance using Onyx-client, use the `--help` option.

```
$ onyx --help
$ onyx profile --help
$ onyx projects --help
$ onyx fields --help
$ onyx filter --help
```
