import asyncio

from aiohttp import ClientError, ClientResponseError, ClientSession
from mashumaro.codecs.orjson import ORJSONDecoder
from yarl import URL

from .exceptions import (
    MatpriskollenConnectionError,
    MatpriskollenError,
    MatpriskollenResponseError,
)
from .models import Location, Store

STORES_DECODER = ORJSONDecoder(list[Store])


class Matpriskollen:
    def __init__(self, session: ClientSession, timeout: int = 10):
        # The session is required and owned by the caller (e.g. Home Assistant).
        # Whoever creates the session is responsible for closing it, never us.
        self.session = session
        self.timeout = timeout

    async def _request(self, uri: str, params: dict[str, str] | None = None) -> str:
        url = URL("https://matpriskollen.se/").joinpath(uri)

        try:
            async with asyncio.timeout(self.timeout):
                async with self.session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.text()
        except TimeoutError as err:
            raise MatpriskollenConnectionError("Timeout talking to Matpriskollen") from err
        except ClientResponseError as err:
            if err.status == 404:
                raise MatpriskollenResponseError(f"{uri} not found") from err
            raise MatpriskollenError(f"Unexpected status {err.status} for {uri}") from err
        except ClientError as err:
            raise MatpriskollenConnectionError("Error talking to Matpriskollen") from err

    async def get_stores_near(self, lat: float, lon: float) -> list[Store]:
        # params must be strings, aiohttp raises TypeError on floats
        response_text = await self._request("api/v1/stores", {"lat": str(lat), "lon": str(lon)})
        return STORES_DECODER.decode(response_text)

    async def get_stores_from_postal_code(self, postal_code: str) -> list[Store]:
        postal_code = "".join(postal_code.split())  # Remove all space even trailing
        if len(postal_code) != 5 or not postal_code.isdigit():
            raise ValueError(f"Invalid postnummer: {postal_code!r}, expected 5 digits")
        # params is for api/geo/postal-code?postalCode=XXXXX
        response_text = await self._request("api/geo/postal-code", {"postalCode": postal_code})
        location = Location.from_json(response_text)
        return await self.get_stores_near(location.lat, location.lon)

    # async def get_stores_from_city(self, city: str) -> str:
    #     return await self._request("api/geo/local", {"city": city})

    async def get_deals_from_store(self, store_id: str) -> str:
        response_text = await self._request(f"api/v1/stores/{store_id}/offers")
        

