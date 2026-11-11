import asyncio

from aiohttp import ClientError, ClientResponseError, ClientSession
from yarl import URL

from .exceptions import (
    MatpriskollenConnectionError,
    MatpriskollenError,
    MatpriskollenResponseError,
)


class Matpriskollen:
    def __init__(self, session: ClientSession, timeout: int = 10):
        # The session is required and owned by the caller (e.g. Home Assistant).
        # Whoever creates the session is responsible for closing it, never us.
        self.session = session
        self.timeout = timeout

    async def _request(self, uri: str, params: dict[str, str] | None = None) -> str:
        # uri must NOT start with "/" joinpath raises ValueError on a leading slash
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

    async def getStoresFromPostalcode(self, postalcode: str) -> str:
        postalcode = "".join(postalcode.split())  # Remove all space even trailing
        if len(postalcode) != 5 or not postalcode.isdigit():
            raise ValueError(f"Invalid postnummer: {postalcode!r}, expected 5 digits")
        # params is for api/geo/postal-code?postalCode=XXXXX
        return await self._request("api/geo/postal-code", {"postalCode": postalcode})

    async def getStoresFromCity(self, city: str) -> str:
        return await self._request("api/geo/local", {"city": city})

    async def getDealsFromStore(self, storeId: str) -> str:
        return await self._request(f"api/v1/stores/{storeId}/offers")
