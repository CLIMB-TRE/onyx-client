# `onyx`

Client Version: 2.0.0

**Usage**:

```console
$ onyx [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--config TEXT`: [env var: ONYX_CLIENT_CONFIG; default: ~/.onyx]
* `--domain TEXT`: [env var: ONYX_CLIENT_DOMAIN]
* `--token TEXT`: [env var: ONYX_CLIENT_TOKEN]
* `--version`: Show the client version number and exit.
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `init`: Create a `config` file.
* `register`: Register a new user.
* `login`: Log in to Onyx.
* `logout`: Log out of Onyx.
* `logoutall`: Log out of Onyx everywhere.
* `waiting`: List users waiting for approval.
* `approve`: Approve a user.
* `siteusers`: List site users.
* `allusers`: List all users.
* `projects`: View available projects.
* `fields`: View fields for a project.
* `choices`: View choices for a field.
* `get`: Get a record from a project.
* `filter`: Filter records from a project.

## `onyx init`

Create a `config` file.

**Usage**:

```console
$ onyx init [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx register`

Register a new user.

**Usage**:

```console
$ onyx register [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx login`

Log in to Onyx.

**Usage**:

```console
$ onyx login [OPTIONS]
```

**Options**:

* `--username TEXT`: [env var: ONYX_CLIENT_USERNAME]
* `--password TEXT`: [env var: ONYX_CLIENT_PASSWORD]
* `--help`: Show this message and exit.

## `onyx logout`

Log out of Onyx.

**Usage**:

```console
$ onyx logout [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx logoutall`

Log out of Onyx everywhere.

**Usage**:

```console
$ onyx logoutall [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx waiting`

List users waiting for approval.

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

* `USERNAME`: [required]

**Options**:

* `--help`: Show this message and exit.

## `onyx siteusers`

List site users.

**Usage**:

```console
$ onyx siteusers [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `onyx allusers`

List all users.

**Usage**:

```console
$ onyx allusers [OPTIONS]
```

**Options**:

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

View fields for a project.

**Usage**:

```console
$ onyx fields [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `--scope TEXT`
* `--help`: Show this message and exit.

## `onyx choices`

View choices for a field.

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

* `--include TEXT`
* `--exclude TEXT`
* `--scope TEXT`
* `--help`: Show this message and exit.

## `onyx filter`

Filter records from a project.

**Usage**:

```console
$ onyx filter [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `--field TEXT`
* `--include TEXT`
* `--exclude TEXT`
* `--scope TEXT`
* `--format [csv|tsv|json]`
* `--help`: Show this message and exit.
