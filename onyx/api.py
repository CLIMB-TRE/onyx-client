from typing import Any, Generator, List, Dict, TextIO, Optional, Union
from requests.models import Response as Response
from .config import OnyxConfig
from .core import OnyxClientBase, onyx_errors
from .field import OnyxField
from .exceptions import OnyxClientError


class OnyxClient(OnyxClientBase):
    """
    Class for querying and manipulating data within Onyx.
    """

    def __init__(self, config: OnyxConfig) -> None:
        """
        Initialise a client.

        Args:
            config: `OnyxConfig` object that stores information for connecting and authenticating with Onyx.

        Examples:
            The recommended way to initialise a client (as a context manager):
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                pass # Do something with the client here
            ```

            Alternatively, the client can be initialised as follows:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            client = OnyxClient(config)
            # Do something with the client here
            ```

        Tips:
            - When making multiple requests, using the client as a context manager can improve performance.
            - This is due to the fact that the client will re-use the same session for all requests, rather than creating a new session for each request.
            - For more information, see: https://requests.readthedocs.io/en/master/user/advanced/#session-objects
        """
        super().__init__(config)

    @onyx_errors
    def projects(self) -> List[Dict[str, str]]:
        """
        View available projects.

        Returns:
            List of projects.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                projects = client.projects()
            ```
            ```python
            >>> projects
            [
                {
                    "project": "project_1",
                    "scope": "admin",
                    "actions": [
                        "get",
                        "list",
                        "filter",
                        "add",
                        "change",
                        "delete",
                    ],
                },
                {
                    "project": "project_2",
                    "scope": "analyst",
                    "actions": [
                        "get",
                        "list",
                        "filter",
                    ],
                },
            ]
            ```
        """

        response = super().projects()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def types(self) -> List[Dict[str, Any]]:
        """
        View available field types.

        Returns:
            List of field types.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                field_types = client.types()
            ```
            ```python
            >>> field_types
            [
                {
                    "type": "text",
                    "description": "A string of characters.",
                    "lookups": [
                        "exact",
                        "ne",
                        "in",
                        "notin",
                        "contains",
                        "startswith",
                        "endswith",
                        "iexact",
                        "icontains",
                        "istartswith",
                        "iendswith",
                        "length",
                        "length__in",
                        "length__range",
                        "isnull",
                    ],
                },
                {
                    "type": "choice",
                    "description": "A restricted set of options.",
                    "lookups": [
                        "exact",
                        "ne",
                        "in",
                        "notin",
                        "isnull",
                    ],
                },
            ]
            ```
        """

        response = super().types()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def lookups(self) -> List[Dict[str, Any]]:
        """
        View available lookups.

        Returns:
            List of lookups.

        Examples:
            ```python
            import os

            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                lookups = client.lookups()
            ```
            ```python
            >>> lookups
            [
                {
                    "lookup": "exact",
                    "description": "The field's value must be equal to the query value.",
                    "types": [
                        "text",
                        "choice",
                        "integer",
                        "decimal",
                        "date",
                        "datetime",
                        "bool",
                    ],
                },
                {
                    "lookup": "ne",
                    "description": "The field's value must not be equal to the query value.",
                    "types": [
                        "text",
                        "choice",
                        "integer",
                        "decimal",
                        "date",
                        "datetime",
                        "bool",
                    ],
                },
            ]
            ```
        """

        response = super().lookups()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def fields(self, project: str) -> Dict[str, Any]:
        """
        View fields for a project.

        Args:
            project: Name of the project.

        Returns:
            Dict of fields.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                fields = client.fields("project")
            ```
            ```python
            >>> fields
            {
                "name": "Project Name",
                "description": "Project description.",
                "object_type": "records",
                "version": "0.1.0",
                "fields": {
                    "climb_id": {
                        "description": "Unique identifier for a project record in Onyx.",
                        "type": "text",
                        "required": True,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                        ],
                        "restrictions": [
                            "Max length: 12",
                        ],
                    },
                    "is_published": {
                        "description": "Indicator for whether a project record has been published.",
                        "type": "bool",
                        "required": False,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                            "add",
                            "change",
                        ],
                        "default": True,
                    },
                    "published_date": {
                        "description": "The date the project record was published in Onyx.",
                        "type": "date (YYYY-MM-DD)",
                        "required": False,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                        ],
                    },
                    "country": {
                        "description": "Country of origin.",
                        "type": "choice",
                        "required": False,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                            "add",
                            "change",
                        ],
                        "values": [
                            "ENG",
                            "WALES",
                            "SCOT",
                            "NI",
                        ],
                    },
                },
            }
            ```
        """

        response = super().fields(project)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def choices(self, project: str, field: str) -> Dict[str, Dict[str, Any]]:
        """
        View choices for a field.

        Args:
            project: Name of the project.
            field: Choice field on the project.

        Returns:
            Dictionary mapping choices to information about the choice.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                choices = client.choices("project", "country")
            ```
            ```python
            >>> choices
            {
                "ENG": {
                    "description": "England",
                    "is_active" : True,
                },
                "WALES": {
                    "description": "Wales",
                    "is_active" : True,
                },
                "SCOT": {
                    "description": "Scotland",
                    "is_active" : True,
                },
                "NI": {
                    "description": "Northern Ireland",
                    "is_active" : True,
                },
            }
            ```
        """

        response = super().choices(project, field)
        response.raise_for_status()
        return response.json()["data"]

    def _handle_get(
        self,
        project: str,
        object_name: str,
        get_method_name: str,
        filter_method_name: str,
        id_field: str,
        id_value: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        if id_value and fields:
            raise OnyxClientError(f"Cannot provide both '{id_field}' and 'fields'.")

        if not (id_value or fields):
            raise OnyxClientError(f"Must provide either '{id_field}' or 'fields'.")

        if not id_value:
            responses = getattr(super(), filter_method_name)(
                project,
                fields=fields,
                include=[id_field],
            )
            response = next(responses, None)
            if response is None:
                raise OnyxClientError(
                    f"Expected one {object_name} to be returned but received no response."
                )

            response.raise_for_status()
            count = len(response.json()["data"])
            if count != 1:
                raise OnyxClientError(
                    f"Expected one {object_name} to be returned but received: {count}"
                )
            id_value = response.json()["data"][0][id_field]

        response = getattr(super(), get_method_name)(
            **{
                "project": project,
                id_field: id_value,
                "include": include,
                "exclude": exclude,
            }
        )
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def get(
        self,
        project: str,
        climb_id: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        Get a record from a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record.
            fields: Dictionary of field filters used to uniquely identify the record.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.

        Returns:
            Dict containing the record.

        Examples:
            Get a record by CLIMB ID:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                record = client.get("project", "C-1234567890")
            ```
            ```python
            >>> record
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
                "field2": "value2",
            }
            ```

            Get a record by fields that uniquely identify it:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                record = client.get(
                    "project",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                    },
                )
            ```
            ```python
            >>> record
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
                "field2": "value2",
            }
            ```

            The `include` and `exclude` arguments can be used to control the fields returned:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                record_v1 = client.get(
                    "project",
                    climb_id="C-1234567890",
                    include=["climb_id", "published_date"],
                )
                record_v2 = client.get(
                    "project",
                    climb_id="C-1234567890",
                    exclude=["field2"],
                )
            ```
            ```python
            >>> record_v1
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
            }
            >>> record_v2
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
            }
            ```

        Tips:
            - Including/excluding fields to reduce the size of the returned data can improve performance.
        """

        return self._handle_get(
            project=project,
            object_name="record",
            get_method_name="get",
            filter_method_name="filter",
            id_field="climb_id",
            id_value=climb_id,
            fields=fields,
            include=include,
            exclude=exclude,
        )

    @onyx_errors
    def filter(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        summarise: Union[List[str], str, None] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Filter records from a project.

        Args:
            project: Name of the project.
            fields: Dictionary of field filters.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            summarise: For a given field (or group of fields), return the frequency of each unique value (or unique group of values).
            **kwargs: Additional keyword arguments are interpreted as field filters.

        Returns:
            Generator of records. If a summarise argument is provided, each record will be a dict containing values of the summary fields and a count for the frequency.

        Notes:
            - Field filters specify requirements that the returned data must satisfy. They can be provided as keyword arguments, or as a dictionary to the `fields` argument.
            - These filters can be a simple match on a value (e.g. `"published_date" : "2023-01-01"`), or they can use a 'lookup' for more complex matching conditions (e.g. `"published_date__iso_year" : "2023"`).
            - Multi-value lookups (e.g. `in`, `range`) can also be used. For keyword arguments, multiple values can be provided as a Python list. For the `fields` dictionary, multiple values must be provided as a comma-separated string (see examples below).

        Examples:
            Retrieve all records that match a set of field requirements:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            # Field conditions can either be provided as keyword arguments:
            with OnyxClient(config) as client:
                records = list(
                    client.filter(
                        project="project",
                        field1="abcd",
                        published_date__range=["2023-01-01", "2023-01-02"],
                    )
                )

            # Or as a dictionary to the 'fields' argument:
            with OnyxClient(config) as client:
                records = list(
                    client.filter(
                        project="project",
                        fields={
                            "field1": "abcd",
                            "published_date__range" : "2023-01-01, 2023-01-02",
                        },
                    )
                )
            ```
            ```python
            >>> records
            [
                {
                    "climb_id": "C-1234567890",
                    "published_date": "2023-01-01",
                    "field1": "abcd",
                    "field2": 123,
                },
                {
                    "climb_id": "C-1234567891",
                    "published_date": "2023-01-02",
                    "field1": "abcd",
                    "field2": 456,
                },
            ]
            ```

            The `summarise` argument can be used to return the frequency of each unique value for a given field, or the frequency of each unique set of values for a group of fields:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                records_v1 = list(
                    client.filter(
                        project="project",
                        field1="abcd",
                        published_date__range=["2023-01-01", "2023-01-02"],
                        summarise="published_date",
                    )
                )

                records_v2 = list(
                    client.filter(
                        project="project",
                        field1="abcd",
                        published_date__range=["2023-01-01", "2023-01-02"],
                        summarise=["published_date", "field2"],
                    )
                )
            ```
            ```python
            >>> records_v1
            [
                {
                    "published_date": "2023-01-01",
                    "count": 1,
                },
                {
                    "published_date": "2023-01-02",
                    "count": 1,
                },
            ]
            >>> records_v2
            [
                {
                    "published_date": "2023-01-01",
                    "field2": 123,
                    "count": 1,
                },
                {
                    "published_date": "2023-01-02",
                    "field2": 456,
                    "count": 1,
                },
            ]
            ```
        """

        responses = super().filter(
            project,
            fields=fields,
            include=include,
            exclude=exclude,
            summarise=summarise,
            **kwargs,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @onyx_errors
    def query(
        self,
        project: str,
        query: Optional[OnyxField] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        summarise: Union[List[str], str, None] = None,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Query records from a project.

        This method supports more complex filtering than the `OnyxClient.filter` method.
        Here, filters can be combined using Python's bitwise operators, representing AND, OR, XOR and NOT operations.

        Args:
            project: Name of the project.
            query: `OnyxField` object representing the query being made.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            summarise: For a given field (or group of fields), return the frequency of each unique value (or unique group of values).

        Returns:
            Generator of records. If a summarise argument is provided, each record will be a dict containing values of the summary fields and a count for the frequency.

        Notes:
            - The `query` argument must be an instance of `OnyxField`.
            - `OnyxField` instances can be combined into complex expressions using Python's bitwise operators: `&` (AND), `|` (OR), `^` (XOR), and `~` (NOT).
            - Multi-value lookups (e.g. `in`, `range`) support passing a Python list (see example below).

        Examples:
            Retrieve all records that match the query provided by an `OnyxField` object:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient, OnyxField

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                records = list(
                    client.query(
                        project="project",
                        query=(
                            OnyxField(field1="abcd")
                            & OnyxField(published_date__range=["2023-01-01", "2023-01-02"])
                        ),
                    )
                )
            ```
            ```python
            >>> records
            [
                {
                    "climb_id": "C-1234567890",
                    "published_date": "2023-01-01",
                    "field1": "abcd",
                    "field2": 123,
                },
                {
                    "climb_id": "C-1234567891",
                    "published_date": "2023-01-02",
                    "field1": "abcd",
                    "field2": 456,
                },
            ]
            ```
        """

        responses = super().query(
            project,
            query=query,
            include=include,
            exclude=exclude,
            summarise=summarise,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @classmethod
    @onyx_errors
    def to_csv(
        cls,
        csv_file: TextIO,
        data: Union[List[Dict[str, Any]], Generator[Dict[str, Any], Any, None]],
        delimiter: Optional[str] = None,
    ):
        """
        Write a set of records to a CSV file.

        Args:
            csv_file: File object for the CSV file being written to.
            data: The data being written to the CSV file. Must be either a list / generator of dict records.
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                client.to_csv(
                    csv_file=csv_file,
                    data=client.filter(
                        "project",
                        fields={
                            "field1": "value1",
                            "field2": "value2",
                        },
                )
            ```
        """
        super().to_csv(
            csv_file=csv_file,
            data=data,
            delimiter=delimiter,
        )

    @onyx_errors
    def history(
        self,
        project: str,
        climb_id: str,
    ) -> Dict[str, Any]:
        """
        View the history of a record in a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record.

        Returns:
            Dict containing the history of the record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                history = client.history("project", "C-1234567890")
            ```
            ```python
            >>> history
            {
                "climb_id": "C-1234567890",
                "history": [
                    {
                        "username": "user",
                        "timestamp": "2023-01-01T00:00:00Z",
                        "action": "add",
                    },
                    {
                        "username": "user",
                        "timestamp": "2023-01-02T00:00:00Z",
                        "action": "change",
                        "changes": [
                            {
                                "field": "field_1",
                                "type": "text",
                                "from": "value1",
                                "to": "value2",
                            },
                            {
                                "field": "field_2",
                                "type": "integer",
                                "from": 3,
                                "to": 4,
                            },
                            {
                                "field": "nested_field",
                                "type": "relation",
                                "action": "add",
                                "count" : 3,
                            },
                            {
                                "field": "nested_field",
                                "type": "relation",
                                "action": "change",
                                "count" : 10,
                            },
                        ],
                    },
                ],
            }
            ```
        """
        response = super().history(project, climb_id)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def analyses(self, project: str, climb_id: str) -> List[Dict[str, Any]]:
        """
        View the analyses of a record in a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record.

        Returns:
            List of Dicts containing basic details of each analysis of the record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                analyses = client.analyses("project", "C-1234567890")
            ```
            ```python
            >>> analyses
            [
                {
                    "analysis_id": "A-1234567890",
                    "published_date": "2023-02-01",
                    "analysis_date": "2023-01-01",
                    "site": "site",
                    "name": "First Analysis",
                    "report": "s3://analysis_1.html",
                    "outputs": "s3://analysis_1_outputs/",
                },
                {
                    "analysis_id": "A-0987654321",
                    "published_date": "2024-02-01",
                    "analysis_date": "2023-01-01",
                    "site": "site",
                    "name": "Second Analysis",
                    "report": "s3://analysis_2.html",
                    "outputs": "s3://analysis_2_outputs/",
                },
            ]
            ```
        """
        response = super().analyses(project, climb_id)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def identify(
        self,
        project: str,
        field: str,
        value: str,
        site: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get the anonymised identifier for a value on a field.

        Args:
            project: Name of the project.
            field: Field on the project.
            value: Value to identify.
            site: Site to identify the value on. If not provided, defaults to the user's site.

        Returns:
            Dict containing the project, site, field, value and anonymised identifier.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                identification = client.identify("project", "sample_id", "hidden-value")
            ```
            ```python
            >>> identification
            {
                "project": "project",
                "site": "site",
                "field": "sample_id",
                "value": "hidden-value",
                "identifier": "S-1234567890",
            }
            ```
        """

        response = super().identify(project, field, value, site=site)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def create(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a record in a project.

        Args:
            project: Name of the project.
            fields: Object representing the record to be created.
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the created record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.create(
                    "project",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                    },
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```
        """

        response = super().create(project, fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def update(
        self,
        project: str,
        climb_id: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
        clear: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        Update a record in a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record.
            fields: Object representing the record to be updated.
            test: If `True`, runs the command as a test. Default: `False`
            clear: List of fields to be cleared. Overrides any values provided in `fields`.

        Returns:
            Dict containing the CLIMB ID of the updated record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.update(
                    project="project",
                    climb_id="C-1234567890",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                    },
                    clear=["field3", "field4"],
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```
        """

        response = super().update(
            project,
            climb_id,
            fields=fields,
            test=test,
            clear=clear,
        )
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def delete(
        self,
        project: str,
        climb_id: str,
    ) -> Dict[str, Any]:
        """
        Delete a record in a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record.

        Returns:
            Dict containing the CLIMB ID of the deleted record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.delete(
                    project="project",
                    climb_id="C-1234567890",
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```
        """

        response = super().delete(project, climb_id)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def csv_create(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Use a CSV file to create record(s) in a project.

        Args:
            project: Name of the project.
            csv_file: File object for the CSV file being used for record upload.
            fields: Additional fields provided for each record being uploaded. Takes precedence over fields in the CSV.
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.
            multiline: If `True`, allows processing of CSV files with more than one record. Default: `False`
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the created record. If `multiline = True`, returns a list of dicts containing the CLIMB ID of each created record.

        Examples:
            Create a single record:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                result = client.csv_create(
                    project="project",
                    csv_file=csv_file,
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```

            Create multiple records:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                results = client.csv_create(
                    project="project",
                    csv_file=csv_file,
                    multiline=True,
                )
            ```
            ```python
            >>> results
            [
                {"climb_id": "C-1234567890"},
                {"climb_id": "C-1234567891"},
                {"climb_id": "C-1234567892"},
            ]
            ```
        """

        responses = super().csv_create(
            project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
        )
        return self._csv_handle_multiline(responses, multiline)

    @onyx_errors
    def csv_update(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Use a CSV file to update record(s) in a project.

        Args:
            project: Name of the project.
            csv_file: File object for the CSV file being used for record upload.
            fields: Additional fields provided for each record being uploaded. Takes precedence over fields in the CSV.
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.
            multiline: If `True`, allows processing of CSV files with more than one record. Default: `False`
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the updated record. If `multiline = True`, returns a list of dicts containing the CLIMB ID of each updated record.

        Examples:
            Update a single record:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                result = client.csv_update(
                    project="project",
                    csv_file=csv_file,
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```

            Update multiple records:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                results = client.csv_update(
                    project="project",
                    csv_file=csv_file,
                    multiline=True,
                )
            ```
            ```python
            >>> results
            [
                {"climb_id": "C-1234567890"},
                {"climb_id": "C-1234567891"},
                {"climb_id": "C-1234567892"},
            ]
            ```
        """

        responses = super().csv_update(
            project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
        )
        return self._csv_handle_multiline(responses, multiline)

    @onyx_errors
    def csv_delete(
        self,
        project: str,
        csv_file: TextIO,
        delimiter: Optional[str] = None,
        multiline: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Use a CSV file to delete record(s) in a project.

        Args:
            project: Name of the project.
            csv_file: File object for the CSV file being used for record upload.
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.
            multiline: If `True`, allows processing of CSV files with more than one record. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the deleted record. If `multiline = True`, returns a list of dicts containing the CLIMB ID of each deleted record.

        Examples:
            Delete a single record:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                result = client.csv_delete(
                    project="project",
                    csv_file=csv_file,
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```

            Delete multiple records:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                results = client.csv_delete(
                    project="project",
                    csv_file=csv_file,
                    multiline=True,
                )
            ```
            ```python
            >>> results
            [
                {"climb_id": "C-1234567890"},
                {"climb_id": "C-1234567891"},
                {"climb_id": "C-1234567892"},
            ]
            ```
        """

        responses = super().csv_delete(
            project,
            csv_file=csv_file,
            delimiter=delimiter,
            multiline=multiline,
        )
        return self._csv_handle_multiline(responses, multiline)

    @onyx_errors
    def analysis_fields(self, project: str) -> Dict[str, Any]:
        """
        View analysis fields.

        Args:
            project: Name of the project.

        Returns:
            Dict of fields.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                fields = client.analysis_fields("project")
            ```
        """

        response = super().analysis_fields(project)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def analysis_choices(self, project: str, field: str) -> Dict[str, Dict[str, Any]]:
        """
        View choices for an analysis field.

        Args:
            project: Name of the project.
            field: Analysis choice field.

        Returns:
            Dictionary mapping choices to information about the choice.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                choices = client.analysis_choices("project", "country")
            ```
        """

        response = super().analysis_choices(project, field)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def get_analysis(
        self,
        project: str,
        analysis_id: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        Get an analysis from a project.

        Args:
            project: Name of the project.
            analysis_id: Unique identifier for the analysis.
            fields: Dictionary of field filters used to uniquely identify the record.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.

        Returns:
            Dict containing the record.

        Examples:
            Get an analysis by analysis ID:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                analysis = client.get_analysis("project", "A-1234567890")
            ```
            ```python
            >>> analysis
            {
                "analysis_id": "A-1234567890",
                "published_date": "2023-01-01",
                "name": "Very cool analysis",
                "result": "Found very cool things",
            }
            ```
        """

        return self._handle_get(
            project=project,
            object_name="analysis",
            get_method_name="get_analysis",
            filter_method_name="filter_analysis",
            id_field="analysis_id",
            id_value=analysis_id,
            fields=fields,
            include=include,
            exclude=exclude,
        )

    @onyx_errors
    def filter_analysis(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        summarise: Union[List[str], str, None] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Filter analyses from a project.

        Args:
            project: Name of the project.
            fields: Dictionary of field filters.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            summarise: For a given field (or group of fields), return the frequency of each unique value (or unique group of values).
            **kwargs: Additional keyword arguments are interpreted as field filters.

        Returns:
            Generator of analyses. If a summarise argument is provided, each record will be a dict containing values of the summary fields and a count for the frequency.

        Examples:
            Retrieve all analyses that match a set of field requirements:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                analyses = list(
                    client.filter_analysis(
                        project="project",
                        published_date__range=["2023-01-01", "2023-01-02"],
                    )
                )
            ```
            ```python
            >>> analyses
            [
                {
                    "analysis_id": "A-1234567890",
                    "published_date": "2023-01-01",
                    "name": "Very cool analysis",
                    "result": "Found very cool things",
                },
                {
                    "analysis_id": "A-1234567891",
                    "published_date": "2023-01-02",
                    "name": "Not so cool analysis",
                    "result": "Found not so cool things",
                },
            ]
            ```

        Tips:
            - See the documentation for the `filter` method for more information on filtering records, as this also applies to analyses.
        """

        responses = super().filter_analysis(
            project,
            fields=fields,
            include=include,
            exclude=exclude,
            summarise=summarise,
            **kwargs,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @onyx_errors
    def analysis_history(
        self,
        project: str,
        analysis_id: str,
    ) -> Dict[str, Any]:
        """
        View the history of an analysis in a project.

        Args:
            project: Name of the project.
            analysis_id: Unique identifier for the analysis.

        Returns:
            Dict containing the history of the analysis.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                history = client.analysis_history("project", "A-1234567890")
            ```
            ```python
            >>> history
            {
                "analysis_id": "A-1234567890",
                "history": [
                    {
                        "username": "user",
                        "timestamp": "2023-01-01T00:00:00Z",
                        "action": "add",
                    },
                    {
                        "username": "user",
                        "timestamp": "2023-01-02T00:00:00Z",
                        "action": "change",
                        "changes": [
                            {
                                "field": "name",
                                "type": "text",
                                "from": "Cool analysis",
                                "to": "Very cool analysis",
                            },
                        ],
                    },
                ],
            }
            ```
        """
        response = super().analysis_history(project, analysis_id)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def analysis_records(self, project: str, analysis_id: str) -> List[Dict[str, Any]]:
        """
        View the records involved in an analysis in a project.

        Args:
            project: Name of the project.
            analysis_id: Unique identifier for the analysis.

        Returns:
            List of Dicts containing basic details of each record involved in the analysis.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                records = client.analysis_records("project", "A-1234567890")
            ```
            ```python
            >>> records
            [
                {
                    "climb_id": "C-1234567890",
                    "published_date": "2023-01-01",
                    "site": "site_1",
                },
                {
                    "climb_id": "C-1234567891",
                    "published_date": "2023-01-02",
                    "site": "site_2",
                },
            ]
            ```
        """

        response = super().analysis_records(project, analysis_id)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def create_analysis(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Create an analysis in a project.

        Args:
            project: Name of the project.
            fields: Object representing the analysis to be created.
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the Analysis ID of the created analysis.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.create_analysis(
                    "project",
                    fields={
                        "name": "Absolutely incredible analysis",
                        "result": "Insane results",
                    },
                )
            ```
            ```python
            >>> result
            {"analysis_id": "A-1234567890"}
            ```
        """

        response = super().create_analysis(project, fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def update_analysis(
        self,
        project: str,
        analysis_id: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
        clear: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        Update an analysis in a project.

        Args:
            project: Name of the project.
            analysis_id: Unique identifier for the analysis.
            fields: Object representing the analysis to be updated.
            test: If `True`, runs the command as a test. Default: `False`
            clear: List of fields to be cleared. Overrides any values provided in `fields`.

        Returns:
            Dict containing the Analysis ID of the updated analysis.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.update_analysis(
                    project="project",
                    analysis_id="A-1234567890",
                    fields={
                        "result": "The results were even more insane",
                    },
                    clear=["report"],
                )
            ```
            ```python
            >>> result
            {"analysis_id": "A-1234567890"}
            ```
        """

        response = super().update_analysis(
            project,
            analysis_id,
            fields=fields,
            test=test,
            clear=clear,
        )
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def delete_analysis(
        self,
        project: str,
        analysis_id: str,
    ) -> Dict[str, Any]:
        """
        Delete an analysis in a project.

        Args:
            project: Name of the project.
            analysis_id: Unique identifier for the analysis.

        Returns:
            Dict containing the Analysis ID of the deleted analysis.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.delete_analysis(
                    project="project",
                    analysis_id="A-1234567890",
                )
            ```
            ```python
            >>> result
            {"analysis_id": "A-1234567890"}
            ```
        """

        response = super().delete_analysis(project, analysis_id)
        response.raise_for_status()
        return response.json()["data"]

    @classmethod
    @onyx_errors
    def register(
        cls,
        domain: str,
        first_name: str,
        last_name: str,
        email: str,
        site: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            domain: Name of the domain.
            first_name: First name of the user.
            last_name: Last name of the user.
            email: Email address of the user.
            site: Name of the site.
            password: Password for the user.

        Returns:
            Dict containing the user's information.

        Examples:
            ```python
            import os
            from onyx import OnyxClient, OnyxEnv

            registration = OnyxClient.register(
                domain=os.environ[OnyxEnv.DOMAIN],
                first_name="Bill",
                last_name="Will",
                email="bill@email.com",
                site="site",
                password="pass123",
            )
            ```
            ```python
            >>> registration
            {
                "username": "onyx-willb",
                "site": "site",
                "email": "bill@email.com",
                "first_name": "Bill",
                "last_name": "Will",
            }
            ```
        """
        response = super().register(
            domain,
            first_name,
            last_name,
            email,
            site,
            password,
        )
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def login(self) -> Dict[str, Any]:
        """
        Log in the user.

        Returns:
            Dict containing the user's authentication token and it's expiry.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                username=os.environ[OnyxEnv.USERNAME],
                password=os.environ[OnyxEnv.PASSWORD],
            )

            with OnyxClient(config) as client:
                token = client.login()
            ```
            ```python
            >>> token
            {
                "expiry": "2024-01-01T00:00:00.000000Z",
                "token": "abc123",
            }
            ```
        """

        response = super().login()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def logout(self) -> None:
        """
        Log out the user.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                client.logout()
            ```
        """

        response = super().logout()
        response.raise_for_status()

    @onyx_errors
    def logoutall(self) -> None:
        """
        Log out the user in all clients.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                client.logoutall()
            ```
        """

        response = super().logoutall()
        response.raise_for_status()

    @onyx_errors
    def profile(self) -> Dict[str, str]:
        """
        View the user's information.

        Returns:
            Dict containing the user's information.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                profile = client.profile()
            ```
            ```python
            >>> profile
            {
                "username": "user",
                "site": "site",
                "email": "user@email.com",
            }
            ```
        """

        response = super().profile()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def activity(self) -> List[Dict[str, Any]]:
        """
        View the user's latest activity.

        Returns:
            List of the user's latest activity.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                activity = client.activity()
            ```
            ```python
            >>> activity
            [
                {
                    "date": "2023-01-01T00:00:00.000000Z",
                    "address": "127.0.0.1",
                    "endpoint": "/projects/project/",
                    "method": "POST",
                    "status": 400,
                    "exec_time": 29,
                    "error_messages" : "b'{\"status\":\"fail\",\"code\":400,\"messages\":{\"site\":[\"Select a valid choice.\"]}}'",
                },
                {
                    "timestamp": "2023-01-02T00:00:00.000000Z",
                    "address": "127.0.0.1",
                    "endpoint": "/accounts/activity/",
                    "method": "GET",
                    "status": 200,
                    "exec_time": 22,
                    "error_messages": "",
                },
            ]
            ```
        """

        response = super().activity()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def approve(self, username: str) -> Dict[str, Any]:
        """
        Approve another user.

        Args:
            username: Username of the user to be approved.

        Returns:
            Dict confirming user approval success.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                approval = client.approve("waiting_user")
            ```
            ```python
            >>> approval
            {
                "username": "waiting_user",
                "is_approved": True,
            }
            ```
        """

        response = super().approve(username)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def waiting(self) -> List[Dict[str, Any]]:
        """
        Get users waiting for approval.

        Returns:
            List of users waiting for approval.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                users = client.waiting()
            ```
            ```python
            >>> users
            [
                {
                    "username": "waiting_user",
                    "site": "site",
                    "email": "waiting_user@email.com",
                    "date_joined": "2023-01-01T00:00:00.000000Z",
                }
            ]
            ```
        """

        response = super().waiting()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def site_users(self) -> List[Dict[str, Any]]:
        """
        Get users within the site of the requesting user.

        Returns:
            List of users within the site of the requesting user.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config):
                users = client.site_users()
            ```
            ```python
            >>> users
            [
                {
                    "username": "user",
                    "site": "site",
                    "email": "user@email.com",
                }
            ]
            ```
        """

        response = super().site_users()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.

        Returns:
            List of all users.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                users = client.all_users()
            ```
            ```python
            >>> users
            [
                {
                    "username": "user",
                    "site": "site",
                    "email": "user@email.com",
                },
                {
                    "username": "another_user",
                    "site": "another_site",
                    "email": "another_user@email.com",
                },
            ]
            ```
        """

        response = super().all_users()
        response.raise_for_status()
        return response.json()["data"]
