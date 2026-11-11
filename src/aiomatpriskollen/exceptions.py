class MatpriskollenError(Exception):
    "Base error"


class MatpriskollenConnectionError(MatpriskollenError):
    "Raised when communication with the API fails."


class MatpriskollenResponseError(MatpriskollenError):
    "Raised when the API returns an invalid response."


