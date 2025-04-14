import posixpath
from .exceptions import OnyxClientError


def handle_endpoint(endpoint, **kwargs):
    for name, val in kwargs.items():
        if val is None or not str(val).strip():
            raise OnyxClientError(f"Argument '{name}' was not provided.")

        val = str(val).strip()

        if name != "domain":
            for char in "/?":
                if char in val:
                    raise OnyxClientError(
                        f"Argument '{name}' contains invalid character: '{char}'."
                    )

            # Crude but effective prevention of unexpectedly calling other endpoints
            # Its not the end of the world if that did happen, but to the user it would be quite confusing
            clashes = {
                "project": ["types", "lookups"],
                "climb_id": [
                    "test",
                    "query",
                    "fields",
                    "choices",
                    "history",
                    "analyses",
                    "identify",
                ],
                "analysis_id": [
                    "test",
                    "fields",
                    "choices",
                    "history",
                    "records",
                ],
            }

            if name in clashes:
                for clash in clashes[name]:
                    if val == clash:
                        raise OnyxClientError(
                            f"Argument '{name}' cannot have value '{val}'. This creates a URL that resolves to a different endpoint."
                        )

    return endpoint()


# TODO: Convert to an enum for argument checking
OnyxEndpoint = {
    "projects": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects/",
        ),
        domain=domain,
    ),
    "types": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects/types/",
        ),
        domain=domain,
    ),
    "lookups": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects/lookups/",
        ),
        domain=domain,
    ),
    "fields": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "fields/",
        ),
        domain=domain,
        project=project,
    ),
    "choices": lambda domain, project, field: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "choices",
            str(field),
            "",
        ),
        domain=domain,
        project=project,
        field=field,
    ),
    "get": lambda domain, project, climb_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            str(climb_id),
            "",
        ),
        domain=domain,
        project=project,
        climb_id=climb_id,
    ),
    "filter": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "",
        ),
        domain=domain,
        project=project,
    ),
    "query": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "query/",
        ),
        domain=domain,
        project=project,
    ),
    "history": lambda domain, project, climb_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "history",
            str(climb_id),
            "",
        ),
        domain=domain,
        project=project,
        climb_id=climb_id,
    ),
    "identify": lambda domain, project, field: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "identify",
            str(field),
            "",
        ),
        domain=domain,
        project=project,
        field=field,
    ),
    "create": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "",
        ),
        domain=domain,
        project=project,
    ),
    "create.test": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "test/",
        ),
        domain=domain,
        project=project,
    ),
    "update": lambda domain, project, climb_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            str(climb_id),
            "",
        ),
        domain=domain,
        project=project,
        climb_id=climb_id,
    ),
    "update.test": lambda domain, project, climb_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "test",
            str(climb_id),
            "",
        ),
        domain=domain,
        project=project,
        climb_id=climb_id,
    ),
    "delete": lambda domain, project, climb_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            str(climb_id),
            "",
        ),
        domain=domain,
        project=project,
        climb_id=climb_id,
    ),
    "analyses": lambda domain, project, climb_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analyses",
            str(climb_id),
            "",
        ),
        domain=domain,
        project=project,
        climb_id=climb_id,
    ),
    "analysis.fields": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/fields/",
        ),
        domain=domain,
        project=project,
    ),
    "analysis.choices": lambda domain, project, field: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/choices",
            str(field),
            "",
        ),
        domain=domain,
        project=project,
        field=field,
    ),
    "analysis.get": lambda domain, project, analysis_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis",
            str(analysis_id),
            "",
        ),
        domain=domain,
        project=project,
        analysis_id=analysis_id,
    ),
    "analysis.filter": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/",
        ),
        domain=domain,
        project=project,
    ),
    "analysis.history": lambda domain, project, analysis_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/history",
            str(analysis_id),
            "",
        ),
        domain=domain,
        project=project,
        analysis_id=analysis_id,
    ),
    "analysis.create": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/",
        ),
        domain=domain,
        project=project,
    ),
    "analysis.create.test": lambda domain, project: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/test/",
        ),
        domain=domain,
        project=project,
    ),
    "analysis.update": lambda domain, project, analysis_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis",
            str(analysis_id),
            "",
        ),
        domain=domain,
        project=project,
        analysis_id=analysis_id,
    ),
    "analysis.update.test": lambda domain, project, analysis_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/test",
            str(analysis_id),
            "",
        ),
        domain=domain,
        project=project,
        analysis_id=analysis_id,
    ),
    "analysis.delete": lambda domain, project, analysis_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis",
            str(analysis_id),
            "",
        ),
        domain=domain,
        project=project,
        analysis_id=analysis_id,
    ),
    "analysis.records": lambda domain, project, analysis_id: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "projects",
            str(project),
            "analysis/records",
            str(analysis_id),
            "",
        ),
        domain=domain,
        project=project,
        analysis_id=analysis_id,
    ),
    "register": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/register/",
        ),
        domain=domain,
    ),
    "login": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/login/",
        ),
        domain=domain,
    ),
    "logout": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/logout/",
        ),
        domain=domain,
    ),
    "logoutall": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/logoutall/",
        ),
        domain=domain,
    ),
    "profile": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/profile/",
        ),
        domain=domain,
    ),
    "activity": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/activity/",
        ),
        domain=domain,
    ),
    "waiting": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/waiting/",
        ),
        domain=domain,
    ),
    "approve": lambda domain, username: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/approve",
            str(username),
            "",
        ),
        domain=domain,
        username=username,
    ),
    "siteusers": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/site/",
        ),
        domain=domain,
    ),
    "allusers": lambda domain: handle_endpoint(
        lambda: posixpath.join(
            str(domain),
            "accounts/all/",
        ),
        domain=domain,
    ),
}
