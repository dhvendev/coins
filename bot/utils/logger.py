import sys
from loguru import logger


logger.remove()
logger.add(sink=sys.stdout, format="<white>{time:HH:mm:ss DD.MM}</white>"
                                   " | <level>{level: <8}</level>"
                                   " | <white><i>{message}</i></white>")
logger = logger.opt(colors=True)
