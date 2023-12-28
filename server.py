import trio
import json
import logging

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
logger = logging.getLogger('logger')


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


async def send_to_browser(ws):
    while True:
        try:
            message = {
                "msgType": "Buses",
                "buses": list(buses.values()),
            }
            await ws.send_message(json.dumps(message))
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def talk_with_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)
        nursery.start_soon(send_to_browser, ws)
    

async def main():
    logger.setLevel(logging.DEBUG)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, get_bus, '127.0.0.1', 8080, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, talk_with_browser, '127.0.0.1', 8000, ssl_context=None))


with suppress(KeyboardInterrupt):
    trio.run(partial(main))
