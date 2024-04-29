from __future__ import annotations

import json
import logging
import os

import pystac
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac.extensions.projection import ProjectionExtension
from pystac.media_type import MediaType
from referencing import Registry, Resource

from .constants import (
    CLMS_LICENSE,
    COLLECTION_DESCRIPTION,
    COLLECTION_EXTENT,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_TITLE,
    EUHYDRO_HOST_AND_LICENSOR,
    STAC_DIR,
    WORKING_DIR,
)

LOGGER = logging.getLogger(__name__)


def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)


def get_files(root: str, file_extension: str) -> list[str]:
    files = []
    for dirpath, _, filenames in os.walk(root):
        files += [os.path.join(dirpath, filename) for filename in filenames if filename.endswith(f".{file_extension}")]
    return files


def get_gdb(root: str) -> list[str]:
    gdb_dirs = []
    for dirpath, dirnames, _ in os.walk(root):
        if dirnames:
            gdb_dirs += [os.path.join(dirpath, dirname) for dirname in dirnames if dirname.endswith(".gdb")]
    return gdb_dirs


def create_asset(filename, asset_path):
    extension = filename.split(".")[-1]
    asset_id = filename.replace(".", "_")
    media_type_map = {
        "gpkg": MediaType.GEOPACKAGE,
        "gdb": "application/x-filegdb",
        "xml": MediaType.XML,
        "pdf": MediaType.PDF,
    }
    role_map = {
        "gpkg": ["data"],
        "gdb": ["data"],
        "xml": ["metadata"],
        "pdf": ["metadata"],
    }
    title = " ".join([word.capitalize() for word in asset_id.split("_")[:-1]])
    return asset_id, pystac.Asset(
        href=asset_path, media_type=media_type_map[extension], title=title, roles=role_map[extension]
    )


def collect_assets(root: str) -> list[str]:
    asset_list = get_files(root, "xml") + get_files(root, "pdf") + get_files(root, "gpkg") + get_gdb(root)
    assets = {}
    for asset_path in asset_list:
        _, tail = os.path.split(asset_path)
        asset_id, asset = create_asset(tail, asset_path)
        if asset_id not in assets:
            assets[asset_id] = asset
    return assets


def create_collection(n2k_root: str) -> pystac.Collection:
    collection = pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESCRIPTION,
        extent=COLLECTION_EXTENT,
        title=COLLECTION_TITLE,
        keywords=COLLECTION_KEYWORDS,
        providers=[EUHYDRO_HOST_AND_LICENSOR],
    )

    # summaries
    summaries = ProjectionExtension.summaries(collection, add_if_missing=True)
    summaries.epsg = [3035]

    # links
    collection.links.append(CLMS_LICENSE)

    # assets
    assets = collect_assets(n2k_root)
    for key, asset in assets.items():
        collection.add_asset(key, asset)
    collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{collection.id}.json"))
    catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")
    collection.set_root(catalog)
    collection.set_parent(catalog)
    validator = get_stac_validator("schema/products/eu-hydro.json")
    try:
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
        collection.save_object()
    except AssertionError as error:
        LOGGER.error(error)
    return collection
