from pyrogram import Client
import os
from main import settings
from bot.utils.headers import headers_example

class Bot:
    def __init__(self):
        self.tg_sessios: list[Client] = []
        self.collect_sessions()

    
    def collect_sessions(self):
        path = 'sessions'
        for session in os.listdir(path):
            headers = headers_example.copy()
            with open(os.path.join(path, session, 'user_agent.txt'), 'r') as f:
                user_agent = f.read()
            client = Client(name='session', api_id=settings.API_ID,
                            api_hash=settings.API_HASH,workdir=os.path.join(path, session),
                            proxy=None)


    async def start(self):
        pass