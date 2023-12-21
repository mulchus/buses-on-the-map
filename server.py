import trio
import json
import buses

from functools import partial
from trio_websocket import serve_websocket, ConnectionClosed


async def server(request):
    bus = buses.get_bus()
    ws = await request.accept()
    
    buses_to_map = {
        'msgType': "Buses",
        'buses': [
            {'busId': 'аXXXик', 'lat': 0.0, 'lng': 0.0, 'route': bus['name']},
        ]
    }
    
    while True:
        bus_coords = buses.get_bus_coords(bus)
        try:
            for bus_coord in bus_coords:
                buses_to_map['buses'][0]['lat'] = bus_coord[0]
                buses_to_map['buses'][0]['lng'] = bus_coord[1]
                await ws.send_message(json.dumps(buses_to_map))
                await trio.sleep(1)
        except ConnectionClosed:
            break


async def main():
    await serve_websocket(server, '127.0.0.1', 8000, ssl_context=None)

trio.run(partial(main))
