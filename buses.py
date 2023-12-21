import json


def get_bus():
    with open('bus_routers/156.json', encoding='utf-8') as f:
        bus = json.load(f)
        print(len(bus))
        return bus


def get_bus_coords(bus):
    return bus['coordinates']
