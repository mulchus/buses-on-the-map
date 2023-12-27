import trio
import json
import logging

from functools import partial
from trio_websocket import serve_websocket, ConnectionClosed
from contextlib import suppress


buses = {}
bounds = {'south_lat': 0, 'north_lat': 0, 'west_lng': 0, 'east_lng': 0}
logger = logging.getLogger('logger')


def is_inside(lat, lng):
    return bounds['south_lat'] <= lat <= bounds['north_lat'] and bounds['west_lng'] <= lng <= bounds['east_lng']


async def server(request):
    global buses
    ws = await request.accept()
    while True:
        try:
            bus = dict(json.loads(await ws.get_message()))
            if not is_inside(bus['lat'], bus['lng']):
                if bus['busId'] in buses:
                    buses.pop(bus['busId'])
                continue
            if bus['busId'] not in buses:
                buses[bus['busId']] = bus
            else:
                buses.update({bus['busId']: bus})
        except ConnectionClosed:
            break


async def listen_browser(ws):
    global bounds
    while True:
        try:
            bounds = json.loads(await ws.get_message())['data']
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
            await trio.sleep(.1)
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
        nursery.start_soon(partial(serve_websocket, server, '127.0.0.1', 8080, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, talk_with_browser, '127.0.0.1', 8000, ssl_context=None))


with suppress(KeyboardInterrupt):
    trio.run(partial(main))
