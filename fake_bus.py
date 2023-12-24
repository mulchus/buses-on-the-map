import trio
import json
import itertools
import random

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


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


async def main():
    all_buses_count = 0
    async with trio.open_nursery() as nursery:
        for num, route in enumerate(load_routes()):
            buses_count = len(route['stations']) // 8
            if not buses_count:
                buses_count = 1
            all_buses_count += buses_count
            # print(route['name'], buses_count)
            for bus_index in range(buses_count):
                route_copy = route.copy()
                bus_id = generate_bus_id(route_copy['name'], bus_index)
                route_len = len(route_copy['coordinates'])
                route_separation = random.randint(0, route_len)
                new_route = list(itertools.islice(route_copy['coordinates'], route_separation, route_len))
                new_route_end = list(itertools.islice(route_copy['coordinates'], 0, route_separation))
                new_route.extend(new_route_end)
                route_copy['coordinates'] = new_route
                nursery.start_soon(run_bus, 'ws://127.0.0.1:8080', bus_id, route_copy)
        # print(all_buses_count)
            # if num > 0:
            #     return


trio.run(main)
