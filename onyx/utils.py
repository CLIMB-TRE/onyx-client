import sys
import json
import requests
from getpass import getpass
from typing import Generator, Any, List, Dict


def construct_fields_dict(arg_fields: List[List[str]]) -> Dict[str, List[str]]:
    """
    Takes a list of field-value pairs: `[[field1, value], [field2, value], ...]`

    Returns a fields dict: `{field1 : [value, value, ...], field2 : [value, value, ...]}`
    """

    fields = {}
    if arg_fields is not None:
        for f, v in arg_fields:
            fields.setdefault(f, []).append(v)
    return fields


def construct_unique_fields_dict(arg_fields: List[List[str]]) -> Dict[str, str]:
    """
    Takes a list of field-value pairs: `[[field1, value], [field2, value], ...]`

    Returns a fields dict: `{field1 : value, field2 : value}`

    Raises a `KeyError` for any duplicate fields.
    """

    fields = {}
    if arg_fields is not None:
        for f, v in arg_fields:
            if f in fields:
                raise KeyError(f"Field '{f}' was provided more than once.")
            else:
                fields[f] = v
    return fields


def flatten_list_of_lists(arg_fields: List[List[str]]) -> List[str]:
    """
    Takes a list of lists: `[[val1, val2, ...], [val3, val4, ...], ...]`

    Returns a single list: `[val1, val2, ..., val3, val4, ...]`
    """

    return [s for scopes in arg_fields for s in scopes]


def print_response(response: requests.Response, pretty_print: bool = True):
    """
    Print the response and make it look lovely.

    Responses with `response.ok == False` are written to `sys.stderr`.
    """

    if pretty_print:
        indent = 4
    else:
        indent = None

    try:
        formatted_response = json.dumps(response.json(), indent=indent)
    except json.decoder.JSONDecodeError:
        formatted_response = response.text

    if response.ok:
        print(formatted_response)
    else:
        print(formatted_response, file=sys.stderr)


def get_input(field, password=False, type=None, required=True):
    """
    Get user input/password, ensuring they enter something.
    """

    if type is None:
        type = str
    if password:
        # User input is not displayed to the terminal with getpass
        input_func = getpass
    else:
        input_func = input
    try:
        # Take user input, strip it and convert to required type
        value = type(input_func(f"{field[0].upper()}{field[1:].lower()}: ").strip())
    except ValueError:
        value = ""
    if required:
        while not value:
            try:
                value = type(
                    input_func(f"Please enter a valid {field.lower()}: ").strip()
                )
            except ValueError:
                value = ""
    return value


def execute_uploads(uploads: Generator[requests.Response, Any, None]):
    attempted = 0
    successes = 0
    failures = 0

    try:
        for upload in uploads:
            print_response(upload)

            attempted += 1
            if upload.ok:
                successes += 1
            else:
                failures += 1

    except KeyboardInterrupt:
        print("")

    finally:
        print("[UPLOADS]")
        print(f"Attempted: {attempted}")
        print(f"Successes: {successes}")
        print(f"Failures: {failures}")
