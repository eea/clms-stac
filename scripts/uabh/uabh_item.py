from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Final

import pystac
import rasterio as rio
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pyproj import Transformer
from pystac.extensions.projection import ProjectionExtension
from pystac.link import Link
from pystac.provider import ProviderRole
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from referencing import Registry, Resource
from shapely.geometry import Polygon, box, mapping

# KEY = "/Users/xiaomanhuang/pl/ETCDI_STAC/uabh_samples/AT001_WIEN_UA2012_DHM_v020/data/AT001_WIEN_UA2012_DHM_V020.tif"
KEY = "/Users/xiaomanhuang/pl/ETCDI_STAC/uabh_samples/AT001_WIEN_UA2012_DHM_v020"
head, tail = os.path.split(KEY)
(product_id, product_version) = tail.rsplit("_", 1)

PATH_Dataset = os.path.join(KEY, "Dataset/" + tail + ".tif")
PATH_Doc = os.path.join(KEY, "Doc/" + product_id + "_QC_Report" + product_version + ".pdf")
PATH_Metadata = os.path.join(KEY, "Metadata/" + product_id + "_metadata_" + product_version + ".xml")
PATH_Zip = os.path.join(head, tail + ".zip")

ASSET_dataset = pystac.Asset(
    href=PATH_Dataset,
    media_type=pystac.MediaType.GEOTIFF,
    title="Building Height Dataset",
    roles=["data"],
)

ASSET_quality_check_report = pystac.Asset(
    href=PATH_Doc,
    media_type=pystac.MediaType.PDF,
    title="Quality Check Report",
    roles=["metadata"],
)

ASSET_metadata = pystac.Asset(
    href=PATH_Metadata,
    media_type=pystac.MediaType.XML,
    title="Building Height Dataset Metadata",
    roles=["metadata"],
)

ASSET_compressed_dataset = pystac.Asset(
    href=PATH_Zip,
    media_type="application/zip",
    title="Compressed Building Height Metadata",
    roles=["data"],
)

HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides "
        "geographical information on land cover and its "
        "changes, land use, ground motions, vegetation state, "
        "water cycle and Earth's surface energy variables to "
        "a broad range of users in Europe and across the "
        "World in the field of environmental terrestrial "
        "applications."
    ),
    roles=[ProviderRole.LICENSOR, ProviderRole.HOST],
    url="https://land.copernicus.eu",
)

COLLECTION_id = "urban-atlas-building-height"

CLMS_LICENSE: Final[Link] = Link(rel="license", target="https://land.copernicus.eu/en/data-policy")

WORKING_DIR = os.getcwd()
CLMS_CATALOG_LINK: Final[Link] = Link(
    rel=pystac.RelType.ROOT, target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, "stacs/clms_catalog.json"))
)
COLLECTION_LINK: Final[Link] = Link(
    rel=pystac.RelType.COLLECTION,
    target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"stacs/{COLLECTION_id}/{COLLECTION_id}.json")),
)
ITEM_PARENT_LINK: Final[Link] = Link(
    rel=pystac.RelType.PARENT,
    target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"stacs/{COLLECTION_id}/{COLLECTION_id}.json")),
)


def get_metadata_from_tif(key: str) -> tuple[BoundingBox, CRS, int, int]:
    with rio.open(key) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    tif.close()
    return (bounds, crs, height, width)


def str_to_datetime(datetime_str: str):
    year, month, day = datetime_str.split("-")
    return datetime(year=int(year), month=int(month), day=int(day))


def get_metadata_from_xml(xml: str) -> tuple[datetime, datetime, datetime]:
    tree = ET.parse(xml)
    for t in tree.iter("{http://www.opengis.net/gml}beginPosition"):
        start_datetime = t.text
    for t in tree.iter("{http://www.opengis.net/gml}endPosition"):
        end_datetime = t.text
    for t in tree.iter("{http://www.isotc211.org/2005/gmd}dateStamp"):
        created = t.find("{http://www.isotc211.org/2005/gco}Date").text

    return (str_to_datetime(start_datetime), str_to_datetime(end_datetime), str_to_datetime(created))


def get_geom_wgs84(bounds: BoundingBox, crs: CRS) -> Polygon:
    transformer = Transformer.from_crs(crs.to_epsg(), 4326)
    miny, minx = transformer.transform(bounds.left, bounds.bottom)
    maxy, maxx = transformer.transform(bounds.right, bounds.top)
    bbox = (minx, miny, maxx, maxy)
    return box(*bbox)


def get_description(product_id: str) -> str:
    country, city, year, product, version = product_id.split("_")
    return f"{year[2:]} {city.title()} building height"


def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)


if __name__ == "__main__":
    head, tail = os.path.split(KEY)
    (product_id,) = tail.split(".")[0].rsplit("_", 0)
    bounds, crs, height, width = get_metadata_from_tif(PATH_Dataset)
    start_datetime, end_datetime, created = get_metadata_from_xml(PATH_Metadata)
    geom_wgs84 = get_geom_wgs84(bounds, crs)
    description = get_description(product_id)

    item = pystac.Item(
        stac_extensions=["https://stac-extensions.github.io/projection/v1.1.0/schema.json"],
        id=tail,
        geometry=mapping(geom_wgs84),
        bbox=list(geom_wgs84.bounds),
        datetime=None,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        properties={
            "created": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": description,
        },
        collection=COLLECTION_id,
    )

    item.common_metadata.providers = [HOST_AND_LICENSOR]

    # extensions
    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = crs.to_epsg()
    projection.bbox = [int(bounds.left), int(bounds.bottom), int(bounds.right), int(bounds.top)]
    projection.shape = [height, width]

    # links
    links = [CLMS_LICENSE, CLMS_CATALOG_LINK, ITEM_PARENT_LINK, COLLECTION_LINK]
    for link in links:
        item.links.append(link)

    # assets
    item.add_asset("dataset", ASSET_dataset)
    item.add_asset("quality_check_report", ASSET_quality_check_report)
    item.add_asset("metadata", ASSET_metadata)
    item.add_asset("compressed_dataset", ASSET_compressed_dataset)

    # item.set_self_href(os.path.join(KEY, f"{tail}.json"))
    item.set_self_href("scripts/vabh/test_item.json")
    item.save_object()

    # validate
    validator = get_stac_validator("./schema/products/uabh.json")
    error_msg = best_match(validator.iter_errors(item.to_dict()))
    if error_msg is not None:
        print(error_msg)
