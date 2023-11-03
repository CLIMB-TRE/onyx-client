# `onyx`

Client Version: 2.0.0

**Usage**:

```console
$ onyx [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-d, --domain TEXT`: Domain name for connecting to Onyx.  [env var: ONYX_DOMAIN]
* `-t, --token TEXT`: Token for authenticating with Onyx.  [env var: ONYX_TOKEN]
* `-u, --username TEXT`: Username for authenticating with Onyx.  [env var: ONYX_USERNAME]
* `-p, --password TEXT`: Password for authenticating with Onyx.  [env var: ONYX_PASSWORD]
* `-v, --version`: Show the client version number and exit.
* `--help`: Show this message and exit.

**Commands**:

* `projects`: View available projects.
* `fields`: View the field specification for a project.
* `get`: Get a record from a project.
* `filter`: Filter multiple records from a project.
* `choices`: View options for a choice field.
* `profile`: View profile information.
* `siteusers`: View users from the same site.
* `auth`: Authentication commands.
* `admin`: Admin commands.

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

* `-i, --include TEXT`: Specify which fields to include in the output.
* `-e, --exclude TEXT`: Specify which fields to exclude from the output.
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

* `-f, --field TEXT`: Filter the data by providing conditions that the fields must match. Uses a `name=value` syntax.
* `-i, --include TEXT`: Specify which fields to include in the output.
* `-e, --exclude TEXT`: Specify which fields to exclude from the output.
* `-s, --scope TEXT`: Access additional fields beyond the 'base' group of fields.
* `-F, --format [json|csv|tsv]`: Set the file format of the returned data.  [default: json]
* `--help`: Show this message and exit.

## `onyx choices`

View options for a choice field.

**Usage**:

```console
$ onyx choices [OPTIONS] PROJECT FIELD
```

**Arguments**:

* `PROJECT`: [required]
* `FIELD`: [required]

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

## `onyx siteusers`

View users from the same site.

**Usage**:

```console
$ onyx siteusers [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx auth`

Authentication commands.

**Usage**:

```console
$ onyx auth [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `register`: Create a new user.
* `login`: Log in.
* `logout`: Log out.
* `logoutall`: Log out across all clients.

### `onyx auth register`

Create a new user.

**Usage**:

```console
$ onyx auth register [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `onyx auth login`

Log in.

**Usage**:

```console
$ onyx auth login [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `onyx auth logout`

Log out.

**Usage**:

```console
$ onyx auth logout [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `onyx auth logoutall`

Log out across all clients.

**Usage**:

```console
$ onyx auth logoutall [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx admin`

Admin commands.

**Usage**:

```console
$ onyx admin [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `waiting`: View users waiting for approval.
* `approve`: Approve a user.
* `allusers`: View users across all sites.

### `onyx admin waiting`

View users waiting for approval.

**Usage**:

```console
$ onyx admin waiting [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `onyx admin approve`

Approve a user.

**Usage**:

```console
$ onyx admin approve [OPTIONS] USERNAME
```

**Arguments**:

* `USERNAME`: Name of the user being approved.  [required]

**Options**:

* `--help`: Show this message and exit.

### `onyx admin allusers`

View users across all sites.

**Usage**:

```console
$ onyx admin allusers [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
