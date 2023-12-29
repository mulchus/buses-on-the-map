import trio
import json
import logging
import sys

from trio_websocket import open_websocket_url, HandshakeError, ConnectionClosed
from contextlib import suppress


harmful_client_logger = logging.getLogger('harmful_client_logger')


def configuring_logging():
    harmful_client_logger.setLevel(logging.INFO)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )
    logger_handler.setFormatter(logger_formatter)
    harmful_client_logger.addHandler(logger_handler)


async def send_browser(server_address):
    while True:
        try:
            async with open_websocket_url(server_address) as ws:
                await ws.send_message('fake_browser_message')
                await ws.send_message(json.dumps({'fake_browser_message': '123'}))
                await trio.sleep(1)
                harmful_client_logger.info(json.loads(await ws.get_message()))
                harmful_client_logger.info(json.loads(await ws.get_message()))
                harmful_client_logger.info(json.loads(await ws.get_message()))
        except OSError as ose:
            harmful_client_logger.error(f'Connection attempt failed:{ose}')
        except (HandshakeError, ConnectionClosed) as cce:
            harmful_client_logger.error(f'Connection closed:{cce}')


async def main():
    configuring_logging()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(send_browser, 'ws://127.0.0.1:8000')


with suppress(KeyboardInterrupt):
    trio.run(main)
