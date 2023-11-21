from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_utils import force_auto_coercion
from sqlalchemy_utils.types.choice import ChoiceType
from sqlalchemy_utils.types.currency import CurrencyType

from app.db import Base
from app.enums import LocationOSMType

force_auto_coercion()


class User(Base):
    user_id = Column(String, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)

    last_used = Column(DateTime(timezone=True))

    created = Column(DateTime(timezone=True), server_default=func.now())

    __tablename__ = "users"


class Location(Base):
    id = Column(Integer, primary_key=True, index=True)

    osm_id = Column(BigInteger)
    osm_type = Column(ChoiceType(LocationOSMType))

    osm_name = Column(String)
    osm_display_name = Column(String)
    osm_address_postcode = Column(String)
    osm_address_city = Column(String)
    osm_address_country = Column(String)
    osm_lat = Column(Numeric(precision=11, scale=7))
    osm_lon = Column(Numeric(precision=11, scale=7))

    prices: Mapped[list["Price"]] = relationship(back_populates="location")

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    __tablename__ = "locations"


class Proof(Base):
    id = Column(Integer, primary_key=True, index=True)

    file_path = Column(String, nullable=False)
    mimetype = Column(String, index=True)

    prices: Mapped[list["Price"]] = relationship(back_populates="proof")

    owner = Column(String, index=True)

    created = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __tablename__ = "proofs"


class Price(Base):
    id = Column(Integer, primary_key=True, index=True)

    product_code = Column(String, index=True)

    price = Column(Numeric(precision=10, scale=2))
    currency = Column(CurrencyType)

    location_osm_id = Column(BigInteger, index=True)
    location_osm_type = Column(ChoiceType(LocationOSMType))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=True)
    location: Mapped[Location] = relationship(back_populates="prices")

    date = Column(Date)

    proof_id: Mapped[int] = mapped_column(ForeignKey("proofs.id"), nullable=True)
    proof: Mapped[Proof] = relationship(back_populates="prices")

    owner = Column(String)

    created = Column(DateTime(timezone=True), server_default=func.now())

    __tablename__ = "prices"
