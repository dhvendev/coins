import asyncio
import hashlib
import hmac
import math
from time import time
import traceback
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw import functions
from pyrogram.raw.functions.messages import RequestWebView
import pytz
from bot.utils.logger import logger
from bot.utils.proxy import Proxy
from bot.utils.headers import headers_example
from aiocfscrape import CloudflareScraper
from pydantic_settings import BaseSettings
from random import randint, uniform
from urllib.parse import unquote
from datetime import datetime

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
        self.user_id = ""

    @staticmethod
    def value(i):
        return sum(ord(o) for o in list(i)) / 1e5

    @staticmethod
    def calc(i, s, a, o, d, g):
        st = (10 * i + max(0, 1200 - 10 * s) + 2000) * (1 + o / a) / 10
        return math.floor(st) + Gamer.value(g)
    
    async def night_sleep_check(self):
        if bool(self.settings.NIGHT_SLEEP):
            time_now = datetime.now()

            # Start and end of the day
            sleep_start = time_now.replace(hour=0, minute=0, second=0, microsecond=0)  # 00:00 ночи
            sleep_end = time_now.replace(hour=8, minute=0, second=0, microsecond=0)    # 08:00 утра

            if time_now >= sleep_start and time_now <= sleep_end:
                time_to_sleep = (sleep_end - time_now).total_seconds()
                wake_up_time = time_to_sleep + randint(0, 3600)

                logger.info(f"{self.name} | Sleep until {sleep_end.strftime('%H:%M')}")
                await asyncio.sleep(wake_up_time)

            logger.info(f"{self.name} | Sleep cancelled | Now start the game")

    async def get_new_tokens(self, session: CloudflareScraper) -> bool:
        """
        Refreshes the access and refresh tokens.

        :param session: The session to use to make the request
        :return: True if the tokens were successfully refreshed, False otherwise
        """
        payload = {"refreshToken": str(self.refresh_token)}
        try:
            async with session.post("https://api.bybitcoinsweeper.com/api/auth/refresh-token", headers=self.headers, json=payload) as res:
                if res.status == 201:
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
        """
        Connects to Telegram and sends the /start command to the bot.

        :param ref_param: The referral parameter to pass to the bot
        :raises InvalidStartBot: If the connection to Telegram fails
        """
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
        """
        Connects to Telegram and sends the /start command to the bot.
        Extracts auth token from the URL and extracts the user data from it.
        Disconnects from Telegram after finishing.
        :return: The extracted user data
        """
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
        """
        Logs into the BybitCoinsweeper API using the previously obtained initData and the ref_id.

        :param session: The session to use for making the request
        :raises Exception: If an unknown error occurs while trying to login
        """
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

    async def game_start(self, session: CloudflareScraper):
        async with session.post("https://api.bybitcoinsweeper.com/api/games/start", headers=self.headers, json={}) as res:
            if res.status == 401:
                await self.get_new_tokens(session)
                return None
            return await res.json()
        
    async def get_me(self, session: CloudflareScraper):
        try:
            async with session.get("https://api.bybitcoinsweeper.com/api/users/me", headers=self.headers) as res:
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Get user info failed: {res.status} | {res.json()}</yellow>")
                    return False
                user = await res.json()
                self.user_id = user['id']
                logger.info(f"{self.name} | Balance: <light-yellow>{user['score']}</light-yellow>")
                return True
        except Exception as e:
            logger.error(f"Account (get_me) {self.name} | Error: {e}")
            return False
        
    async def lose_round(self, session: CloudflareScraper, game_data: dict):
        game_id = game_data['id']
        bagcoins = game_data['rewards']['bagCoins']
        bits = game_data['rewards']['bits']
        gifts = game_data['rewards']['gifts']
        logger.info(f"Successfully started game: <light-blue>{game_id}</light-blue>")
        sleep = uniform(self.settings.TIME_TO_PLAY_EACH_GAME[0], self.settings.TIME_TO_PLAY_EACH_GAME[1])
        logger.info(f"{self.name} | Wait <cyan>{sleep}s</cyan> to complete game...")
        await asyncio.sleep(sleep)
        payload = {
            "bagCoins": bagcoins,
            "bits": bits,
            "gameId": game_id,
            "gifts": gifts
        }
        async with session.post("https://api.bybitcoinsweeper.com/api/games/lose", headers=self.headers ,json=payload) as res:
            if res.status == 201:
                logger.info(f"{self.name} | <red>Lose game: </red><cyan>{game_id}</cyan> <red>:(</red>")
                await self.get_me(session)
            elif res.status == 401:
                await self.get_new_tokens(session)

    async def win_round(self, session: CloudflareScraper, game_data: dict):
        started_at = game_data['createdAt']
        game_id = game_data['id']
        bagcoins = game_data['rewards']['bagCoins']
        bits = game_data['rewards']['bits']
        gifts = game_data['rewards']['gifts']
        logger.info(f"Successfully started game: <light-blue>{game_id}</light-blue>")
        sleep = uniform(self.settings.TIME_TO_PLAY_EACH_GAME[0], self.settings.TIME_TO_PLAY_EACH_GAME[1])
        logger.info(f"{self.name} | Wait <cyan>{sleep}s</cyan> to complete game...")
        await asyncio.sleep(sleep)
        unix_time_started = datetime.strptime(started_at, '%Y-%m-%dT%H:%M:%S.%fZ')
        unix_time_started = unix_time_started.replace(tzinfo=pytz.UTC)
        unix_time_ms = int(unix_time_started.timestamp() * 1000)
        timeplay = sleep
        self.user_id += "v$2f1"
        mr_pl = f"{game_id}-{unix_time_ms}"
        lr_pl = Gamer.calc(i=45,s=timeplay,a=54,o=9,d=True,g=game_id)
        xr_pl = f"{self.user_id}-{mr_pl}"
        kr_pl = f"{timeplay}-{game_id}"
        _r = hmac.new(xr_pl.encode('utf-8'), kr_pl.encode('utf-8'), hashlib.sha256).hexdigest()
        payload = {
            "bagCoins": bagcoins,
            "bits": bits,
            "gameId": game_id,
            "gameTime": timeplay,
            "gifts": gifts,
            "h": _r,
            "score": lr_pl
        }
        async with session.post("https://api.bybitcoinsweeper.com/api/games/win", json=payload, headers=self.headers) as res:
            if res.status == 201:
                logger.info(
                    f"{self.name} | <green> Won game : </green><cyan>{game_id}</cyan> | Earned <yellow>{int(lr_pl)}</yellow>")
                await self.get_me(session)
            elif res.status == 401:
                self.get_new_tokens(session)
                return False
            return True
    async def start(self):
        logger.info(f"Account {self.name} | started")
        
        connector = self.proxy.get_connector() if self.proxy else None
        self.headers = headers_example.copy()
        self.headers["User-Agent"] = self.user_agent

        client = CloudflareScraper(headers=self.headers, connector=connector)

        async with client as session:
            attempt_refresh_token = 0
            periods = 0
            while True:
                # Get new tokens
                try:
                    current_time = time()  # Store current time to avoid multiple time() calls
                    # Check if JWT token needs refreshing
                    if current_time - self.jwt_token_create_time >= self.jwt_live_time :
                        if self.logged:
                            logger.info(f"{self.name} | Access token expired,  refreshing token.")
                            res = await self.get_new_tokens(session)
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


                    if self.logged:
                        try: 
                            await self.get_me(session)
                        except:
                            attempt_get_me = 0
                            while attempt_get_me < 3:
                                self.refresh_token(session)
                                if await self.get_me(session):
                                    break
                                attempt_get_me += 1
                                logger.warning(f"Account {self.name} | Failed to get me info| New attempt after 1 second")
                                await asyncio.sleep(1)
                            logger.error(f"Account {self.name} | Failed to get me info | Exiting account")
                            break
                        
                        attempt_play = randint(self.settings.ROUND_COUNT_EACH_GAME[0], self.settings.ROUND_COUNT_EACH_GAME[1])
                        while attempt_play > 0:
                            attempt_play -= 1
                            if randint(1, 100) > self.settings.CHANCE_TO_WIN:
                                try:
                                    game_data = await self.game_start(session)
                                    if not game_data:
                                        logger.error(f"Account {self.name} | Failed to start game | New attempt after 1 second")
                                        await asyncio.sleep(1)
                                        continue
                                    await self.lose_round(session, game_data)
                                except Exception as e:
                                    logger.warning(f"{self.name} | Unknown error while trying to play game: {e}")
                                    await asyncio.sleep(1)
                            else:
                                try:
                                    game_data = await self.game_start(session)
                                    if not game_data:
                                        logger.error(f"Account {self.name} | Failed to start game | New attempt after 1 second")
                                        await asyncio.sleep(1)
                                        continue
                                    res = await self.win_round(session, game_data)
                                    if not res:
                                        logger.error(f"Account {self.name} | Failed to win game | New attempt after 1 second")
                                        await asyncio.sleep(1)
                                        continue
                                except Exception as e:
                                    logger.warning(f"{self.name} | Unknown error while trying to play game: {e} - Sleep 20s")
                                    traceback.print_exc()
                                    await asyncio.sleep(20)

                            logger.info(f"Account {self.name} | New attempt after sleep 15-25s")
                            await asyncio.sleep(randint(15, 25))
                    periods += 1

                    if periods == 3:
                        sleep = randint(3600, 3600 * 3)
                        logger.info(f"Account {self.name} | Antifrost period | Sleep {sleep}s...")
                        await asyncio.sleep(sleep)
                        periods = 0
                    else:
                        sleep = randint(200, 1000)
                        logger.info(f"Account {self.name} | All attempts finished  | Sleep {sleep}s...")
                        await asyncio.sleep(sleep)

                    # Sleep until next night
                    await self.night_sleep_check()

                except Exception as e:
                    traceback.print_exc()
                    logger.error(f"Account {self.name} | Error: {e}")


async def run_gamer(tg_session: tuple[Client, Proxy, str], settings) -> None:
    """
    Starts a Gamer instance and waits for a random time between 1-5 seconds before doing so.
    
    Args:
        tg_session (tuple[Client, Proxy, str]): A tuple containing a Client instance, a Proxy instance and a User-Agent string.
        settings (Settings): The settings to use for this Gamer instance.
    """
    tg_session, proxy, user_agent = tg_session
    gamer = Gamer(tg_session=tg_session, settings=settings, proxy=proxy, user_agent=user_agent)
    try:
        sleep = randint(1, 5)
        logger.info(f"Account {gamer.name} | ready in {sleep}s")
        await asyncio.sleep(sleep)
        await gamer.start()
    except Exception as e:
        logger.error(f"Account {gamer.name} | Error: {e}")