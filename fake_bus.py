import trio
import json

from load_routes import load_routes
from sys import stderr
from trio_websocket import open_websocket_url


async def run_bus(url, bus_id, route):
    try:
        async with open_websocket_url(url) as ws:
            while True:
                fake_bus = {'busId': bus_id, 'lat': 0.0, 'lng': 0.0, 'route': route['name']}
                for bus_coord in route['coordinates']:
                    fake_bus['lat'] = bus_coord[0]
                    fake_bus['lng'] = bus_coord[1]
                    await ws.send_message(json.dumps(fake_bus, ensure_ascii=False))
                    await trio.sleep(1)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def main():
    async with trio.open_nursery() as nursery:
        for num, route in enumerate(load_routes()):
            print(num, route['name'])
            nursery.start_soon(run_bus, 'ws://127.0.0.1:8080', route['name'], route)
            if num > 2:
                return


trio.run(main)
