from app.core import config
from app.models.settings import SettingsModel
from aiohttp import ClientSession as BaseClientSession


class ClientSession(BaseClientSession):
    def __init__(self, settings: SettingsModel | None, *args, **kw) -> None:
        if settings:
            kw["proxy"] = settings.get_http_proxy()
            kw["headers"] = settings.get_http_headers()
            kw["cookies"] = settings.get_http_cookies()
        else:
            kw["proxy"] = config.settings.http_proxy
            kw["headers"] = config.headers
            kw["cookies"] = config.cookies

        super().__init__(*args, **kw)
