from __future__ import annotations

import os
from glob import glob

import pystac
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension

from .constants import (
    CLMS_LICENSE,
    COLLECTION_DESCRIPTION,
    COLLECTION_EXTENT,
    COLLECTION_ID,
    COLLECTION_KEYWORDS,
    COLLECTION_SUMMARIES,
    COLLECTION_TITLE,
    IBU10M_HOST_AND_LICENSOR,
    STAC_DIR,
    TITLE_MAP,
    WORKING_DIR,
)


def create_collection(item_list: list[str]) -> pystac.Collection:
    collection = pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESCRIPTION,
        extent=COLLECTION_EXTENT,
        title=COLLECTION_TITLE,
        keywords=COLLECTION_KEYWORDS,
        providers=[IBU10M_HOST_AND_LICENSOR],
        summaries=COLLECTION_SUMMARIES,
    )

    # extensions
    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {
        key: AssetDefinition(
            {"title": TITLE_MAP[key][0], "media_type": TITLE_MAP[key][1], "roles": [TITLE_MAP[key][2]]}
        )
        for key in TITLE_MAP
    }

    # links
    collection.links.append(CLMS_LICENSE)

    # add items
    items = glob(item_list)
    for item in items:
        stac_object = pystac.read_file(item)
        collection.add_item(stac_object, title=stac_object.id)

    collection_dir = os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}")
    collection_path = os.path.join(collection_dir, f"{collection.id}.json")
    collection.set_self_href(collection_path)
    collection.save_object()
