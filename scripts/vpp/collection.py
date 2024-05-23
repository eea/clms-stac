from __future__ import annotations

import json
import logging
import os

import pystac
import pystac.extensions
import pystac.extensions.projection
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.link import Link
from referencing import Registry, Resource

from .constants import (
    CLMS_LICENSE,
    COLLECTION_DESCRIPTION,
    COLLECTION_EXTENT,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_TITLE,
    STAC_DIR,
    TITLE_MAP,
    VPP_HOST_AND_LICENSOR,
    VPP_PRODUCER_AND_PROCESSOR,
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


def create_core_collection() -> pystac.Collection:
    return pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESCRIPTION,
        extent=COLLECTION_EXTENT,
        title=COLLECTION_TITLE,
        keywords=COLLECTION_KEYWORDS,
        providers=[VPP_HOST_AND_LICENSOR, VPP_PRODUCER_AND_PROCESSOR],
    )


def add_summaries_to_collection(collection: pystac.Collection, epsg_list: list[int]) -> None:
    summaries = ProjectionExtension.summaries(collection, add_if_missing=True)
    summaries.epsg = epsg_list


def add_item_assets_to_collection(collection: pystac.Collection, asset_title_map: dict[str, str]) -> None:
    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {
        key: AssetDefinition({"title": asset_title_map[key], "media_type": pystac.MediaType.GEOTIFF, "roles": ["data"]})
        for key in asset_title_map
    }


def add_links_to_collection(collection: pystac.Collection, link_list: list[Link]) -> None:
    for link in link_list:
        collection.links.append(link)


def add_items_to_collection(collection: pystac.Collection, item_list: list[str]) -> None:
    for item in item_list:
        stac_object = pystac.read_file(item)
        collection.add_item(stac_object, title=stac_object.id)


def create_collection(item_list: list[str]) -> pystac.Collection:
    try:
        collection = create_core_collection()

        # summaries
        epsg_list = [
            32620,
            32621,
            32622,
            32625,
            32626,
            32627,
            32628,
            32629,
            32630,
            32631,
            32632,
            32633,
            32634,
            32635,
            32636,
            32637,
            32638,
            32738,
            32740,
        ]
        add_summaries_to_collection(collection, epsg_list)

        # extensions
        add_item_assets_to_collection(collection, TITLE_MAP)

        # links
        link_list = [CLMS_LICENSE]
        add_links_to_collection(collection, link_list)

        # add items
        add_items_to_collection(collection, item_list)

        # add self, root, and parent links
        collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{collection.id}/{collection.id}.json"))
        catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")
        collection.set_root(catalog)
        collection.set_parent(catalog)
    except Exception as error:
        raise CollectionCreationError(error)
    return collection


def create_vpp_collection(item_list: list[str], validator: Draft7Validator) -> None:
    try:
        collection = create_collection(item_list)
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
        collection.save_object()
    except (AssertionError, CollectionCreationError) as error:
        LOGGER.error(error)
