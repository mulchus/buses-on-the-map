import trio
import json
import logging
import sys

from trio_websocket import open_websocket_url, HandshakeError, ConnectionClosed
from contextlib import suppress


harmful_bus_logger = logging.getLogger('harmful_bus_logger')


def configuring_logging():
    harmful_bus_logger.setLevel(logging.INFO)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )
    logger_handler.setFormatter(logger_formatter)
    harmful_bus_logger.addHandler(logger_handler)
    

async def send_bus(server_address):
    while True:
        try:
            async with open_websocket_url(server_address) as ws:
                await ws.send_message('fake_bus')
                await ws.send_message(json.dumps({'fake_bus': '123'}))
                await trio.sleep(1)
                harmful_bus_logger.info(json.loads(await ws.get_message()))
                harmful_bus_logger.info(json.loads(await ws.get_message()))
        except OSError as ose:
            harmful_bus_logger.error(f'Connection attempt failed:{ose}')
        except (HandshakeError, ConnectionClosed) as cce:
            harmful_bus_logger.error(f'Connection closed:{cce}')


async def main():
    configuring_logging()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(send_bus, 'ws://127.0.0.1:8080')


with suppress(KeyboardInterrupt):
    trio.run(main)
