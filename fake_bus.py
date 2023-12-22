import trio
import json
import buses

from sys import stderr
from trio_websocket import open_websocket_url


async def main():
    bus = buses.get_bus()
    fake_bus = {'busId': 'аXXXик', 'lat': 0.0, 'lng': 0.0, 'route': bus['name']}
    # buses_to_map = {
    #     'msgType': "Buses",
    #     'buses': [
    #         {'busId': 'аXXXик', 'lat': 0.0, 'lng': 0.0, 'route': bus['name']},
    #     ]
    # }
    try:
        bus_coords = buses.get_bus_coords(bus)
        async with open_websocket_url('ws://127.0.0.1:8080') as ws:  # ws://127.0.0.1:8080/ws
            for bus_coord in bus_coords:
                fake_bus['lat'] = bus_coord[0]
                fake_bus['lng'] = bus_coord[1]
                await ws.send_message(json.dumps(fake_bus, ensure_ascii=False))
                await trio.sleep(1)
            # await ws.send_message('hello world!')
            # message = await ws.get_message()
            # print('Received message: %s' % message)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)

trio.run(main)
