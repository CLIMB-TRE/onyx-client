def check_kwargs(kwargs):
    if len(kwargs) != 1:
        raise Exception("Exactly one field and its value must be provided")


def check_field(field):
    if not isinstance(field, F):
        raise Exception("Can only combine F object with other F objects")


def combine_on_associative(operation, field1, field2):
    """
    Combine two pre-existing queries on an ASSOCIATIVE operation (`&`, `|`, `^`), and use this to reduce nested JSON.

    E.g. take the following query:

    `((X & Y) & Z) | (W & (X & (Y | (Z | X))))`

    We can use associativity of `&` and `|` to reduce how deeply nested the JSON request body is.

    By associativity of `&` and `|`, the following is unambiguous and logically equivalent to the previous query:

    `(X & Y & Z) | (W & X & (Y | Z | X))`

    With the former corresponding to more deeply-nested JSON than the latter.

    Believe it or not this is somewhat useful!! There is normally a limit on how deeply nested a JSON request body can be.

    So by preventing unnecessary nesting, users can programatically construct and execute a broader range of queries.
    """
    field1_key = next(iter(field1.query))
    field2_key = next(iter(field2.query))

    # For each field
    # If the topmost key is equal to the current operation, we pull out the values
    # Otherwise, they stay self-contained
    if field1_key == operation:
        field1_query = field1.query[field1_key]
    else:
        field1_query = [field1.query]

    if field2_key == operation:
        field2_query = field2.query[field1_key]
    else:
        field2_query = [field2.query]

    return F(**{operation: field1_query + field2_query})


class F:
    def __init__(self, **kwargs):
        check_kwargs(kwargs)

        field, value = next(iter(kwargs.items()))

        if field not in ["&", "|", "^", "~"]:
            if type(value) in [list, tuple, set]:
                # Multi-value lookups require values in a comma-separated string
                value = ",".join(map(str, value))

        self.query = {field: value}

    def __and__(self, field):
        check_field(field)
        return combine_on_associative("&", self, field)

    def __or__(self, field):
        check_field(field)
        return combine_on_associative("|", self, field)

    def __xor__(self, field):
        check_field(field)
        return combine_on_associative("^", self, field)

    def __invert__(self):
        # Here we account for double negatives to also reduce nesting
        # Not really needed as people are (unlikely) to be putting multiple '~' one after the other
        # But hey you never know
        self_key = next(iter(self.query))
        if self_key == "~":
            return F(**next(iter(self.query[self_key])))  # type: ignore
        else:
            return F(**{"~": [self.query]})
