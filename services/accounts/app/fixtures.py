from collections import OrderedDict
from random import randint
from .models import OrgRole, RepoRole, Organization, Repository, User
from .authorization import oso

from faker import Faker
import faker_microservice

from oso_cloud import Fact

FAKE_USERS = 100
FAKE_ORGANIZATIONS = 10
FAKE_REPOSITORIES = 20
FAKE_ISSUES = 100


def limit_bulk_tell(facts, bulk_limit=20):
    start_index = 0
    end_index = min(len(facts), bulk_limit)
    total_facts_added = 0
    total_number_facts = len(facts)
    while start_index < total_number_facts:
        oso_response = oso.bulk_tell(facts=facts[start_index:end_index])
        if oso_response is not None:
            print(
                "An issue occurred adding facts {} - {})".format(start_index, end_index)
            )
        else:
            total_facts_added += end_index - start_index

        start_index = end_index
        end_index = start_index + min(total_number_facts - start_index, bulk_limit)

    if total_facts_added == total_number_facts:
        print(
            "All {} facts were successfully added to Oso Cloud!".format(
                total_facts_added
            )
        )
    else:
        print(
            "An error occurred. Not all facts were properly uploaded ({} of {}).".format(
                total_facts_added, total_number_facts
            )
        )


def load_fixture_data(session):
    #########
    # Users #
    #########

    faker = Faker()
    Faker.seed(0)
    faker.add_provider(faker_microservice.Provider)
    faker_uniq = faker.unique

    session.query(User).delete()
    session.query(Organization).delete()
    session.query(Repository).delete()

    deletions: list[Fact] = []
    facts: list[Fact] = []

    john = User(username="john", name="John Lennon", email="john@beatles.com")
    paul = User(username="paul", name="Paul McCartney", email="paul@beatles.com")
    george = User(username="george", name="George Harrison", email="george@beatles.com")
    mike = User(username="mike", name="Mike Wazowski", email="mike@monsters.com")
    sully = User(username="sully", name="James P Sullivan", email="sully@monsters.com")
    ringo = User(username="ringo", name="Ringo Starr", email="ringo@beatles.com")
    randall = User(
        username="randall", name="Randall Boggs", email="randall@monsters.com"
    )
    users = [
        john,
        paul,
        george,
        mike,
        sully,
        ringo,
        randall,
    ]

    for _ in range(FAKE_USERS):
        users.append(
            User(
                username=faker_uniq.user_name(),
                name=faker_uniq.name(),
                email=faker_uniq.company_email(),
            )
        )

    for user in users:
        session.add(user)

    ########
    # Orgs #
    ########

    beatles = Organization(
        name="The Beatles",
        description="It's The Beatles",
        billing_address="64 Penny Ln Liverpool, UK",
    )
    monsters = Organization(
        name="Monsters Inc.",
        description="You Won't Believe Your Eye. We Think They Are Scary, But Really We Scare Them!",
        billing_address="123 Scarers Rd Monstropolis, USA",
    )

    orgs = [beatles, monsters]

    for org in orgs:
        session.add(org)

    ########
    # Repos #
    ########

    abbey_road = Repository(
        name="Abbey Road",
        org=beatles,
        description="In the end, the love you take is equal to the love you make",
        public=True,
    )
    paperwork = Repository(
        name="Paperwork",
        org=monsters,
        description="Oh, that darn paperwork! Wouldn't it be easier if it all just blew away?",
    )
    repos = [abbey_road, paperwork]

    for repo in repos:
        session.add(repo)

    ##########
    # Faker  #
    ##########

    for _ in range(FAKE_ORGANIZATIONS):
        org = Organization(
            name=faker_uniq.domain_word(),
            description=faker_uniq.catch_phrase(),
            billing_address=faker_uniq.address(),
        )
        orgs.append(org)
        session.add(org)

        for _ in range(randint(0, FAKE_REPOSITORIES)):
            repo = Repository(
                name=faker_uniq.microservice(),
                org=org,
                description=faker_uniq.bs(),
                public=(randint(0, 10) < 1),
                protected=(randint(0, 20) < 1),
            )
            repos.append(repo)
            session.add(repo)

    # https://github.com/osohq/oso/blob/70965f2277d7167c38d3641140e6e97dec78e3bf/languages/python/sqlalchemy-oso/tests/test_roles.py#L132-L133
    session.flush()
    session.commit()
    # session.close()

    #################
    # Relationships #
    #################

    deletions.append(
        {
            "name": "has_relation",
            "args": [{"type": "Repository"}, "organization", {"type": "Organization"}],
        }
    )

    deletions.append(
        {"name": "is_protected", "args": [{"type": "Repository"}, {"type": "Boolean"}]}
    )
    deletions.append({"name": "is_public", "args": [{"type": "Repository"}]})

    for repo in repos:
        facts.append(
            {
                "name": "has_relation",
                "args": [
                    {"type": "Repository", "id": str(repo.id)},
                    "organization",
                    {"type": "Organization", "id": str(repo.org.id)},
                ],
            }
        )
        facts.append(
            {
                "name": "is_protected",
                "args": [
                    {"type": "Repository", "id": str(repo.id)},
                    {"type": "Boolean", "id": str(repo.protected).lower()},
                ],
            }
        )
        if repo.public:
            facts.append(
                {
                    "name": "is_public",
                    "args": [{"type": "Repository", "id": str(repo.id)}],
                }
            )

    ##############
    # Repo roles #
    ##############

    # repo_roles = [
    #     (john, abbey_road, "reader"),
    #     (paul, abbey_road, "reader"),
    #     (ringo, abbey_road, "maintainer"),
    #     (mike, paperwork, "reader"),
    #     (sully, paperwork, "reader"),
    # ]
    # for (user, repo, role) in repo_roles:
    #     facts.append(["has_role", { "type": "User", "id": user.username }, role, { "type": "Repository", "id": str(repo.id) }])

    #############
    # Org roles #
    #############

    org_roles = [
        OrgRole(user_id=john.id, org_id=beatles.id, role="admin"),
        OrgRole(user_id=paul.id, org_id=beatles.id, role="member"),
        OrgRole(user_id=ringo.id, org_id=beatles.id, role="member"),
        OrgRole(user_id=george.id, org_id=beatles.id, role="member"),
        OrgRole(user_id=mike.id, org_id=monsters.id, role="admin"),
        OrgRole(user_id=sully.id, org_id=monsters.id, role="member"),
        OrgRole(user_id=randall.id, org_id=monsters.id, role="member"),
    ]

    org_role_choices = OrderedDict(
        [
            ("admin", 0.1),
            ("member", 0.9),
        ]
    )

    ### Faker Org Roles
    for org in orgs[2:]:
        # make sure every org has an admin
        admin = faker.random_element(elements=users)
        org_roles.append(OrgRole(user_id=admin.id, org_id=org.id, role="admin"))
        org_users = faker.random_elements(
            elements=users, length=randint(1, 10), unique=True
        )
        for user in org_users:
            org_roles.append(
                OrgRole(
                    user_id=user.id,
                    org_id=org.id,
                    role=faker.random_element(org_role_choices),
                )
            )

    # make sure every user has at least one org
    for user in users:
        org = faker.random_element(orgs)
        role = faker.random_element(org_role_choices)
        org_roles.append(OrgRole(user_id=user.id, org_id=org.id, role=role))

    deletions.append(
        {
            "name": "has_role",
            "args": [{"type": "User"}, {"type": "String"}, {"type": "Organization"}],
        }
    )
    for org_role in org_roles:
        session.add(org_role)
        facts.append(
            {
                "name": "has_role",
                "args": [
                    {"type": "User", "id": str(org_role.user_id)},
                    str(org_role.role),
                    {"type": "Organization", "id": str(org_role.org_id)},
                ],
            }
        )

    repo_roles = []

    repo_role_choices = OrderedDict(
        [
            ("editor", 0.5),
            ("maintainer", 0.5),
        ]
    )
    for repo in repos[2:]:
        repo_users = faker.random_elements(
            elements=users, length=randint(0, 4), unique=True
        )
        for user in repo_users:
            repo_roles.append(
                RepoRole(
                    user_id=user.id,
                    repo_id=repo.id,
                    role=faker.random_element(repo_role_choices),
                )
            )

    deletions.append(
        {
            "name": "has_role",
            "args": [{"type": "User"}, {"type": "String"}, {"type": "Repository"}],
        }
    )
    for repo_role in repo_roles:
        session.add(repo_role)
        facts.append(
            {
                "name": "has_role",
                "args": [
                    {"type": "User", "id": str(repo_role.user_id)},
                    repo_role.role,
                    {"type": "Repository", "id": str(repo_role.repo_id)},
                ],
            }
        )

    # delete old facts
    oso.bulk(deletions, [])

    for idx in range(0, len(facts), 20):
        print(oso.bulk_tell(facts=facts[idx : idx + 20]))

    session.flush()
    session.commit()
