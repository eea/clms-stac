import os
import re

import pystac
import pystac.item
import pystac.link
from pystac.provider import ProviderRole
from pystac.extensions.projection import ProjectionExtension

from pystac.extensions.item_assets import ItemAssetsExtension, AssetDefinition

from datetime import datetime, UTC

import rasterio.warp

from .constants import (
    COLLECTION_DESCRIPTION,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_TITLE,
    COLLECTION_LICENSE,
    COLLITAS_MEDIA_TYPE_DICT,
    COLLITAS_ROLES_DICT,
    COLLITAS_TITLE_DICT,
    CLMS_LICENSE,
    WORKING_DIR,
    STAC_DIR
)

from .item import create_item, get_img_paths

def proj_epsg_from_item_asset(item):
    for asset_key in item.assets:
        asset = item.assets[asset_key].to_dict()
        if 'proj:epsg' in asset.keys():
            return(asset.get('proj:epsg'))
        

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
        key: AssetDefinition({"title": COLLITAS_TITLE_DICT[key].format(label='').strip(),
                            "media_type": COLLITAS_MEDIA_TYPE_DICT[key], 
                            "roles": COLLITAS_ROLES_DICT[key]})
        for key in COLLITAS_TITLE_DICT
    }

    collection.add_link(CLMS_LICENSE)
    collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{collection.id}/{collection.id}.json"))
    catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")

    collection.set_root(catalog)
    collection.set_parent(catalog)

    collection.save_object()
    return(collection)

def populate_collection(collection: pystac.Collection, data_root: str) -> pystac.Collection:
    img_paths = get_img_paths(path=data_root)

    proj_epsg = []
    for img_path in img_paths:
        item = create_item(img_path, data_root)
        collection.add_item(item)

        item_epsg = proj_epsg_from_item_asset(item)
        proj_epsg.append(item_epsg)

        item.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{item.id}/{item.id}.json"))
        item.save_object()

    collection.make_all_asset_hrefs_relative()
    collection.update_extent_from_items()
    ProjectionExtension.add_to(collection)
    collection.summaries = pystac.Summaries({'proj:epsg': list(set(proj_epsg))})

    collection.save_object()
    return(collection)