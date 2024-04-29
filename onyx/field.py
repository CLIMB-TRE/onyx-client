from __future__ import annotations
from typing import Any
from .exceptions import OnyxFieldError


class OnyxOperator:
    AND = "&"
    OR = "|"
    XOR = "^"
    NOT = "~"


class OnyxField:
    """
    Class that represents a single field-value pair for use in Onyx queries.
    """

    __slots__ = "query"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialise a field.

        Args:
            **kwargs: Keyword arguments containing a single key-value pair.

        Notes:
            - Takes a single key-value argument as input.
            - The key corresponds to a field (and optional lookup) to use for filtering.
            - The value corresponds to the field value(s) that are being matched against.
            - `OnyxField` instances can be combined into complex expressions using Python's bitwise operators: `&` (AND), `|` (OR), `^` (XOR), and `~` (NOT).
            - Multi-value lookups (e.g. `in`, `range`) support passing a Python list as the value. These are coerced into comma-separated strings internally.

        Examples:
            Create `OnyxField` objects and combine them using Python bitwise operators:
            ```python
            from onyx import OnyxField

            field1 = OnyxField(field1="value1")
            field2 = OnyxField(field2__contains="value2")

            expression = (field1 | field2) & OnyxField(
                published_date__range=["2023-01-01", "2023-01-02"]
            )
            ```
            ```python
            >>> field1
            <onyx.field.OnyxField object at 0x1028eb850>
            >>> field2
            <onyx.field.OnyxField object at 0x1028eb850>
            >>> expression
            <onyx.field.OnyxField object at 0x103b6fc40>
            >>> field1.query
            {"field1": "value1"}
            >>> field2.query
            {"field2__contains": "value2"}
            >>> expression.query
            {
                "&": [
                    {"|": [{"field1": "value1"}, {"field2__contains": "value2"}]},
                    {"published_date__range": "2023-01-01,2023-01-02"},
                ]
            }
            ```
        """

        if len(kwargs) != 1:
            raise OnyxFieldError(
                f"Expected exactly one field-value pair as a keyword argument. Received: {len(kwargs)}"
            )

        # Get the field-value pair from the kwargs
        field, value = next(iter(kwargs.items()))

        # If the field is not an operation and it is a multi-value lookup
        # Join the values into a comma-separated string
        if field not in {
            OnyxOperator.AND,
            OnyxOperator.OR,
            OnyxOperator.XOR,
            OnyxOperator.NOT,
        }:
            if type(value) in {list, tuple, set}:
                value = ",".join(map(lambda x: str(x) if x is not None else "", value))

        self.query = {field: value}

    def _validate_field(self, field: OnyxField) -> None:
        """
        Ensure an instance with the correct type has been provided.
        """
        if not isinstance(field, OnyxField):
            raise OnyxFieldError(
                f"Expected another instance of the same type. Received: {type(field)}"
            )

    def _combine_on_associative(self, field: OnyxField, operation: str) -> OnyxField:
        """
        Combine two pre-existing queries on an ASSOCIATIVE operation (`AND`, `OR`, `XOR`), and use this to reduce nested JSON.
        E.g. take the following query:

        `((X AND Y) AND Z) OR (W AND (X AND (Y OR (Z OR X))))`

        We can use associativity of `AND` and `OR` to reduce how deeply nested the JSON request body is.
        By associativity of `AND` and `OR`, the following is unambiguous and logically equivalent to the previous query:

        `(X AND Y AND Z) OR (W AND X AND (Y OR Z OR X))`

        With the former corresponding to more deeply-nested JSON than the latter.
        This is useful! There is normally a limit on how deeply nested a JSON request body can be.
        So by preventing unnecessary nesting, users can programatically construct and execute a broader range of queries.
        """

        # For each field, if the topmost key is equal to the current operation, we pull up the values.
        # Otherwise, they stay self-contained within their existing operation.
        # For example, if operation the operation is '&' and we have self = {"&" : [{...}]} and field = {"|" : [{...}]}
        # Then this function would take [{...}] from self, and create [{"|" : [{...}]}] from field
        # And then return {"&" : [{...}] + [{"|" : [{...}]}]} or {"&" : [{...}, {"|" : [{...}]}]}
        self_key, self_value = next(iter(self.query.items()))
        if self_key == operation:
            if not isinstance(self_value, list):
                raise OnyxFieldError(
                    f"Expected associative operation key '{self_key}' to point to a list. Received: {type(self_value)}"
                )
            self_query = self_value
        else:
            self_query = [self.query]

        field_key, field_value = next(iter(field.query.items()))
        if field_key == operation:
            if not isinstance(field_value, list):
                raise OnyxFieldError(
                    f"Expected associative operation key '{field_key}' to point to a list. Received: {type(self_value)}"
                )
            field_query = field_value
        else:
            field_query = [field.query]

        return OnyxField(**{operation: self_query + field_query})

    def __eq__(self, field: OnyxField) -> bool:
        self._validate_field(field)
        return self.query == field.query

    def __and__(self, field: OnyxField) -> OnyxField:
        self._validate_field(field)
        return self._combine_on_associative(field, OnyxOperator.AND)

    def __or__(self, field: OnyxField) -> OnyxField:
        self._validate_field(field)
        return self._combine_on_associative(field, OnyxOperator.OR)

    def __xor__(self, field: OnyxField) -> OnyxField:
        self._validate_field(field)
        return self._combine_on_associative(field, OnyxOperator.XOR)

    def __invert__(self) -> OnyxField:
        # Here we account for double negatives to also reduce nesting
        # Not really needed as people are (unlikely) to be putting multiple negations one after the other
        # But hey you never know

        # Get the top-most key of the current query
        # If its also a NOT, we pull out the value and initialise that as the query
        self_key, self_value = next(iter(self.query.items()))
        if self_key == OnyxOperator.NOT:
            if not isinstance(self_value, dict):
                raise OnyxFieldError(
                    f"Expected operation key '{self_key}' to point to a dict. Received: {type(self_value)}"
                )

            return OnyxField(**self_value)
        else:
            return OnyxField(**{OnyxOperator.NOT: self.query})
