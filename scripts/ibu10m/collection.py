from __future__ import annotations

import json
import logging
import os
from enum import Enum

import pystac
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.link import Link
from pystac.media_type import MediaType
from referencing import Registry, Resource

from .constants import (
    CLMS_LICENSE,
    COLLECTION_DESCRIPTION,
    COLLECTION_EXTENT,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_TITLE,
    IBU10M_DATA_DIR,
    IBU10M_HOST_AND_LICENSOR,
    STAC_DIR,
    WORKING_DIR,
)

LOGGER = logging.getLogger(__name__)


class CollectionCreationError(Exception):
    pass


class IBUItemAssets(Enum):
    builtup_map = AssetDefinition({"title": "Map", "media_type": pystac.MediaType.GEOTIFF, "roles": ["data"]})
    builtup_map_database = AssetDefinition(
        {"title": "Map Database", "media_type": "application/dbf", "roles": ["metadata"]}
    )
    builtup_map_worldfile = AssetDefinition(
        {"title": "Map World File", "media_type": pystac.MediaType.TEXT, "roles": ["metadata"]}
    )


def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)


def create_core_collection() -> pystac.Collection:
    return pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESCRIPTION,
        extent=COLLECTION_EXTENT,
        title=COLLECTION_TITLE,
        keywords=COLLECTION_KEYWORDS,
        providers=[IBU10M_HOST_AND_LICENSOR],
    )


def add_item_assets_to_collection(collection: pystac.Collection, item_asset_class: Enum) -> None:
    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {asset.name: asset.value for asset in item_asset_class}


def add_summaries_to_collection(collection: pystac.Collection, epsg_list: list[int]) -> None:
    summaries = ProjectionExtension.summaries(collection, add_if_missing=True)
    summaries.epsg = epsg_list


def add_links_to_collection(collection: pystac.Collection, link_list: list[Link]) -> None:
    for link in link_list:
        collection.links.append(link)


def add_items_to_collection(collection: pystac.Collection, item_list: list[str]) -> None:
    for item in item_list:
        stac_object = pystac.read_file(item)
        collection.add_item(stac_object, title=stac_object.id)


def create_asset(href: str, media_type: str, title: str, roles: list[str]) -> pystac.Asset:
    return pystac.Asset(href=href, media_type=media_type, title=title, roles=roles)


def collect_assets() -> list[pystac.Asset]:
    assets = {}
    for dirpath, _, filenames in os.walk(IBU10M_DATA_DIR):
        for filename in filenames:
            name, extension = tuple(filename.rsplit(".", 1))
            if extension == "xml":
                media_type = MediaType.XML
                title = name.replace("_", " ") + "metadata"
            elif extension == "txt":
                media_type = MediaType.TEXT
                title = name.replace("_", " ") + "color palette"
            else:
                continue
            asset_id = filename.replace(".", "_").lower()
            href = os.path.join(dirpath, filename)
            if asset_id not in assets:
                assets[asset_id] = create_asset(href, media_type, title, ["metadata"])
    return assets


def add_assets_to_collection(collection: pystac.Collection, asset_dict: dict[str, pystac.Asset]) -> None:
    for key, asset in asset_dict.items():
        collection.add_asset(key, asset)


def create_collection(item_list: list[str]) -> pystac.Collection:
    try:
        collection = create_core_collection()

        # extensions
        add_item_assets_to_collection(collection, IBUItemAssets)

        # summaries
        epsg_list = [3035]
        add_summaries_to_collection(collection, epsg_list)

        # links
        link_list = [CLMS_LICENSE]
        add_links_to_collection(collection, link_list)

        # add items
        add_items_to_collection(collection, item_list)

        # add assets
        assets = collect_assets()
        add_assets_to_collection(collection, assets)

        collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{collection.id}/{collection.id}.json"))
        catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")
        collection.set_root(catalog)
        collection.set_parent(catalog)
    except Exception as error:
        raise CollectionCreationError(f"Failed to create Imperviousness Building Height collection. Reason: {error}.")
    return collection


def create_ibu10m_collection(item_list: list[str], validator: Draft7Validator) -> None:
    try:
        collection = create_collection(item_list)
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
        collection.save_object()
    except (AssertionError, CollectionCreationError) as error:
        LOGGER.error(error)
