actor User { 
     permissions = [
          "read", "read_profile"
     ];
     relations = {
          application: Application
     };

     "read" if "member" on "application";
     "read_profile" if is_self(actor, resource);
}
# users are themselves
is_self(user: User, user: User);

actor Group { }

resource Application {
     permissions = ["create_organization"];
     roles = ["member"];

     "create_organization" if "member";
}

# all users default to members of the application
has_role(_user: User, "member", Application{"gitcloud"});

has_relation(_: Resource, "application", Application{"gitclod"});

resource Organization {
     permissions = [
        "read",
        "read_details",
        "view_members",
        "manage_members",
        "set_default_role",
        "create_repositories",
        "delete"
     ];
     roles = ["admin", "member"];
     relations = {
          application: Application
     };

     # everyone can see all organizations
     "read" if "member" on "application";

     "read_details" if "member";
     "view_members" if "member";
     "create_repositories" if "member";

     "member" if "admin";
     "manage_members" if "admin";
     "set_default_role" if "admin";
     "delete" if "admin";
}

resource Repository {
     permissions = [
        "read", "create", "update", "delete",
        "invite", "write",
        "read_issues", "manage_issues",  "create_issues",
        "read_jobs", "manage_jobs",
        "view_members", "manage_members"
     ];
     roles = ["reader", "admin", "maintainer", "editor"];
     relations = { organization: Organization };

     "reader" if "member" on "organization";
     "admin" if "admin" on "organization";
     "reader" if "editor";
     "editor" if "maintainer";
     "maintainer" if "admin";

     "reader" if is_public(resource);

     # reader permissions
     "read" if "reader";
     "read_issues" if "reader";
     "create_issues" if "reader";

     # editor permissions
     "read_jobs" if "editor";
     "write" if "editor";
     "manage_jobs" if "editor";
     "manage_issues" if "editor";
     "view_members" if "maintainer";
     "delete" if "maintainer" and is_protected(resource, false);

     # admin permissions
     "manage_members" if "admin";
     "update" if "admin";
     "delete" if "admin";
     "invite" if "admin" ;
}

resource Issue {
     permissions = ["read", "comment", "close"];
     relations = { repository: Repository, creator: User };

     "read" if "read" on "repository";
     "comment" if "manage_issues" on "repository";
     "close" if "manage_issues" on "repository";

     "close" if "creator";

     "comment" if "read" and is_closed(resource, false);

}

# Policy tests
# Organization members inherit the read permission
# on repositories that belong to the org
# and issues that belong to those repositories
test "organization members can read repos and issues" {
    # Define test data (facts)
    setup {
        # alice is a member of the "acme" organization
        has_role(User{"alice"}, "member", Organization{"acme"});
        # The "test-repo" Repository belongs to the "acme" organization
        has_relation(Repository{"test-repo"}, "organization", Organization{"acme"});
        # The issue "Issue 1" belongs to the "test-repo" repository
        has_relation(Issue{"Issue 1"}, "repository", Repository{"test-repo"});
    }

    # alice can read the "test-repo" Repository
    assert allow(User{"alice"}, "read", Repository{"test-repo"});
    # alice can read the issue "Issue 1"
    assert allow(User{"alice"}, "read", Issue{"Issue 1"});
    # alice can not write to the "test-repo" Repository
    assert_not allow(User{"alice"}, "write", Repository{"test-repo"});
}
