import asyncio
from typing import Self

from aiohttp import ClientError, ClientResponseError, ClientSession
from yarl import URL

from .exceptions import (
    MatpriskollenConnectionError,
    MatpriskollenError,
    MatpriskollenResponseError,
)


class Matpriskollen:
    def __init__(self, session: ClientSession | None = None, timeout: int = 10):
        # Home Assistant passes in its own session. Without one, we create our own
        # in _request and remember that we own it, so close() only closes ours.
        self.session = session
        self.timeout = timeout
        self._close_session = False

    async def _request(self, uri: str, params: dict[str, str] | None = None) -> str:
        # uri must NOT start with "/", joinpath raises ValueError on a leading slash
        url = URL("https://matpriskollen.se/").joinpath(uri)

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

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

    async def close(self) -> None:
        # Only close a session we created ourselves, never Home Assistant's shared one
        if self.session is not None and self._close_session:
            await self.session.close()

    # Enter "async block" are needed beacuse of the context blocks (with)
    async def __aenter__(self) -> Self:
        return self

    # Exit "async block"
    async def __aexit__(self, *_exc_info: object) -> None:
        await self.close()

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
