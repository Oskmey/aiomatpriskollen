"Models for Matpriskollen API responses."

from dataclasses import dataclass, field
from datetime import datetime, timezone

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin



def _product_name(product):
    return product["name"]

def _brand(product):
    return product["brand"]  # null for roughly 1 in 8 offers

def _category(product):
    categories = product["categories"]
    return categories[0]["name"] if categories else None

def _date(date):
    return datetime.fromtimestamp(date, tz=timezone.utc)

@dataclass
class Store(DataClassORJSONMixin):
    id: int
    name: str
    uuid: str = field(metadata=field_options(alias="key"))  # This is what is used for offers
    chain_name: str = field(metadata=field_options(alias="chainName"))
    offer_count: int = field(metadata=field_options(alias="offerCount"))
    latitude: float = field(metadata=field_options(alias="lat"))
    longitude: float = field(metadata=field_options(alias="lon"))
    distance: float = field(metadata=field_options(alias="dist", deserialize=float))  # km from the searched point


@dataclass
class Location(DataClassORJSONMixin):
    lat: float
    lon: float

@dataclass
class Offer(DataClassORJSONMixin):
    id: int
    description: str
    price: str
    compare_price: str = field(metadata=field_options(alias="comprice"))
    volume: str
    regular_price: str = field(metadata=field_options(alias="regular"))  # "" when not given
    requires_membership_card: bool = field(metadata=field_options(alias="requiresMembershipCard"))
    product_name: str = field(metadata=field_options(alias="product", deserialize=_product_name))
    brand: str | None = field(metadata=field_options(alias="product", deserialize=_brand))
    category: str | None = field(metadata=field_options(alias="product", deserialize=_category))
    valid_from: datetime | None = field(metadata=field_options(alias="validFrom", deserialize=_date))
    valid_to: datetime | None = field(metadata=field_options(alias="validTo", deserialize=_date))