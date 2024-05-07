import os
import re

import json
import logging
import pystac
import pystac.item
import pystac.link
from pystac.provider import ProviderRole
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.item_assets import ItemAssetsExtension, AssetDefinition

from datetime import datetime, UTC

import rasterio.warp

#Taken 'as is' from other scripts
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

from .constants import (
    COLLECTION_DESCRIPTION,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_TITLE,
    COLLECTION_LICENSE,
    COLLECTION_TITLE_MAP,
    COLLECTION_MEDIA_TYPE_MAP,
    COLLECTION_ROLES_MAP,
    COLLITAS_MEDIA_TYPE_MAP,
    COLLITAS_ROLES_MAP,
    COLLITAS_TITLE_MAP,
    CLMS_LICENSE,
    WORKING_DIR,
    STAC_DIR
)

from .item import create_item, get_img_paths, deconstruct_clc_name


LOGGER = logging.getLogger(__name__)


#Taken 'as is' from other scripts
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
        if 'proj:epsg' in asset.keys():
            return asset.get('proj:epsg')

def get_collection_asset_files(data_root: str) -> list[str]:

    asset_files = []
    
    for root, _, files in os.walk(data_root):

        for file in files:

            if ((file.startswith('clc-country-coverage') and file.endswith('pdf')) or
                file.startswith('clc-file-naming-convention') or 
                (file.startswith('readme') and file.endswith('raster.txt'))):

                asset_files.append(os.path.join(root, file))

    return asset_files

def create_collection_asset(asset_file: str) -> tuple[str, pystac.Asset]:

    filename_elements = deconstruct_clc_name(asset_file)
    id = filename_elements['id']
    
    if id.startswith('clc-file-naming'):
        key = 'clc_file_naming'
    elif id.startswith('clc-country-coverage'):
        key = 'clc_country_coverage'
    elif id.startswith('readme'):
        key = 'readme'
    
    asset = pystac.Asset(href=asset_file, title=COLLECTION_TITLE_MAP[key], media_type=COLLECTION_MEDIA_TYPE_MAP[key], roles=COLLECTION_ROLES_MAP[key])
    
    return id, asset


def create_collection() -> pystac.Collection:

    sp_extent = pystac.SpatialExtent([None, None, None, None])
    tmp_extent = pystac.TemporalExtent([datetime(1990, 1, 1, microsecond=0, tzinfo=UTC), None])
    extent = pystac.Extent(sp_extent,  tmp_extent)

    collection = pystac.Collection(id=COLLECTION_ID,
                                description=COLLECTION_DESCRIPTION,
                                title=COLLECTION_TITLE,
                                extent=extent,
                                keywords=COLLECTION_KEYWORDS,
                                license=COLLECTION_LICENSE,
                                stac_extensions=[]
                                )


    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {
        key: AssetDefinition({"title": COLLITAS_TITLE_MAP[key].format(label='').strip(),
                              "media_type": COLLITAS_MEDIA_TYPE_MAP[key], 
                              "roles": COLLITAS_ROLES_MAP[key]})
        for key in COLLITAS_TITLE_MAP
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

    proj_epsg = []
    for img_path in img_paths:
        item = create_item(img_path, data_root)
        collection.add_item(item)

        item_epsg = proj_epsg_from_item_asset(item)
        proj_epsg.append(item_epsg)

        DOM_code = deconstruct_clc_name(img_path).get('DOM_code')
        href = os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{item.id.removesuffix(f'_FR_{DOM_code}')}/{item.id}.json")
        item.set_self_href(href)
        
        validator = get_stac_validator("schema/products/clc.json")
        error_msg = best_match(validator.iter_errors(item.to_dict()))
        try:
            assert error_msg is None, f"Failed to create {item.id} item. Reason: {error_msg}."
        except AssertionError as error:
            LOGGER.error(error)

        item.save_object()

    asset_files = get_collection_asset_files(data_root)

    for asset_file in asset_files:
        key, asset = create_collection_asset(asset_file)
        collection.assets |= {key: asset}

    

    collection.make_all_asset_hrefs_relative()
    collection.update_extent_from_items()
    ProjectionExtension.add_to(collection)
    collection.summaries = pystac.Summaries({'proj:epsg': list(set(proj_epsg))})
    
    try:
        error_msg = best_match(validator.iter_errors(collection.to_dict()))
        assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
    except AssertionError as error:
        LOGGER.error(error)
    
    collection.save_object()

    return collection