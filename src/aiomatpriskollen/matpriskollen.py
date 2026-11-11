from aiohttp import ClientError, ClientSession, ClientResponseError
from yarl import URL
import asyncio

# Relative imports kinda scary look into __init__ if there are errors.
from .exceptions import *

class Matpriskollen:
    def __init__(self, session: ClientSession, timeout: int = 10):
        self.session = session
        self.timeout = timeout
    
    async def _request(self, uri: str, params: dict[str, str] | None):
        url = URL("https://matpriskollen.se/").joinpath(uri)
        try: 
            async with asyncio.timeout(self.timeout):
                async with self.session.get(url, params) as response: 
                    response.raise_for_status()
                    return await response.text()
        except TimeoutError as err:
            raise MatpriskollenConnectionError("Timeout talking to Matpriskollen") from err
        except ClientResponseError as err:   
            if err.status == 404 or err.status == 500:
                raise MatpriskollenResponseError(f"{uri} not found") from err
            raise MatpriskollenError(f"Unexpected status {err.status}") from err
        except ClientError as err: 
            raise MatpriskollenConnectionError("Error talking to Matpriskollen") from err


    # Enter "async block" are needed beacuse of the context blocks (with)
    async def __aenter__(self) -> Self:
        return self
    # Exit "async block"
    async def __aexit__(self, *_exc_info: object) -> None:
        await self.close()

    async def getStoresFromPostalcode(self, postalcode: str):
        postalcode = "".join(postalcode.split()) # Remove all space even trailing
        if len(postalcode) != 5 or not postalcode.isdigit():
            raise ValueError(f"Invalid postnummer: {postalcode!r}, expected 5 digits")
        respons_text = await self._request("/api/geo/postal-code", {"postalCode": postalcode}) # params is for /api/geo/postal-code?postalCode=XXXX

    async def getStoresFromCity(self, city: str):
        respons_text = await self._request("/api/geo/local", {"city", city})

    async def getDealsFromStore(self, storeId: str):
        respons_text = await self._request("/api/v1/stores/" + storeId + "/offers")