import json


def get_bus():
    with open('bus_routers/156.json', encoding='utf-8') as f:
        bus = json.load(f)
        return bus


def get_bus_coords(bus):
    return bus['coordinates']
