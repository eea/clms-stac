from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime

import pystac
import pystac.item
import pystac.link

# Taken 'as is' from other scripts
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from referencing import Registry, Resource

from .constants import (
    CLC_PROVIDER,
    CLMS_LICENSE,
    COLLECTION_DESCRIPTION,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_LICENSE,
    COLLECTION_MEDIA_TYPE_MAP,
    COLLECTION_ROLES_MAP,
    COLLECTION_TITLE,
    COLLECTION_TITLE_MAP,
    ITEM_MEDIA_TYPE_MAP,
    ITEM_ROLES_MAP,
    ITEM_TITLE_MAP,
    STAC_DIR,
    WORKING_DIR,
)
from .item import create_item, deconstruct_clc_name, get_img_paths

LOGGER = logging.getLogger(__name__)


# Taken 'as is' from other scripts
def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)


def proj_epsg_from_item_asset(item: pystac.Item) -> int:
    for asset_key in item.assets:
        asset = item.assets[asset_key].to_dict()
        if "proj:epsg" in asset:
            return asset.get("proj:epsg")

    return None


def get_collection_asset_files(data_root: str) -> list[str]:
    asset_files = []

    for root, _, files in os.walk(data_root):
        for file in files:
            if (
                (file.startswith("clc-country-coverage") and file.endswith("pdf"))
                or file.startswith("clc-file-naming-convention")
                or (file.startswith("readme") and file.endswith("raster.txt"))
            ):
                asset_files.append(os.path.join(root, file))

    return asset_files


def create_collection_asset(asset_file: str) -> tuple[str, pystac.Asset]:
    filename_elements = deconstruct_clc_name(asset_file)
    clc_id = filename_elements["id"]

    if clc_id.startswith("clc-file-naming"):
        key = "clc_file_naming"
    elif clc_id.startswith("clc-country-coverage"):
        key = "clc_country_coverage"
    elif clc_id.startswith("readme"):
        key = "readme"

    asset = pystac.Asset(
        href=asset_file,
        title=COLLECTION_TITLE_MAP[key],
        media_type=COLLECTION_MEDIA_TYPE_MAP[key],
        roles=COLLECTION_ROLES_MAP[key],
    )

    return clc_id, asset


def create_collection() -> pystac.Collection:
    sp_extent = pystac.SpatialExtent([None, None, None, None])
    tmp_extent = pystac.TemporalExtent([datetime(1990, 1, 1, microsecond=0, tzinfo=UTC), None])
    extent = pystac.Extent(sp_extent, tmp_extent)

    collection = pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESCRIPTION,
        title=COLLECTION_TITLE,
        extent=extent,
        keywords=COLLECTION_KEYWORDS,
        license=COLLECTION_LICENSE,
        stac_extensions=[],
        providers=[CLC_PROVIDER]
    )

    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {
        f"clc_map_{key}": AssetDefinition(
            {
                "title": ITEM_TITLE_MAP[key].format(label="").strip(),
                "media_type": ITEM_MEDIA_TYPE_MAP[key],
                "roles": ITEM_ROLES_MAP[key],
            }
        )
        for key in ITEM_TITLE_MAP
    }

    collection.add_link(CLMS_LICENSE)
    collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{collection.id}/{collection.id}.json"))
    catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")

    collection.set_root(catalog)
    collection.set_parent(catalog)

    collection.save_object()

    return collection


def populate_collection(collection: pystac.Collection, data_root: str) -> pystac.Collection:
    img_paths = get_img_paths(data_root)
    validator = get_stac_validator("schema/products/clc.json")
    proj_epsg = []
    for img_path in img_paths:
        item = create_item(img_path, data_root)
        collection.add_item(item)

        item_epsg = proj_epsg_from_item_asset(item)
        proj_epsg.append(item_epsg)

        dom_code = deconstruct_clc_name(img_path).get("DOM_code")
        href = os.path.join(
            WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{item.id.removesuffix(f'_FR_{dom_code}')}/{item.id}.json"
        )
        item.set_self_href(href)

        error_msg = best_match(validator.iter_errors(item.to_dict()))
        try:
            assert error_msg is None, f"Failed to create {item.id} item. Reason: {error_msg}."
            item.save_object()
        except AssertionError as error:
            LOGGER.error(error)

    asset_files = get_collection_asset_files(data_root)

    for asset_file in asset_files:
        key, asset = create_collection_asset(asset_file)
        collection.assets |= {key: asset}

    # keep asset href absolute
    # collection.make_all_asset_hrefs_relative()
    collection.update_extent_from_items()
    ProjectionExtension.add_to(collection)
    collection.summaries = pystac.Summaries({"proj:epsg": list(set(proj_epsg))})

    try:
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
        collection.save_object()
    except AssertionError as error:
        LOGGER.error(error)
    return collection
