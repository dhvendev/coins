import asyncio
from time import time
import traceback
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw import functions
from pyrogram.raw.functions.messages import RequestWebView
from bot.utils.logger import logger
from bot.utils.proxy import Proxy
from bot.utils.headers import headers_example
from aiocfscrape import CloudflareScraper
from pydantic_settings import BaseSettings
from random import randint
from urllib.parse import unquote

class InvalidStartBot(BaseException):
    ...

class Gamer:
    def __init__(self, tg_session:Client, settings: BaseSettings, proxy: Proxy | None = None, user_agent: str | None = None) -> None:
        self.tg_session = tg_session
        self.settings = settings

        self.name = "@" + str(tg_session.workdir).split("/")[-1] if tg_session.workdir else tg_session.name
        self.proxy = proxy
        self.user_agent = user_agent
        self.headers = {}

        self.token_live_time = randint(3500, 3600)
        self.jwt_token_create_time = 0
        self.jwt_live_time = randint(850, 900)
        self.access_token_created_time = 0

        self.logged = False
        self.auth_token = None

        self.access_token = None
        self.refresh_token = None

        self.user_id = ""
        self.first_name = ""
        self.last_name = ""

    async def get_new_tokens(self, session: CloudflareScraper) -> bool:
        payload = {"refreshToken": str(self.refresh_token)}
        try:
            async with session.post("https://api.bybitcoinsweeper.com/api/auth/refresh-token", headers=self.headers, json=payload) as res:
                if await res.status == 201:
                    token = await res.json()
                    self.headers['Authorization'] = f"Bearer {token['accessToken']}"
                    self.access_token = token['accessToken']
                    self.refresh_token = token['refreshToken']
                    logger.success(f"{self.name} | Refresh token successfully")
                    return True
                text = await res.text()
                logger.error(f"{self.name} | <red>Refresh token failed: {text}</red>")
                return False

        except Exception as e:
            logger.error(f"{self.name} | Error: {e}")
            return False
        
    async def tg_connect(self, ref_param: str):
        try:
            await self.tg_session.connect()
            start_command_found = False
            async for message in self.tg_session.get_chat_history('BybitCoinsweeper_Bot'):
                if (message.text and message.text.startswith('/start')) or (
                        message.caption and message.caption.startswith('/start')):
                    start_command_found = True
                    break
            if not start_command_found:
                peer = await self.tg_session.resolve_peer('BybitCoinsweeper_Bot')
                await self.tg_session.invoke(
                    functions.messages.StartBot(
                        bot=peer,
                        peer=peer,
                        start_param=ref_param,
                        random_id=randint(1, 9999999),
                    )
                )
        except (Unauthorized, UserDeactivated, AuthKeyUnregistered) as e:
            raise InvalidStartBot(e)
    
    async def get_tg_web_data(self) -> str:
        ref_param = f"referredBy={self.settings.REF_ID}"
        self.ref_id = str(self.settings.REF_ID)
        try:
            if not self.tg_session.is_connected:
                await self.tg_connect(ref_param=ref_param)

            while True:
                try:
                    peer = await self.tg_session.resolve_peer('BybitCoinsweeper_Bot')
                    break
                except FloodWait as fl:
                    fls = fl.value
                    logger.warning(f"<light-yellow>{self.name}</light-yellow> | FloodWait {fl}")
                    logger.info(f"<light-yellow>{self.name}</light-yellow> | Sleep {fls}s")
                    await asyncio.sleep(fls + 3)
            web_view = await self.tg_session.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url="https://bybitcoinsweeper.com",
                start_param=ref_param
            ))
            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))

            self.user_id = tg_web_data.split('"id":')[1].split(',"first_name"')[0]
            self.first_name = tg_web_data.split('"first_name":"')[1].split('","last_name"')[0]
            self.last_name = tg_web_data.split('"last_name":"')[1].split('","username"')[0]

            if self.tg_session.is_connected:
                await self.tg_session.disconnect()

            return unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

        except InvalidStartBot as error:
            raise error

        except Exception as error:
            logger.error(f"<light-yellow>{self.name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)

    async def login_tg_web_app(self, session: CloudflareScraper):
        try:
            payload = { 
                "initData": self.auth_token,
                "referredBy": str(self.ref_id)
            }
            async with session.post("https://api.bybitcoinsweeper.com/api/auth/login", headers=self.headers, json=payload) as res:
                res.raise_for_status()
                user_data = await res.json()
                logger.success(f"{self.name} | Logged in Successfully!")
                self.headers['Authorization'] = f"Bearer {user_data['accessToken']}"
                self.access_token = user_data['accessToken']
                self.refresh_token = user_data['refreshToken']
                self.logged = True
        except Exception as e:
            logger.error(f"{self.name} | Unknown error while trying to login: {e}")

    async def start(self):
        logger.info(f"Account {self.name} | started")
        
        connector = self.proxy.get_connector() if self.proxy else None
        self.headers = headers_example.copy()
        self.headers["User-Agent"] = self.user_agent

        client = CloudflareScraper(headers=self.headers, connector=connector)

        async with client as session:
            attempt_refresh_token = 0
            while True:
                # Get new tokens
                try:
                    current_time = time()  # Store current time to avoid multiple time() calls
                    # Check if JWT token needs refreshing
                    if current_time - self.jwt_token_create_time >= self.jwt_live_time :
                        if self.logged:
                            logger.info(f"{self.name} | Access token expired,  refreshing token.")
                            res = await self.refresh_token(session)
                            if not res:
                                logger.error(f"{self.name} | Starting new attempt")
                                attempt_refresh_token += 1
                                if attempt_refresh_token >= 3:
                                    logger.error(f"{self.name} | Failed to refresh token 3 times | Exiting")
                                    break
                                continue
                            self.jwt_token_create_time = current_time  # Update create time after refresh
                            self.jwt_live_time = randint(850, 900)    # Reset JWT live time
                            attempt_refresh_token = 0
                            
                    # Check if access token needs to be renewed
                    if current_time - self.access_token_created_time >= self.token_live_time:
                        tg_web_data = await self.get_tg_web_data()
                        self.headers['Tl-Init-Data'] = tg_web_data
                        self.auth_token = tg_web_data
                        await self.login_tg_web_app(session)
                        self.access_token_created_time = current_time  # Update token created time
                        self.token_live_time = randint(3500, 3600)    # Reset token live time
                        
                    self.logged = True
                except Exception as e:
                    traceback.print_exc()
                    logger.error(f"Account {self.name} | Error: {e}")

                break




async def run_gamer(tg_session: tuple[Client, Proxy, str], settings) -> None:
    tg_session, proxy, user_agent = tg_session
    gamer = Gamer(tg_session=tg_session, settings=settings, proxy=proxy, user_agent=user_agent)
    try:
        sleep = randint(1, 5)
        logger.info(f"Account {gamer.name} | ready in {sleep}s")
        await asyncio.sleep(sleep)
        await gamer.start()
    except Exception as e:
        logger.error(f"Account {gamer.name} | Error: {e}")