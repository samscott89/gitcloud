from typing import Any, Type
from sqlalchemy.types import Integer, String, Boolean
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import Session
from sqlalchemy import select, func
from sqlalchemy.orm.relationships import RelationshipProperty
from werkzeug.exceptions import Forbidden, NotFound

Base: Type = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    name = Column(String)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    billing_address = Column(String)

    repos = relationship("Repository")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    description = Column(String(256))

    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    org = relationship(Organization, back_populates="repos")

    public = Column(Boolean, default=False)
    protected = Column(Boolean, default=False)

    unique_name_in_org = UniqueConstraint(name, org_id)


Repository.name_with_owner = column_property(
    select(Organization.name + "/" + Repository.name)
    .filter(Organization.id == Repository.org_id)
    .scalar_subquery()
)


Organization.repository_count = column_property(
    select(func.count(Repository.id))
    .where(Repository.org_id == Organization.id)
    .correlate_except(Repository)
    .scalar_subquery(),
)



# Creates Marshmallow schemas for all models which makes
# it easy to serialize with `as_json`
def setup_schema(base):
    for mapper in base.registry.mappers:
        class_ = mapper.class_
        if hasattr(class_, "__tablename__"):
            columns = []
            for d in mapper.all_orm_descriptors:
                # print(d.__dict__)
                # breakpoint()
                if hasattr(d, "property") and isinstance(
                    d.property, RelationshipProperty
                ):
                    continue
                if hasattr(d, "key"):
                    columns.append(d.key)
                elif hasattr(d, "__name__"):
                    columns.append(d.__name__)
                else:
                    raise Exception("Unable to find column name for %s" % d)

            print(
                "Creating schema for %s" % class_.__name__
                + " with columns %s" % columns
            )
            setattr(class_, "__columns", columns)
            setattr(
                class_,
                "as_json",
                lambda self: {c: getattr(self, c) for c in self.__class__.__columns},
            )


def get_or_raise(self, cls: Type[Any], error, **kwargs):
    resource = self.query(cls).filter_by(**kwargs).one_or_none()
    if resource is None:
        raise error
    return resource


def get_or_403(self, cls: Type[Any], **kwargs):
    return self.get_or_raise(cls, Forbidden, **kwargs)


def get_or_404(self, cls: Type[Any], **kwargs):
    return self.get_or_raise(cls, NotFound, **kwargs)


Session.get_or_404 = get_or_404  # type: ignore
Session.get_or_403 = get_or_403  # type: ignore
Session.get_or_raise = get_or_raise  # type: ignore
