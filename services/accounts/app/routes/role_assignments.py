from flask import Blueprint, g, request, jsonify
from typing import cast
from werkzeug.exceptions import Forbidden, NotFound

import oso_cloud
from oso_cloud import Value
from ..models import Organization, Repository, User
from ..authorization import oso

bp = Blueprint("role_assignments", __name__, url_prefix="/orgs/<int:org_id>")


@bp.route("/unassigned_users", methods=["GET"])
def org_unassigned_users_index(org_id):
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    permissions = oso.actions(user, {"type": "Organization", "id": org_id})
    if "read" not in permissions:
        raise NotFound
    elif "view_members" not in permissions:
        raise Forbidden
    existing = oso.get(
        {
            "name": "has_role",
            "args": [{"type": "User"}, None, {"type": "Organization", "id": org_id}],
        }
    )
    existing_users: list[oso_cloud.ValueDict] = [e["args"][0] for e in existing]
    existing_ids = {e["id"] for e in existing_users}  # type: ignore
    unassigned = g.session.query(User).filter(User.id.notin_(existing_ids))
    return jsonify([u.as_json() for u in unassigned])


@bp.route("/role_assignments", methods=["GET"])
def org_index(org_id):
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    permissions = oso.actions(user, {"type": "Organization", "id": org_id})
    if "read" not in permissions:
        raise NotFound
    elif "view_members" not in permissions:
        raise Forbidden

    assignment_facts = oso.get(
        {
            "name": "has_role",
            "args": [{"type": "User"}, None, {"type": "Organization", "id": org_id}],
        }
    )
    assignment_ids = [
        (
            a["args"][0]["id"],  # type: ignore
            a["args"][1]["id"],  # type: ignore
        )
        for a in assignment_facts
    ]
    assignment_ids = sorted(assignment_ids, key=lambda assignment: assignment[0])
    assignments = [
        (g.session.query(User).filter_by(id=user_id).first(), role)
        for (user_id, role) in assignment_ids
    ]
    # TODO(gj): fetch users in bulk
    assignments_json = [
        {
            "user": user.as_json(),
            "role": role,
        }
        for (user, role) in assignments
        if user is not None
    ]
    return jsonify(assignments_json)


@bp.route("/role_assignments", methods=["POST"])
def org_create(org_id):
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    payload = cast(dict, request.get_json(force=True))
    permissions = oso.actions(user, {"type": "Organization", "id": org_id})
    if "read" not in permissions:
        raise NotFound
    elif "manage_members" not in permissions:
        raise Forbidden

    org = g.session.get_or_404(Organization, id=org_id)
    target_user: Value = {"type": "User", "id": payload["id"]}
    if not oso.authorize(user, "read", target_user):
        raise NotFound
    oso.tell({"name": "has_role", "args": [target_user, payload["role"], org]})

    user_obj: User = g.session.get_or_404(User, id=user["id"])
    return {"user": user_obj.as_json(), "role": payload["role"]}, 201  # type: ignore


@bp.route("/role_assignments", methods=["PATCH"])
def org_update(org_id):
    payload = cast(dict, request.get_json(force=True))
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    permissions = oso.actions(user, {"type": "Organization", "id": org_id})
    if "read" not in permissions:
        raise NotFound
    elif "manage_members" not in permissions:
        raise Forbidden
    org = g.session.get_or_404(Organization, id=org_id)
    target_user: Value = {"type": "User", "id": payload["id"]}
    if not oso.authorize(user, "read", target_user):
        raise NotFound

    oso.bulk(
        delete=[{"name": "has_role", "args": [user, None, org]}],
        tell=[{"name": "has_role", "args": [user, payload["role"], org]}],
    )

    user_obj: User = g.session.get_or_404(User, id=user["id"])
    return {"user": user_obj.as_json(), "role": payload["role"]}  # type: ignore


@bp.route("/role_assignments", methods=["DELETE"])
def org_delete(org_id):
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    payload = cast(dict, request.get_json(force=True))
    permissions = oso.actions(user, {"type": "Organization", "id": org_id})
    if "read" not in permissions:
        raise NotFound
    elif "manage_members" not in permissions:
        raise Forbidden
    org = g.session.get_or_404(Organization, id=org_id)
    target_user: Value = {"type": "User", "id": payload["id"]}
    if not oso.authorize(user, "read", target_user):
        raise NotFound

    oso.bulk(delete=[{"name": "has_role", "args": [user, None, org]}])

    return {}, 204


@bp.route("/repos/<int:repo_id>/unassigned_users", methods=["GET"])
def repo_unassigned_users_index(org_id, repo_id):
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    repo = g.session.get_or_404(Repository, id=repo_id, org_id=org_id)
    if not oso.authorize(user, "view_members", repo):
        raise NotFound
    if not oso.authorize(user, "manage_members", repo):
        raise Forbidden
    existing = oso.get(
        {
            "name": "has_role",
            "args": [{"type": User}, None, {"type": "Repository", "id": repo.id}],
        }
    )
    existing_ids = {fact["args"][0]["id"] for fact in existing}  # type: ignore
    unassigned = g.session.query(User).filter(User.id.notin_(existing_ids))
    return jsonify([u.as_json() for u in unassigned])


@bp.route("/repos/<int:repo_id>/role_assignments", methods=["GET"])
def repo_index(org_id, repo_id):
    repo = g.session.get_or_404(Repository, id=repo_id, org_id=org_id)
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    if not oso.authorize(user, "view_members", repo):
        raise Forbidden
    assignment_facts = oso.get(
        {
            "name": "has_role",
            "args": [{"type": "User"}, None, {"type": "Repository", "id": repo_id}],
        }
    )
    assignment_ids = [
        (
            a["args"][0]["id"],  # type: ignore
            a["args"][1]["id"],  # type: ignore
        )
        for a in assignment_facts
    ]
    assignment_ids = sorted(assignment_ids, key=lambda assignment: assignment[0])
    assignments = [
        (g.session.query(User).filter_by(id=user_id).first(), role)
        for (user_id, role) in assignment_ids
    ]
    # TODO(gj): fetch users in bulk
    assignments_json = [
        {
            "user": user.as_json(),
            "role": role,
        }
        for (user, role) in assignments
        if user is not None
    ]
    return jsonify(assignments_json)


@bp.route("/repos/<int:repo_id>/role_assignments", methods=["POST"])
def repo_create(org_id, repo_id):
    payload = cast(dict, request.get_json(force=True))
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    repo = g.session.get_or_404(Repository, id=repo_id, org_id=org_id)
    if not oso.authorize(user, "view_members", repo):
        raise NotFound
    if not oso.authorize(user, "manage_members", repo):
        raise Forbidden
    user: Value = {"type": "User", "id": payload["id"]}
    if not oso.authorize(user, "read", user):
        raise NotFound
    oso.tell({"name": "has_role", "args": [user, payload["role"], repo]})
    user_obj: User = g.session.get_or_404(User, id=user["id"])
    return {"user": user_obj.as_json(), "role": payload["role"]}, 201  # type: ignore


@bp.route("/repos/<int:repo_id>/role_assignments", methods=["PATCH"])
def repo_update(org_id, repo_id):
    payload = cast(dict, request.get_json(force=True))
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    repo = g.session.get_or_404(Repository, id=repo_id, org_id=org_id)
    if not oso.authorize(user, "view_members", repo):
        raise NotFound
    if not oso.authorize(user, "manage_members", repo):
        raise Forbidden
    user: oso_cloud.Value = {"type": "User", "id": str(payload["id"])}

    oso.bulk(
        delete=[{"name": "has_role", "args": [user, None, repo]}],
        tell=[{"name": "has_role", "args": [user, payload["role"], repo]}],
    )

    user_obj = g.session.get_or_404(User, id=user["id"])

    return {"user": user_obj.as_json(), "role": payload["role"]}  # type: ignore


@bp.route("/repos/<int:repo_id>/role_assignments", methods=["DELETE"])
def repo_delete(org_id, repo_id):
    payload = cast(dict, request.get_json(force=True))
    user: Value = {
        "type": "User",
        "id": str(g.current_user),
    }
    repo = g.session.get_or_404(Repository, id=repo_id, org_id=org_id)
    if not oso.authorize(user, "view_members", repo):
        raise NotFound
    if not oso.authorize(user, "manage_members", repo):
        raise Forbidden
    user: oso_cloud.Value = {"type": "User", "id": str(payload["id"])}

    oso.bulk(delete=[{"name": "has_role", "args": [user, None, repo]}])
    return {}, 204
