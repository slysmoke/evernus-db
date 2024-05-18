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
        ) and d.get("is_market_structure", False):
            structure = {
                "firstSeen": d.get("last_seen_public_structure")
                or "1970-01-01T00:00:00.000Z",
                "lastSeen": d.get("last_structure_get") or "1970-01-01T00:00:00.000Z",
                "name": d.get("name") or "Unknown",
                "public": d.get("is_public_structure") or 0,
                "regionId": d.get("region_id") or 0,
                "regionName": get_region_name(d.get("region_id")) or "None",
                "systemId": d.get("solar_system_id") or 0,
                "systemName": get_system_name(d.get("solar_system_id")) or "None",
                "typeId": d.get("type_id") or 0,
                "typeName": d.get("typeName", ""),
            }
            result[d["structure_id"]] = structure

    with open("citadel.json", "w") as f:
        json.dump(result, f, separators=(",", ":"))

save_structures_to_json()

