from requests import HTTPError


class QuotaExceededError(HTTPError):
    """
    A 429 response that is a quota, not a rate limit: retrying soon will not help, so it is raised instead of retried.

    Subclasses ``requests.HTTPError``, so existing ``except HTTPError`` handlers still catch it.
    """

    def __init__(self, message: str, *, response=None, body: dict | None = None):
        super().__init__(message, response=response)
        self.body = body or {}
        retry_after = response.headers.get("Retry-After") if response is not None else None
        self.retry_after: int | None = int(retry_after) if retry_after and retry_after.isdigit() else None


class DailyDownloadLimitError(QuotaExceededError):
    """
    The daily limit on downloading replay files uploaded by other people is reached.
    It resets at 00:00 UTC (``reset``); your own replays are not limited.
    """

    def __init__(self, message: str, *, response=None, body: dict | None = None):
        super().__init__(message, response=response, body=body)
        self.limit: int | None = self.body.get("limit")
        self.count: int | None = self.body.get("count")
        self.reset: str | None = self.body.get("reset")


class UploadQuotaError(QuotaExceededError):
    """The account reached its upload quota for the ``window`` ("day" or "week")."""

    def __init__(self, message: str, *, response=None, body: dict | None = None):
        super().__init__(message, response=response, body=body)
        self.max_uploads: int | None = self.body.get("max_uploads")
        self.window: str | None = self.body.get("window")


class AccountRestrictedError(HTTPError):
    """
    A 403 for a restriction ballchasing put on the account (``code``). Do not retry while it is active.

    - ``account_banned``: every API call is refused, uploads included.
    - ``api_access_blocked``: reads are refused (except the ping); writes and uploads still work.
    - ``files_suspended``: replay files uploaded by other players are refused; your own still download.

    Subclasses ``requests.HTTPError``, so existing ``except HTTPError`` handlers still catch it.
    """
    ACCOUNT_BANNED = "account_banned"
    API_ACCESS_BLOCKED = "api_access_blocked"
    FILES_SUSPENDED = "files_suspended"

    def __init__(self, message: str, *, response=None, body: dict | None = None):
        super().__init__(message, response=response)
        self.body = body or {}
        self.code: str | None = self.body.get("code")
