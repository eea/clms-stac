from __future__ import annotations

import json
import logging
import os

import pystac
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac import MediaType
from pystac.extensions.projection import ProjectionExtension
from referencing import Registry, Resource

from .constants import (
    CLMS_LICENSE,
    COLLECTION_DESCRIPTION,
    COLLECTION_EXTENT,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_TITLE,
    N2K_HOST_AND_LICENSOR,
    STAC_DIR,
    WORKING_DIR,
)

LOGGER = logging.getLogger(__name__)


class CollectionCreationError(Exception):
    pass


def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)


def get_files(n2k_root: str, file_extension: str) -> list[str]:
    files = []
    for dirpath, _, filenames in os.walk(n2k_root):
        files += [os.path.join(dirpath, filename) for filename in filenames if filename.endswith(f".{file_extension}")]
    return files


def get_gdb(n2k_root: str) -> list[str]:
    gdb_dirs = []
    for dirpath, dirnames, _ in os.walk(n2k_root):
        if dirnames:
            gdb_dirs += [os.path.join(dirpath, dirname) for dirname in dirnames if dirname.endswith(".gdb")]
    return gdb_dirs


def create_asset(filename, asset_path):
    extension = filename.split(".")[-1]
    asset_id = filename.replace(".", "_")
    year = filename.split("_")[1]
    file_format = asset_id.split("_")[-2].upper()
    media_type_map = {
        "zip": "application/zip",
        "gpkg": MediaType.GEOPACKAGE,
        "gdb": "application/x-filegdb",
        "xml": MediaType.XML,
        "lyr": "application/octet-stream",
        "qml": "application/octet-stream",
        "sld": "application/octet-stream",
    }
    title_map = {
        "zip": f"Compressed Natura 2000 {year} Land Cover/Land Use Status {file_format}",
        "gpkg": f"Natura 2000 {year} Land Cover/Land Use Status {file_format}",
        "gdb": f"Natura 2000 {year} Land Cover/Land Use Status {file_format}",
        "xml": f"Natura 2000 {year} Land Cover/Land Use Status Metadata",
        "lyr": f"Natura 2000 {year} Land Cover/Land Use Status ArcGIS Layer File",
        "qml": f"Natura 2000 {year} Land Cover/Land Use Status QGIS Layer File",
        "sld": f"Natura 2000 {year} Land Cover/Land Use Status OGC Layer File",
    }
    role_map = {
        "zip": ["data"],
        "gpkg": ["data"],
        "gdb": ["data"],
        "xml": ["metadata"],
        "lyr": ["metadata"],
        "qml": ["metadata"],
        "sld": ["metadata"],
    }
    return asset_id, pystac.Asset(
        href=asset_path, media_type=media_type_map[extension], title=title_map[extension], roles=role_map[extension]
    )


def collect_assets(n2k_root: str) -> list[str]:
    asset_list = (
        get_files(n2k_root, "xml")
        + get_files(n2k_root, "lyr")
        + get_files(n2k_root, "qml")
        + get_files(n2k_root, "sld")
        + get_files(n2k_root, "gpkg")
        + get_gdb(n2k_root)
        + get_files(n2k_root, "zip")
    )
    assets = {}
    for asset_path in asset_list:
        _, tail = os.path.split(asset_path)
        asset_id, asset = create_asset(tail, asset_path)
        if asset_id not in assets:
            assets[asset_id] = asset
    return assets


def add_summaries_to_collection(collection: pystac.Collection, epsg_list: list[int]) -> None:
    summaries = ProjectionExtension.summaries(collection, add_if_missing=True)
    summaries.epsg = epsg_list


def add_links_to_collection(collection: pystac.Collection, link_list: list[pystac.Link]) -> None:
    for link in link_list:
        collection.links.append(link)


def add_assets_to_collection(collection: pystac.Collection, asset_dict: dict[str, pystac.Asset]) -> None:
    for key, asset in asset_dict.items():
        collection.add_asset(key, asset)


def create_collection(n2k_root: str) -> pystac.Collection:
    try:
        collection = pystac.Collection(
            id=COLLECTION_ID,
            description=COLLECTION_DESCRIPTION,
            extent=COLLECTION_EXTENT,
            title=COLLECTION_TITLE,
            keywords=COLLECTION_KEYWORDS,
            providers=[N2K_HOST_AND_LICENSOR],
        )

        # summaries
        epsg_list = [3035]
        add_summaries_to_collection(collection, epsg_list)

        # links
        link_list = [CLMS_LICENSE]
        add_links_to_collection(collection, link_list)

        # assets
        assets = collect_assets(n2k_root)
        add_assets_to_collection(collection, assets)

        # update links
        collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{collection.id}.json"))
        catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")
        collection.set_root(catalog)
        collection.set_parent(catalog)
    except Exception as error:
        raise CollectionCreationError(f"Reasom: {error}")
    return collection


def create_n2k_collection(n2k_root: str) -> None:
    try:
        collection = create_collection(n2k_root)
        validator = get_stac_validator("schema/products/n2k.json")
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
        collection.save_object()
    except (AssertionError, CollectionCreationError) as error:
        LOGGER.error(error)
