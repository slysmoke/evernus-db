import requests
import json
from pprint import pprint
import sqlite3


def get_data():
    url = "https://data.everef.net/structures/structures-latest.v2.json"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f"HTTP error {r.status_code} when getting structures data")
    return json.loads(r.text)


def get_region_name(region_id):
    conn = sqlite3.connect("eve.db")
    c = conn.cursor()
    query = """
    SELECT
        regionName
    FROM
        mapRegions
    WHERE
        regionID = ?
    """
    c.execute(query, (region_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


def get_system_name(region_id):
    conn = sqlite3.connect("eve.db")
    c = conn.cursor()
    query = """
    SELECT
        solarSystemName
    FROM
        mapSolarSystems
    WHERE
        solarSystemID = ?
    """
    c.execute(query, (region_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None


def save_structures_to_json():
    data = get_data()
    result = {}
    for d in data.values():
        if not any(
            v is None
            for v in (d.get("name"), d.get("solar_system_id"), d.get("region_id"))
        ):
            structure = {
                "firstSeen": d.get("last_seen_public_structure"),
                "lastSeen": d.get("last_structure_get"),
                "name": d.get("name"),
                "public": d.get("is_public_structure"),
                "regionId": d.get("region_id"),
                "regionName": get_region_name(d.get("region_id")),
                "systemId": d.get("solar_system_id"),
                "systemName": get_system_name(d.get("solar_system_id")),
                "typeId": d.get("type_id"),
                "typeName": d.get("typeName", ""),
            }
            result[d["structure_id"]] = structure

    with open("citadel.json", "w") as f:
        json.dump(result, f, separators=(",", ":"))


save_structures_to_json()
