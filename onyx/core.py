import csv
import functools
import inspect
import requests
from requests import HTTPError, RequestException
from typing import Any, Generator, List, Dict, TextIO, Optional, Union
from .config import OnyxConfig
from .field import OnyxField
from .exceptions import (
    OnyxClientError,
    OnyxConnectionError,
    OnyxRequestError,
    OnyxServerError,
)
from .endpoints import OnyxEndpoint


class OnyxClientBase:
    __slots__ = "config", "_request_handler", "_session"

    def __init__(self, config: OnyxConfig):
        self.config = config
        self._session = None
        self._request_handler = requests.request

    def __enter__(self):
        self._session = requests.Session()
        self._request_handler = self._session.request
        return self

    def __exit__(self, type, value, traceback):
        if self._session:
            self._session.close()
        self._request_handler = requests.request

    def _request(self, method: str, retries: int = 3, **kwargs) -> requests.Response:
        if not retries:
            raise Exception(
                "Request retry limit reached. This should not be possible..."
            )

        kwargs.setdefault("headers", {}).update(
            {"Authorization": f"Token {self.config.token}"}
        )
        method_response = self._request_handler(method, **kwargs)

        # Token has expired or was invalid.
        # If username and password were provided, log in again, obtain a new token, and re-run the method.
        if (
            method_response.status_code == 401
            and self.config.username
            and self.config.password
        ):
            OnyxClientBase.login(self).raise_for_status()
            # A retry mechanism has been incorporated as a failsafe.
            # This is to protect against the case where an onyx endpoint returns a 401 status code,
            # despite the user being able to successfully log in, leading to an infinite loop of
            # re-logging in and re-hitting the endpoint.
            # This scenario should not be possible. But if it happened, it would not be fun at all.
            # So, better safe than sorry...
            return self._request(method, retries=retries - 1, **kwargs)

        return method_response

    def _csv_upload(
        self,
        method: str,
        endpoint: str,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
        climb_id_required: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        # Get appropriate endpoint for test/prod
        if test:
            endpoint += ".test"

        # Create CSV reader
        if delimiter is None:
            reader = csv.DictReader(
                csv_file,
                skipinitialspace=True,
            )
        else:
            reader = csv.DictReader(
                csv_file,
                delimiter=delimiter,
                skipinitialspace=True,
            )

        # Read the first two records (if they exist) and store in 'records' list
        # This is done to protect against two scenarios:
        # - There are no records in the file (never allowed)
        # - There is more than one record, but multiline = False (not allowed)
        records = []

        record_1 = next(reader, None)
        if record_1:
            records.append(record_1)
        else:
            raise OnyxClientError("File must contain at least one record.")

        record_2 = next(reader, None)
        if record_2:
            if not multiline:
                raise OnyxClientError(
                    "File contains multiple records but this is not allowed. To upload multiple records, set 'multiline' = True."
                )
            records.append(record_2)

        # Iterate over the read and unread records and upload sequentially
        for iterator in (records, reader):
            for record in iterator:
                if fields:
                    record = record | fields

                if climb_id_required:
                    # Grab the climb_id, if required for the URL
                    climb_id = record.pop("climb_id", None)
                    if not climb_id:
                        raise OnyxClientError(
                            "Record requires a 'climb_id' for upload."
                        )
                    url = OnyxEndpoint[endpoint](self.config.domain, project, climb_id)
                else:
                    url = OnyxEndpoint[endpoint](self.config.domain, project)

                response = self._request(
                    method=method,
                    url=url,
                    json=record,
                )
                yield response

    def _csv_handle_multiline(
        self,
        responses: Generator[requests.Response, Any, None],
        multiline: bool,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        if multiline:
            results = []
            for response in responses:
                response.raise_for_status()
                results.append(response.json()["data"])
            return results
        else:
            response = next(responses, None)
            if response is None:
                raise OnyxClientError("Iterator must contain at least one record.")

            response.raise_for_status()
            return response.json()["data"]

    def projects(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["projects"](self.config.domain),
        )
        return response

    def types(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["types"](self.config.domain),
        )
        return response

    def lookups(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["lookups"](self.config.domain),
        )
        return response

    def fields(self, project: str, endpoint: str = "fields") -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint[endpoint](self.config.domain, project),
        )
        return response

    def choices(
        self, project: str, field: str, endpoint: str = "choices"
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint[endpoint](self.config.domain, project, field),
        )
        return response

    def get(
        self,
        project: str,
        climb_id: str,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        endpoint: str = "get",
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint[endpoint](self.config.domain, project, climb_id),
            params={"include": include, "exclude": exclude},
        )
        return response

    def filter(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        summarise: Union[List[str], str, None] = None,
        endpoint: str = "filter",
        **kwargs: Any,
    ) -> Generator[requests.Response, Any, None]:
        if fields is None:
            fields = {}

        for field, value in kwargs.items():
            if type(value) in {list, tuple, set}:
                value = ",".join(map(lambda x: str(x) if x is not None else "", value))
            fields[field] = value

        for field, value in fields.items():
            if type(value) in {list, tuple, set}:
                fields[field] = [v if v is not None else "" for v in value]
            if value is None:
                fields[field] = ""

        fields = fields | {
            "include": include,
            "exclude": exclude,
            "summarise": summarise,
        }

        _next = OnyxEndpoint[endpoint](self.config.domain, project)

        while _next is not None:
            response = self._request(
                method="get",
                url=_next,
                params=fields,
            )
            yield response

            fields = None
            if response.ok:
                _next = response.json().get("next")
            else:
                _next = None

    def query(
        self,
        project: str,
        query: Optional[OnyxField] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        summarise: Union[List[str], str, None] = None,
        endpoint: str = "query",
    ) -> Generator[requests.Response, Any, None]:
        if query:
            if not isinstance(query, OnyxField):
                raise OnyxClientError(
                    f"Query must be an instance of {OnyxField}. Received: {type(query)}"
                )
            else:
                query_json = query.query
        else:
            query_json = None

        fields = {
            "include": include,
            "exclude": exclude,
            "summarise": summarise,
        }
        _next = OnyxEndpoint[endpoint](self.config.domain, project)

        while _next is not None:
            response = self._request(
                method="post",
                url=_next,
                json=query_json,
                params=fields,
            )
            yield response

            fields = None
            if response.ok:
                _next = response.json().get("next")
            else:
                _next = None

    @classmethod
    def to_csv(
        cls,
        csv_file: TextIO,
        data: Union[List[Dict[str, Any]], Generator[Dict[str, Any], Any, None]],
        delimiter: Optional[str] = None,
    ):
        # Ensure data is an iterator
        if inspect.isgenerator(data):
            data_iterator = data
        else:
            data_iterator = iter(data)

        row = next(data_iterator, None)
        if row:
            fields = row.keys()

            # Create CSV writer
            if delimiter is None:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fields,
                )
            else:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fields,
                    delimiter=delimiter,
                )

            # Write data
            writer.writeheader()
            writer.writerow(row)
            for row in data_iterator:
                writer.writerow(row)

    def history(
        self,
        project: str,
        climb_id: str,
        endpoint: str = "history",
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint[endpoint](self.config.domain, project, climb_id),
        )
        return response

    def identify(
        self,
        project: str,
        field: str,
        value: str,
        site: Optional[str] = None,
        endpoint="identify",
    ) -> requests.Response:
        identify_json = {"value": value}
        if site:
            identify_json = identify_json | {"site": site}

        response = self._request(
            method="post",
            url=OnyxEndpoint[endpoint](self.config.domain, project, field),
            json=identify_json,
        )
        return response

    def create(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
        endpoint: str = "create",
    ) -> requests.Response:
        if test:
            endpoint += ".test"

        response = self._request(
            method="post",
            url=OnyxEndpoint[endpoint](self.config.domain, project),
            json=fields,
        )
        return response

    def update(
        self,
        project: str,
        climb_id: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
        clear: Union[List[str], str, None] = None,
        endpoint: str = "update",
    ) -> requests.Response:
        if test:
            endpoint += ".test"

        response = self._request(
            method="patch",
            url=OnyxEndpoint[endpoint](self.config.domain, project, climb_id),
            json=fields,
            params={"clear": clear},
        )
        return response

    def delete(
        self,
        project: str,
        climb_id: str,
        endpoint: str = "delete",
    ) -> requests.Response:
        response = self._request(
            method="delete",
            url=OnyxEndpoint[endpoint](self.config.domain, project, climb_id),
        )
        return response

    def csv_create(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="post",
            endpoint="create",
            project=project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
        )

    def csv_update(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="patch",
            endpoint="update",
            project=project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
            climb_id_required=True,
        )

    def csv_delete(
        self,
        project: str,
        csv_file: TextIO,
        delimiter: Optional[str] = None,
        multiline: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="delete",
            endpoint="delete",
            project=project,
            csv_file=csv_file,
            delimiter=delimiter,
            multiline=multiline,
            climb_id_required=True,
        )

    def analyses(
        self,
        project: str,
        climb_id: str,
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["analyses"](self.config.domain, project, climb_id),
        )
        return response

    def analysis_fields(self, project: str) -> requests.Response:
        return OnyxClientBase.fields(
            self,
            project=project,
            endpoint="analysis.fields",
        )

    def analysis_choices(self, project: str, field: str) -> requests.Response:
        return OnyxClientBase.choices(
            self,
            project=project,
            field=field,
            endpoint="analysis.choices",
        )

    def get_analysis(
        self,
        project: str,
        analysis_id: str,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
    ) -> requests.Response:
        return OnyxClientBase.get(
            self,
            project=project,
            climb_id=analysis_id,
            include=include,
            exclude=exclude,
            endpoint="analysis.get",
        )

    def filter_analysis(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        summarise: Union[List[str], str, None] = None,
        **kwargs: Any,
    ) -> Generator[requests.Response, Any, None]:
        return OnyxClientBase.filter(
            self,
            project=project,
            fields=fields,
            include=include,
            exclude=exclude,
            summarise=summarise,
            endpoint="analysis.filter",
            **kwargs,
        )

    def analysis_history(
        self,
        project: str,
        analysis_id: str,
    ) -> requests.Response:
        return OnyxClientBase.history(
            self,
            project=project,
            climb_id=analysis_id,
            endpoint="analysis.history",
        )

    def create_analysis(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> requests.Response:
        return OnyxClientBase.create(
            self,
            project=project,
            fields=fields,
            test=test,
            endpoint="analysis.create",
        )

    def update_analysis(
        self,
        project: str,
        analysis_id: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
        clear: Union[List[str], str, None] = None,
    ) -> requests.Response:
        return OnyxClientBase.update(
            self,
            project=project,
            climb_id=analysis_id,
            fields=fields,
            test=test,
            clear=clear,
            endpoint="analysis.update",
        )

    def delete_analysis(
        self,
        project: str,
        analysis_id: str,
    ) -> requests.Response:
        return OnyxClientBase.delete(
            self,
            project=project,
            climb_id=analysis_id,
            endpoint="analysis.delete",
        )

    def analysis_records(
        self,
        project: str,
        analysis_id: str,
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["analysis.records"](
                self.config.domain, project, analysis_id
            ),
        )
        return response

    @classmethod
    def register(
        cls,
        domain: str,
        first_name: str,
        last_name: str,
        email: str,
        site: str,
        password: str,
    ) -> requests.Response:
        response = requests.post(
            OnyxEndpoint["register"](domain),
            json={
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "email": email,
                "site": site,
            },
        )
        return response

    def login(self) -> requests.Response:
        if self.config.username and self.config.password:
            credentials = (self.config.username, self.config.password)
        else:
            credentials = None

        response = self._request_handler(
            "post",
            auth=credentials,
            url=OnyxEndpoint["login"](self.config.domain),
        )
        if response.ok:
            self.config.token = response.json()["data"]["token"]

        return response

    def logout(self) -> requests.Response:
        response = self._request(
            method="post",
            url=OnyxEndpoint["logout"](self.config.domain),
        )
        if response.ok:
            self.config.token = None

        return response

    def logoutall(self) -> requests.Response:
        response = self._request(
            method="post",
            url=OnyxEndpoint["logoutall"](self.config.domain),
        )
        if response.ok:
            self.config.token = None

        return response

    def profile(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["profile"](self.config.domain),
        )
        return response

    def activity(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["activity"](self.config.domain),
        )
        return response

    def approve(self, username: str) -> requests.Response:
        response = self._request(
            method="patch",
            url=OnyxEndpoint["approve"](self.config.domain, username),
        )
        return response

    def waiting(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["waiting"](self.config.domain),
        )
        return response

    def site_users(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["siteusers"](self.config.domain),
        )
        return response

    def all_users(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxEndpoint["allusers"](self.config.domain),
        )
        return response


def onyx_errors(method):
    """
    Decorator that coerces `requests` library errors into appropriate `OnyxError` subclasses.
    """
    if inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def wrapped_generator_method(self, *args, **kwargs):
            try:
                yield from method(self, *args, **kwargs)

            except HTTPError as e:
                if e.response is None:
                    # TODO: Seems this does not need handling?
                    raise e  #  type: ignore
                elif e.response.status_code < 500:
                    raise OnyxRequestError(str(e), e.response) from e
                else:
                    raise OnyxServerError(str(e), e.response) from e
            except RequestException as e:
                raise OnyxConnectionError(str(e)) from e

        return wrapped_generator_method
    else:

        @functools.wraps(method)
        def wrapped_method(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)

            except HTTPError as e:
                if e.response is None:
                    # TODO: Seems this does not need handling?
                    raise e  #  type: ignore
                elif e.response.status_code < 500:
                    raise OnyxRequestError(str(e), e.response) from e
                else:
                    raise OnyxServerError(str(e), e.response) from e
            except RequestException as e:
                raise OnyxConnectionError(str(e)) from e

        return wrapped_method
