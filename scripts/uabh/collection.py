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
    COLLECTION_KEYWORD,
    COLLECTION_TITLE,
    HOST_AND_LICENSOR,
    STAC_DIR,
    WORKING_DIR,
)

LOGGER = logging.getLogger(__name__)


class CollectionCreationError(Exception):
    pass


class UABHItemAssets(Enum):
    dataset = AssetDefinition({"title": "Building height raster", "media_type": MediaType.GEOTIFF, "roles": ["data"]})
    metadata = AssetDefinition(
        {"title": "Building height metadata", "media_type": MediaType.XML, "roles": ["metadata"]}
    )
    quality_check_report = AssetDefinition(
        {"title": "Quality check report", "media_type": MediaType.PDF, "roles": ["metadata"]}
    )
    quality_control_report = AssetDefinition(
        {"title": "Quality control report", "media_type": MediaType.PDF, "roles": ["metadata"]}
    )
    pixel_based_info_shp = AssetDefinition(
        {"title": "Pixel based info shape format", "media_type": "application/octet-stream", "roles": ["metadata"]}
    )
    pixel_based_info_shx = AssetDefinition(
        {"title": "Pixel based info shape index", "media_type": "application/octet-stream", "roles": ["metadata"]}
    )
    pixel_based_info_dbf = AssetDefinition(
        {"title": "Pixel based info attribute", "media_type": "application/x-dbf", "roles": ["metadata"]}
    )
    pixel_based_info_prj = AssetDefinition(
        {"title": "Pixel based info projection description", "media_type": "text/plain", "roles": ["metadata"]}
    )
    pixel_based_info_cpg = AssetDefinition(
        {"title": "Pixel based info character encoding", "media_type": "text/plain", "roles": ["metadata"]}
    )
    compressed_dataset = AssetDefinition(
        {"title": "Compressed building height raster", "media_type": "application/zip", "roles": ["data"]}
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
        keywords=COLLECTION_KEYWORD,
        providers=[HOST_AND_LICENSOR],
    )


def add_summaries_to_collection(collection: pystac.Collection, epsg_list: list[int]) -> None:
    summaries = ProjectionExtension.summaries(collection, add_if_missing=True)
    summaries.epsg = epsg_list


def add_item_assets_to_collection(collection: pystac.Collection, item_asset_class: Enum) -> None:
    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {asset.name: asset.value for asset in item_asset_class}


def add_links_to_collection(collection: pystac.Collection, link_list: list[Link]) -> None:
    for link in link_list:
        collection.links.append(link)


def add_items_to_collection(collection: pystac.Collection, item_list: list[str]) -> None:
    for item in item_list:
        stac_object = pystac.read_file(item)
        collection.add_item(stac_object, title=stac_object.id)


def create_collection(item_list: list[str]) -> None:
    try:
        collection = create_core_collection()

        # summaries
        epsg_list = [3035]
        add_summaries_to_collection(collection, epsg_list)

        # extensions
        add_item_assets_to_collection(collection, UABHItemAssets)

        # links
        link_list = [CLMS_LICENSE]
        add_links_to_collection(collection, link_list)

        # add items
        add_items_to_collection(collection, item_list)

        # add self, root and parent links
        collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{collection.id}/{collection.id}.json"))
        catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")
        collection.set_root(catalog)
        collection.set_parent(catalog)
    except Exception as error:
        raise CollectionCreationError(f"Failed to create Urban Atlas Building Height collection. Reason: {error}.")
    return collection


def create_uabh_collection(item_list: list[str], validator: Draft7Validator) -> None:
    try:
        collection = create_collection(item_list)
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
        collection.save_object()
    except (AssertionError, CollectionCreationError) as error:
        LOGGER.error(error)
