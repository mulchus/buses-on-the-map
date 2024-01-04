import json
import glob


def load_routes(routes_number, directory_path='bus_routers'):
    for filepath in glob.glob(f'{directory_path}/*.json')[:routes_number]:
        with open(filepath, 'r', encoding='utf8') as file:
            yield json.load(file)
