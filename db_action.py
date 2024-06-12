import requests
import tarfile
import json
import sqlite3
import hashlib
import os

db = sqlite3.connect("eve.db")


def download_reference_data():
    url = "https://data.everef.net/reference-data/reference-data-latest.tar.xz"
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        raise Exception(f"HTTP error {r.status_code} when getting reference data")
    with open("reference-data-latest.tar.xz", "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)


def read_types_json_from_reference_data():
    with tarfile.open("reference-data-latest.tar.xz", "r:xz") as f:
        file = f.extractfile("types.json")
        data = json.load(file)
        return data


def read_market_groups_json_from_reference_data():
    with tarfile.open("reference-data-latest.tar.xz", "r:xz") as f:
        file = f.extractfile("market_groups.json")
        data = json.load(file)
        return data


def check_md5sum(data):
    md5 = hashlib.md5(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    print(md5)
    return md5


def droptable():
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS invTypes")
    cursor.execute("DROP TABLE IF EXISTS invMarketGroups")
    db.commit()


def delete_file():
    os.remove("reference-data-latest.tar.xz")


def create_table():
    query = """
    CREATE TABLE IF NOT EXISTS invTypes (
        typeID INTEGER PRIMARY KEY not null,
        groupID INTEGER,
        typeName TEXT VARCHAR(100),
        description TEXT,
        mass FLOAT,
        volume FLOAT,
        capacity FLOAT,
        portionSize INTEGER,
        raceID INTEGER,
        basePrice DECIMAL(19,4),
        published BOOLEAN,
        marketGroupID INTEGER,
        iconID INTEGER,
        soundID INTEGER,
        graphicID INTEGER
    )
    """
    query2 = """
    CREATE TABLE "invMarketGroups" (
	"marketGroupID"	INTEGER NOT NULL,
	"parentGroupID"	INTEGER DEFAULT NULL,
	"marketGroupName"	VARCHAR(100) DEFAULT NULL,
	"description"	VARCHAR(3000) DEFAULT NULL,
	"iconID"	INTEGER DEFAULT NULL,
	"hasTypes"	INTEGER DEFAULT NULL,
	PRIMARY KEY("marketGroupID")
)
    """

    cursor = db.cursor()
    cursor.execute(query)
    cursor.execute(query2)
    db.commit()


def insert_into_inv_market_groups(data):
    query = """
    INSERT INTO invMarketGroups (
        marketGroupID,
        parentGroupID,
        marketGroupName,
        description,
        iconID,
        hasTypes
    ) VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor = db.cursor()
    for d in data:
        cursor.execute(
            query,
            (
                d.get("market_group_id"),
                d.get("parent_group_id"),
                d.get("name", {}).get("en"),
                d.get("description", {}).get("en"),
                d.get("icon_id"),
                d.get("has_types"),
            ),
        )

    db.commit()


def insert_into_inv_types(data):
    query = """
    INSERT INTO invTypes (
        typeID,
        groupID,
        typeName,
        description,
        
        volume,
        capacity,
        portionSize,
        raceID,
        basePrice,
        published,
        marketGroupID,
        iconID,
        soundID,
        graphicID
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?,  ?, ?, ?,  ?, ?, ?)
    """
    cursor = db.cursor()
    for d in data:
        cursor.execute(
            query,
            (
                d.get("type_id"),
                d.get("group_id"),
                d.get("name", {}).get("en"),
                d.get("description", {}).get("en"),
                d.get("volume"),
                d.get("capacity"),
                d.get("portion_size"),
                d.get("race_id"),
                d.get("base_price"),
                d.get("published"),
                d.get("market_group_id"),
                d.get("icon_id"),
                d.get("sound_id"),
                d.get("graphic_id"),
            ),
        )

    db.commit()


def main():
    print("Download reference data")
    download_reference_data()
    data = read_types_json_from_reference_data()
    market_group_data = read_market_groups_json_from_reference_data()
    md5sum = check_md5sum(data)

    with open(r"latest_version.json", "r") as f:
        latest_version = json.load(f)
    if latest_version["sdeVersion"] != md5sum:
        print(
            f"Starting update because current md5sum {latest_version['sdeVersion']} != new md5sum {md5sum}"
        )
        droptable()
        create_table()
        print("Insert types into db")
        insert_into_inv_types(data.values())
        print("Insert market groups into db")
        insert_into_inv_market_groups(market_group_data.values())
        print("Update md5sum in latest_version.json")
        latest_version["sdeVersion"] = md5sum
        with open(r"latest_version.json", "w") as f:
            json.dump(latest_version, f, indent=4)
    else:
        print("No need to update")
    print("Delete file")
    delete_file()
    print("Finish updating db")


if __name__ == "__main__":
    main()
