import trio
import json
import logging
import argparse
import sys

from functools import partial
from trio_websocket import serve_websocket, ConnectionClosed
from contextlib import suppress
from dataclasses import dataclass, asdict


@dataclass
class Bus:
    """Class for keeping bus data."""
    busId: str = ''
    lat: float = 0.0
    lng: float = 0.0
    route: str = ''


@dataclass
class WindowBounds:
    """Class for keeping window posotion."""
    south_lat: float = 0.0
    north_lat: float = 0.0
    west_lng: float = 0.0
    east_lng: float = 0.0

    def is_inside(self, bus):
        return self.south_lat <= bus.lat <= self.north_lat and self.west_lng <= bus.lng <= self.east_lng
    
    def update(self, south_lat, north_lat, west_lng, east_lng):
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


buses = {}
bounds = WindowBounds()
server_logger = logging.getLogger('server_logger')


def get_args():
    parser = argparse.ArgumentParser(description='Скрипт запуска автобусов на карту')
    parser.add_argument(
        '--browser_port ',
        '-brop',
        nargs='?',
        type=int,
        default=8000,
        help='порт для браузера'
    )
    parser.add_argument(
        '--bus_port',
        '-busp',
        nargs='?',
        type=int,
        default=8080,
        help='порт для имитатора автобусов'
    )
    parser.add_argument(
        '--refresh_timeout',
        '-t',
        nargs='?',
        type=float,
        default=.1,
        help='задержка в обновлении координат автобусов'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        nargs='?',
        type=bool,
        help='настройка логирования'
    )
    
    return parser.parse_args().__dict__.values()


def configuring_logging():
    server_logger.setLevel(logging.INFO)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )
    logger_handler.setFormatter(logger_formatter)
    server_logger.addHandler(logger_handler)
    

async def get_bus(request):
    global buses
    ws = await request.accept()
    while True:
        try:
            bus = Bus(**json.loads(await ws.get_message()))
            if not bounds.is_inside(bus):
                if bus.busId in buses:
                    buses.pop(bus.busId)
                continue
            if bus.busId not in buses:
                buses[bus.busId] = asdict(bus)
            else:
                buses.update({bus.busId: asdict(bus)})
        except ConnectionClosed:
            break


async def listen_browser(ws):
    global bounds
    while True:
        try:
            bounds.update(**json.loads(await ws.get_message())['data'])
        except ConnectionClosed:
            break


async def send_to_browser(ws, refresh_timeout):
    while True:
        try:
            message = {
                "msgType": "Buses",
                "buses": list(buses.values()),
            }
            await ws.send_message(json.dumps(message))
            await trio.sleep(refresh_timeout)
        except ConnectionClosed:
            break


async def talk_with_browser(request, refresh_timeout):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)
        nursery.start_soon(send_to_browser, ws, refresh_timeout)
    

async def main():
    browser_port, bus_port, refresh_timeout, verbose = get_args()
    if verbose:
        configuring_logging()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, get_bus, '127.0.0.1', bus_port, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, partial(talk_with_browser, refresh_timeout=refresh_timeout),
                                   '127.0.0.1', browser_port, ssl_context=None))


with suppress(KeyboardInterrupt):
    trio.run(partial(main))
