# `onyx`

Client Version: 2.0.0

**Usage**:

```console
$ onyx [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-d, --domain TEXT`: Domain name for Onyx.  [env var: ONYX_DOMAIN]
* `-t, --token TEXT`: Token for authentication.  [env var: ONYX_TOKEN]
* `-v, --version`: Show the client version number and exit.
* `--help`: Show this message and exit.

**Commands**:

* `register`: Create a new user.
* `login`: Log in.
* `logout`: Log out.
* `logoutall`: Log out across all clients.
* `profile`: View profile information.
* `waiting`: View users waiting for approval.
* `approve`: Approve a user.
* `users`: View users from the same site.
* `projects`: View available projects.
* `fields`: View the field specification for a project.
* `choices`: View allowed choices for a field.
* `get`: Get a record from a project.
* `filter`: Filter multiple records from a project.

## `onyx register`

Create a new user.

**Usage**:

```console
$ onyx register [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx login`

Log in.

**Usage**:

```console
$ onyx login [OPTIONS]
```

**Options**:

* `-u, --username TEXT`: Name of the user logging in.  [env var: ONYX_USERNAME]
* `-p, --password TEXT`: Password of the user logging in.  [env var: ONYX_PASSWORD]
* `--help`: Show this message and exit.

## `onyx logout`

Log out.

**Usage**:

```console
$ onyx logout [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx logoutall`

Log out across all clients.

**Usage**:

```console
$ onyx logoutall [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx profile`

View profile information.

**Usage**:

```console
$ onyx profile [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx waiting`

View users waiting for approval.

**Usage**:

```console
$ onyx waiting [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx approve`

Approve a user.

**Usage**:

```console
$ onyx approve [OPTIONS] USERNAME
```

**Arguments**:

* `USERNAME`: Name of the user being approved.  [required]

**Options**:

* `--help`: Show this message and exit.

## `onyx users`

View users from the same site.

**Usage**:

```console
$ onyx users [OPTIONS]
```

**Options**:

* `-a, --all`: View all users, across all sites
* `--help`: Show this message and exit.

## `onyx projects`

View available projects.

**Usage**:

```console
$ onyx projects [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx fields`

View the field specification for a project.

**Usage**:

```console
$ onyx fields [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `-s, --scope TEXT`: Access additional fields beyond the 'base' group of fields.
* `--help`: Show this message and exit.

## `onyx choices`

View allowed choices for a field.

**Usage**:

```console
$ onyx choices [OPTIONS] PROJECT FIELD
```

**Arguments**:

* `PROJECT`: [required]
* `FIELD`: [required]

**Options**:

* `--help`: Show this message and exit.

## `onyx get`

Get a record from a project.

**Usage**:

```console
$ onyx get [OPTIONS] PROJECT CID
```

**Arguments**:

* `PROJECT`: [required]
* `CID`: [required]

**Options**:

* `-i, --include TEXT`: Set which fields to include in the output.
* `-e, --exclude TEXT`: Set which fields to exclude from the output.
* `-s, --scope TEXT`: Access additional fields beyond the 'base' group of fields.
* `--help`: Show this message and exit.

## `onyx filter`

Filter multiple records from a project.

**Usage**:

```console
$ onyx filter [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `-f, --field TEXT`: Filter the data by providing criteria that fields must match. Uses a `name=value` syntax.
* `-i, --include TEXT`: Set which fields to include in the output.
* `-e, --exclude TEXT`: Set which fields to exclude from the output.
* `-s, --scope TEXT`: Access additional fields beyond the 'base' group of fields.
* `-F, --format [json|csv|tsv]`: Set the file format of the returned data.  [default: json]
* `--help`: Show this message and exit.
