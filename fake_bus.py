import trio
import json
import itertools
import random
import argparse
import logging
import sys

from load_routes import load_routes
from trio_websocket import open_websocket_url
from contextlib import suppress


logger = logging.getLogger('logger')


def configuring_logging():
    logger.setLevel(logging.INFO)
    logger_handler = logging.StreamHandler(sys.stdout)
    logger_formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)


def get_args():
    parser = argparse.ArgumentParser(description='Скрипт запуска автобусов на карту')
    parser.add_argument(
        '--server',
        '-s',
        nargs='?',
        type=str,
        default='ws://127.0.0.1:8080',
        help='адрес сервера'
    )
    parser.add_argument(
        '--routes_number',
        '-r',
        nargs='?',
        type=int,
        default=1,
        help='количество маршрутов'
    )
    parser.add_argument(
        '--buses_per_route',
        '-b',
        nargs='?',
        type=int,
        default=1,
        help='количество автобусов на каждом маршруте'
    )
    parser.add_argument(
        '--emulator_id',
        '-e',
        nargs='?',
        type=str,
        default='',
        help='префикс к busId на случай запуска нескольких экземпляров имитатора'
    )
    parser.add_argument(
        '--websockets_number',
        '-w',
        nargs='?',
        type=int,
        default=3,
        help='количество открытых веб-сокетов'
    )
    parser.add_argument(
        '--refresh_timeout',
        '-t',
        nargs='?',
        type=float,
        default=1,
        help='задержка в обновлении координат сервера'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        nargs='?',
        type=bool,
        help='настройка логирования'
    )
    
    return parser.parse_args().__dict__.values()


async def run_bus(bus_id, route, send_channel, refresh_timeout, nursery):
    async with send_channel:
        while True:
            try:
                fake_bus = {'busId': bus_id, 'lat': 0.0, 'lng': 0.0, 'route': route['name']}
                for bus_coord in route['coordinates']:
                    fake_bus['lat'] = bus_coord[0]
                    fake_bus['lng'] = bus_coord[1]
                    # print(fake_bus)
                    await send_channel.send(json.dumps(fake_bus, ensure_ascii=False))
                    await trio.sleep(refresh_timeout)
            except Exception:
                nursery.cancel_scope.cancel()


def generate_bus_id(route_id, bus_index, emulator_id):
    return f'{route_id}-{bus_index}{emulator_id}'


async def send_updates(server_address, receive_channel):
    async with receive_channel:
        try:
            async with open_websocket_url(server_address) as ws:
                async for fake_bus in receive_channel:
                    # print(f"got value {fake_bus!r}")
                    await ws.send_message(fake_bus)
                    # await trio.sleep(1)
        except OSError as ose:
            logger.error(f'Connection attempt failed:{ose}')


async def main():
    server, routes_number, buses_per_route, emulator_id, websockets_number, refresh_timeout, verbose = get_args()
    if verbose:
        configuring_logging()
    
    logger.info(f'{server, routes_number, buses_per_route, emulator_id, websockets_number, refresh_timeout, verbose}')
  
    send_channel, receive_channel = trio.open_memory_channel(0)
    async with send_channel, receive_channel:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send_updates, server, receive_channel)
    
            all_buses_count = 0
            for num, route in enumerate(load_routes(routes_number)):
                # buses_count = len(route['stations']) // 5
                # if not buses_count:
                #     buses_count = 1
                all_buses_count += buses_per_route
                # print(route['name'], buses_count)
                for bus_index in range(buses_per_route):
                    route_copy = route.copy()
                    bus_id = generate_bus_id(route_copy['name'], bus_index, emulator_id)
                    route_len = len(route_copy['coordinates'])
                    route_separation = random.randint(0, route_len)
                    new_route = list(itertools.islice(route_copy['coordinates'], route_separation, route_len))
                    new_route_end = list(itertools.islice(route_copy['coordinates'], 0, route_separation))
                    new_route.extend(new_route_end)
                    route_copy['coordinates'] = new_route
                    random.choice([nursery.start_soon(run_bus, bus_id, route_copy, send_channel.clone(),
                                                      refresh_timeout, nursery) for _ in range(websockets_number)])
            logger.info(all_buses_count)


with suppress(KeyboardInterrupt):
    trio.run(main)
