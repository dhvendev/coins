import re
from types import NoneType

import aiohttp
from aiohttp_proxy import ProxyConnector, ProxyType
from aiocfscrape import CloudflareScraper

from bot.utils.logger import logger


class Proxy:
    def __init__(self, scheme: str | None = None,
                    hostname: str | None = None,
                    port: int | None = None,
                    username: str | None = None,
                    password: str | None = None):
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

    def __str__(self) -> str:
        return f"{self.scheme}://{self.username}:{self.password}@{self.hostname}:{self.port}"

    def parse_proxy(self, proxy_input: str) -> bool:
        regex = r'^(?P<scheme>socks5|socks4|http)://(?:(?P<username>[^:]+)(?::(?P<password>[^@]+))?@)?(?P<hostname>[^:\/]+):(?P<port>[0-9]{1,5})$'
        match = re.match(regex, proxy_input)
        if not match:
            return False
        self.scheme = match.group("scheme")
        self.hostname = match.group("hostname")
        self.port = int(match.group("port"))
        self.username = match.group("username")
        self.password = match.group("password")
        return self
    
    def get_proxy_for_pyrogram(self) -> dict:
        return {
            "scheme": self.scheme, 
            "hostname": self.hostname, 
            "port": self.port, 
            "username": self.username, 
            "password": self.password, 
        }
    
    def get_connector(self) -> ProxyConnector:
        connector = ProxyConnector(proxy_type=ProxyType(self.scheme),
                                    host=self.hostname, port=self.port,
                                    username=self.username, password=self.password)
        return connector
    
    async def check_proxy(self, headers: dict) -> bool:
        try:
            async with CloudflareScraper(headers=headers, connector=self.get_connector()) as client:
                async with client.get(url='http://ip-api.com/json/') as response:
                    result = await response.json()
                    ip = result.get('query', None)
                    country = result.get('country', None)
                    city = result.get('city', None)
                    logger.success(f"Checked proxy Result country: {country}/city: {city} IP: <blue>{ip}</blue>")
                    return True
        except Exception as error:
            logger.error(f"Proxy check failed | Error: {error}")
            return False
        
    