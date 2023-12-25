import trio
import json

from functools import partial
from trio_websocket import serve_websocket, ConnectionClosed
from contextlib import suppress


buses = {}


async def server(request):
    global buses
    ws = await request.accept()
    while True:
        try:
            bus = dict(json.loads(await ws.get_message()))
            if bus['busId'] not in buses:
                buses[bus['busId']] = bus
            else:
                buses.update({bus['busId']: bus})
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()
    while True:
        try:
            message = {
              "msgType": "Buses",
              "buses": list(buses.values()),
            }
            # print(message)
            await ws.send_message(json.dumps(message))
            await trio.sleep(.1)
        except ConnectionClosed:
            break


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, server, '127.0.0.1', 8080, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, talk_to_browser, '127.0.0.1', 8000, ssl_context=None))


with suppress(KeyboardInterrupt):
    trio.run(partial(main))
