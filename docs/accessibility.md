# Accessibility

## Enable/disable colours in the command-line interface

Colours are enabled by default in the output of the command-line interface:

![Image of the Onyx command-line interface](img/cli.png)

 To disable them, create an environment variable `ONYX_COLOURS` with the value `NONE`:

```
$ export ONYX_COLOURS=NONE
```

![Image of the Onyx command-line interface without colours](img/cli-no-colours.png)

To re-enable colours, unset the environment variable:

```
$ unset ONYX_COLOURS
```
