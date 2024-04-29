from __future__ import annotations

import json
import logging
import os
from glob import glob

import pystac
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from referencing import Registry, Resource

from .constants import (
    CLMS_LICENSE,
    COLLECTION_DESCRIPTION,
    COLLECTION_EXTENT,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_SUMMARIES,
    COLLECTION_TITLE,
    STAC_DIR,
    TITLE_MAP,
    VPP_HOST_AND_LICENSOR,
    VPP_PRODUCER_AND_PROCESSOR,
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


def create_collection(item_list: list[str]) -> pystac.Collection:
    collection = pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESCRIPTION,
        extent=COLLECTION_EXTENT,
        title=COLLECTION_TITLE,
        stac_extensions=["https://stac-extensions.github.io/projection/v1.1.0/schema.json"],
        keywords=COLLECTION_KEYWORDS,
        providers=[VPP_HOST_AND_LICENSOR, VPP_PRODUCER_AND_PROCESSOR],
        summaries=COLLECTION_SUMMARIES,
    )

    # extensions
    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {
        key: AssetDefinition({"title": TITLE_MAP[key], "media_type": pystac.MediaType.GEOTIFF, "roles": ["data"]})
        for key in TITLE_MAP
    }

    # links
    collection.links.append(CLMS_LICENSE)

    # add items
    items = glob(item_list)
    for item in items:
        stac_object = pystac.read_file(item)
        collection.add_item(stac_object, title=stac_object.id)

    collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{collection.id}/{collection.id}.json"))
    catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")
    collection.set_root(catalog)
    collection.set_parent(catalog)
    validator = get_stac_validator("schema/products/vpp.json")
    try:
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
    except AssertionError as error:
        LOGGER.error(error)
    collection.save_object()
