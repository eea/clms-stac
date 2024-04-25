import os
import pystac
import json
from pystac.extensions.item_assets import ItemAssetsExtension, AssetDefinition
from glob import glob
from constants import COLLECTION_DESCRIPTION, COLLECTION_ID, COLLECTION_EXTENT, COLLECTION_TITLE, WORKING_DIR, COLLECTION_KEYWORDS, VPP_HOST_AND_LICENSOR, VPP_PRODUCER_AND_PROCESSOR, COLLECTION_SUMMARIES, TITLE_MAP, CLMS_LICENSE, STAC_DIR
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)


def create_collection():
    collection = pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESCRIPTION,
        extent=COLLECTION_EXTENT,
        title=COLLECTION_TITLE,
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
    items = glob(f"{WORKING_DIR}/{STAC_DIR}/{COLLECTION_ID}/**/VPP*.json")
    for item in items:
        stac_object = pystac.read_file(item)
        collection.add_item(stac_object, title=stac_object.id)

    collection.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{collection.id}/{collection.id}.json"))
    catalog = pystac.read_file(f"{WORKING_DIR}/{STAC_DIR}/clms_catalog.json")
    collection.set_root(catalog)
    collection.set_parent(catalog)
    validator = get_stac_validator("schema/products/vpp.json")
    error_msg = best_match(validator.iter_errors(collection.to_dict()))
    assert error_msg is None, f"Failed to create {collection.id} collection. Reason: {error_msg}."
    collection.save_object()

if __name__ == "__main__":
    create_collection()
