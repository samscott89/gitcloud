import oso_cloud
from flask import Blueprint, g, jsonify
from typing import cast
from werkzeug.exceptions import NotFound

from ..models import Organization, User, Repository
from ..authorization import oso

bp = Blueprint("users", __name__, url_prefix="/users")


@bp.route("/<username>", methods=["GET"])
def show(username):
    if not oso.authorize(
        {
            "type": "User",
            "id": str(g.current_user),
        },
        "read_profile",
        {"type": "User", "id": username},
    ):
        raise NotFound
    user = g.session.get_or_404(User, username=username)
    return user.as_json()


@bp.route("/<username>/repos", methods=["GET"])
def repo_index(username):
    user = {
        "type": "User",
        "id": str(g.current_user),
    }
    if not oso.authorize(user, "read_profile", {"type": "User", "id": username}):
        raise NotFound

    # get all the repositories that the user has a role for
    repos = oso.query(
        "has_role", {"type": "User", "id": username}, {}, {"type": "Repository"}
    )
    repoIds = list(
        map(lambda fact: cast(oso_cloud.Value, fact["args"][2]).get("id", "_"), repos)
    )
    print(repos, repoIds)
    if "_" in repoIds:
        repo_objs = g.session.query(Repository)
        return jsonify([r.as_json() for r in repo_objs])
    else:
        repo_objs = g.session.query(Repository).filter(Repository.id.in_(repoIds))
        return jsonify([r.as_json() for r in repo_objs])


@bp.route("/<username>/orgs", methods=["GET"])
def org_index(username):
    user = {
        "type": "User",
        "id": str(g.current_user),
    }
    if not oso.authorize(user, "read_profile", {"type": "User", "id": username}):
        raise NotFound

    # get all the repositories that the user has a role for
    orgs = oso.query(
        "has_role", {"type": "User", "id": username}, {}, {"type": "Organization"}
    )
    orgIds = list(
        map(lambda fact: cast(oso_cloud.Value, fact["args"][2]).get("id", "_"), orgs)
    )
    if "_" in orgIds:
        orgs = g.session.query(Organization)
        return jsonify([o.as_json() for o in orgs])
    else:
        orgs = g.session.query(Organization).filter(Organization.id.in_(orgIds))
        return jsonify([o.as_json() for o in orgs])
