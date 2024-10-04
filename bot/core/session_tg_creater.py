import os
import shutil
from pyrogram import Client
from bot.utils.logger import logger
from bot.utils.proxy import Proxy
from bot.utils.headers import BrowserType, DeviceType, UserAgent, headers_example



async def register_sessions(settings) -> bool | None:
    API_ID = settings.API_ID
    API_HASH = settings.API_HASH
    # Start creating session
    if not API_ID or not API_HASH:
        raise ValueError("API_ID and API_HASH must be set in .env file")
    print("Enter session name (or press Enter to exit): ")
    session_name = input('➤ ')
    if not session_name:
        return None
    if os.path.exists(f'sessions/{session_name}'):
        logger.error('Session already exists, please try again')
        return None
    
    # Generate User-Agent
    headers = headers_example.copy()
    user_agent = UserAgent(device=DeviceType.ANDROID,
                            browser=BrowserType.CHROME).generate()
    headers['User-Agent'] = user_agent


    # Get proxy or use default
    while True:
        print("┌──────────────────────────────────────────────┐")
        print("│   Enter proxy (or press Enter to use your    │")
        print("│        default IP without a proxy)           │")
        print("├──────────────────────────────────────────────┤")
        print("│ Example:                                     │")
        print("│   socks5://login:password@ip:port            │")
        print("│   http://login:password@ip:port              │")
        print("└──────────────────────────────────────────────┘")
        proxy = input('➤ ')
        if not proxy:
            logger.info('Use default IP\n')
            break
        proxy = Proxy().parse_proxy(proxy)
        if not proxy:
            logger.warning('Invalid proxy format, please try again\n')
            continue
        if isinstance(proxy, Proxy):
            if not await proxy.check_proxy(headers):
                logger.error('Proxy check failed, please try again\n')
                continue
        break


    # Create session 
    try:
        os.mkdir(f'sessions/{session_name}')
        session = Client(
            name='session',
            api_id=API_ID,
            api_hash=API_HASH,
            workdir=f"sessions/{session_name}",
            proxy=proxy.get_proxy_for_pyrogram() if isinstance(proxy, Proxy) else None)

    # Authorization telegram
        async with session:
            user_data = await session.get_me()
    except Exception as error:
        shutil.rmtree(f"sessions/{session_name}")
        logger.error(f"Session creation failed | Error: {error}")
        return False
    
    # Save user agent
    with open(f'sessions/{session_name}/user-agent.txt', 'w') as f:
        f.write(user_agent)

    # Save proxy
    with open(f'sessions/{session_name}/proxy.txt', 'w') as f:
        f.write(str(proxy))

    logger.success(f'Session added successfully @{user_data.username} | id:{user_data.id}')
    return True
