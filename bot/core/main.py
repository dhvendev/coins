import asyncio
from pyrogram import Client
import os
from bot.core.gamer import run_gamer
from bot.utils.logger import logger
from bot.utils.proxy import Proxy
from bot.utils.headers import headers_example

class Bot:
    def __init__(self, settings):
        self.settings = settings
        self.tg_sessios: list[tuple[Client, Proxy, str]] = [] # (client: Client, proxy: Proxy, user-agent: str)

    
    async def collect_sessions(self) -> None:
        """
        Collect sessions from sessions folder.

        :raises ValueError: If API_ID or API_HASH is not set in .env file
        :raises FileNotFoundError: If no sessions found in sessions folder
        :return: None
        :rtype: None
        """
        if not self.settings.API_ID or not self.settings.API_HASH:
            raise ValueError("API_ID and API_HASH must be set in .env file")

        path = 'sessions'
        if not os.path.exists(path) or not os.listdir(path):
            raise FileNotFoundError("No sessions found")
        
        for session in os.listdir(path):
            try:
                headers = headers_example.copy()
                with open(os.path.join(path, session, 'user-agent.txt'), 'r') as f:
                    user_agent = f.read()
                headers['User-Agent'] = user_agent

                if os.path.exists(os.path.join(path, session, 'proxy.txt')):
                    with open(os.path.join(path, session, 'proxy.txt'), 'r') as f:
                        proxy = f.read()
                    proxy = Proxy().parse_proxy(proxy)
                    if proxy is None:
                        logger.error(f"Proxy parse failed for session: {session}")
                        logger.info("This account passed, please edit proxy.txt file or delete it")
                        continue
                    check_proxy = await proxy.check_proxy(headers=headers)

                    if not check_proxy:
                        proxy = None
                        logger.error(f"Proxy check failed for session: {session}")
                        logger.info("This account passed, please edit proxy.txt file or delete it")
                        continue
                else:
                    proxy = None

                client = Client(name='session', api_id=self.settings.API_ID,
                                api_hash=self.settings.API_HASH,workdir=os.path.join(path, session),
                                proxy=proxy.get_proxy_for_pyrogram() if isinstance(proxy, Proxy) else None)
                self.tg_sessios.append((client, proxy, user_agent))
                logger.success(f"Session {session} collected successfully\n")
            except Exception as error:
                logger.error(f"Error while collecting sessions: {error}")
        logger.success(f"All sessions collected successfully | Total: {len(self.tg_sessios)}")


    async def start(self):
        await self.collect_sessions()
        if len(self.tg_sessios) == 0:
            logger.error("No sessions found")
            return
        logger.info(f"Starting bot | Total: {len(self.tg_sessios)}")
        tasks = [asyncio.create_task(run_gamer(tg_session=tg_session, settings=self.settings)) for tg_session in self.tg_sessios]
        await asyncio.gather(*tasks)