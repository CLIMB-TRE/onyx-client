import sys
import json
import inspect
import requests
from getpass import getpass


def construct_fields_dict(arg_fields):
    """
    Takes a list of field-value pairs: `[[field1, value], [field2, value], ...]`

    Returns a fields dict: `{field1 : [value, value, ...], field2 : [value, value, ...]}`
    """
    fields = {}
    if arg_fields is not None:
        for f, v in arg_fields:
            fields.setdefault(f, []).append(v)
    return fields


def construct_unique_fields_dict(arg_fields):
    """
    Takes a list of field-value pairs: `[[field1, value], [field2, value], ...]`

    Returns a fields dict: `{field1 : value, field2 : value}`

    Raises a `KeyError` for any duplicate fields.
    """
    fields = {}
    if arg_fields is not None:
        for f, v in arg_fields:
            if f in fields:
                raise KeyError(f"Field '{f}' was provided more than once")
            else:
                fields[f] = v
    return fields


def construct_scope_list(arg_fields):
    """
    Takes a list of list of scopes: `[[scope, scope, ...], [scope, scope, ...], ...]`

    Returns a list of scopes: `[scope, scope, scope, ...]`
    """
    return [s for scopes in arg_fields for s in scopes]


def print_response(response, pretty_print=True, status_only=False):
    """
    Print the response and make it look lovely.

    Responses with `response.ok == False` are written to `sys.stderr`.
    """
    if pretty_print:
        indent = 4
    else:
        indent = None
    status_code = f"<[{response.status_code}] {response.reason}>"
    try:
        if status_only:
            formatted_response = str(status_code)
        else:
            formatted_response = (
                f"{status_code}\n{json.dumps(response.json(), indent=indent)}"
            )
    except json.decoder.JSONDecodeError:
        formatted_response = f"{status_code}\n{response.text}"

    if response.ok:
        print(formatted_response)
    else:
        print(formatted_response, file=sys.stderr)


def raise_for_status(response):
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        print_response(response)
        raise e


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


def session_required(method):
    """
    Decorator that does the following:

    * Checks the client object has session details.
    * Runs the provided method and returns the output.
    * Writes user tokens to their tokens file, after running the provided method.
    """

    # If the method is a generator we have to use 'yield from'
    # Meddling with forces I don't fully understand here, but it works
    if inspect.isgeneratorfunction(method):

        def wrapped_generator_method(obj, *args, **kwargs):
            if not hasattr(obj, "token"):
                raise Exception("The client has no token to log in with")
            try:
                # Run the method and yield the output
                output = yield from method(obj, *args, **kwargs)
            finally:
                # ONLY when the method has finished yielding do we reach this point
                # After everything is done, write the user tokens to their tokens file
                obj.config.write_token(obj.username, obj.token, obj.expiry)
            return output

        return wrapped_generator_method

    else:

        def wrapped_method(obj, *args, **kwargs):
            if not hasattr(obj, "token"):
                raise Exception("The client has no token to log in with")
            try:
                # Run the method and get the output
                output = method(obj, *args, **kwargs)
            finally:
                # After everything is done, write the user tokens to their tokens file
                obj.config.write_token(obj.username, obj.token, obj.expiry)
            return output

        return wrapped_method


def execute_uploads(uploads):
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


def iterate(responses):
    for response in responses:
        raise_for_status(response)

        for result in response.json()["data"]["records"]:
            yield result
