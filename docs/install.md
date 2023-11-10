# Installation Guide 

This guide walks through how to install the Onyx client.

## Setup

Create a Python virtual environment for the client:

```
$ python -m venv onyx-env
```

Install the client within this environment:

```
$ source onyx-env/bin/activate
$ pip install climb-onyx-client
```

## Create a config

Generate a config folder with the `onyx config create` command.

For this you need to provide:

* `Domain`: this should be `https://onyx-test.climb.ac.uk`
* `Config directory`: specify a folder that does not exist, e.g. `onyx-config`

For example:

```
$ onyx config create --domain https://onyx-test.climb.ac.uk --config-dir onyx-config
```

Once this is done, you **must** export the environment variable `ONYX_CLIENT_CONFIG` as the path to the config directory.

## Register

Register for an Onyx account with the `onyx register` command.

For this you need to provide:

* `First name`
* `Last name`
* `Email address`
* `Site code`: set this to `users`
* `Password`: this will need to be entered twice

For example:

```
$ onyx register
```

And then follow the instructions.

## Log in

To log in to your Onyx account, run the following command and enter your password:

```
$ onyx login
```

## View available projects

Once logged in, run the following command to view all the projects available to you:

```
$ onyx projects
```

If you cannot see the projects that you require access to, contact an admin.

If you can see your intended project, then you can run the following to view the fields available within that project:

```
$ onyx fields <project-name>
```


## View data from a project

To view all data from a project:

```
$ onyx filter <project-name>
```

To export that data to a `.tsv` file:

```
$ onyx filter <project-name> --format tsv > data.tsv
```

You can also filter the data so that it falls within various requirements on its fields.

### Examples

To filter for all samples published on a specific date (e.g. `2023-09-18`):

```
$ onyx filter <project-name> --field published_date 2023-09-18
```

To filter for all samples published on the current date, you can use the keyword `today`:

```
$ onyx filter <project-name> --field published_date today
```

To filter for all samples with a `published_date` within the dates `2023-09-01` and `2023-09-18`, you can use the `range` filter: 

```
$ onyx filter <project-name> --field published_date__range 2023-09-01,2023-09-18
```

## Further guidance

For further guidance using the Onyx client, use the `--help` option.

```
$ onyx --help
$ onyx filter --help
```

For more information, such as how to use the Python API, check out the README file on the Onyx client's [GitHub page](https://github.com/CLIMB-TRE/onyx-client).
