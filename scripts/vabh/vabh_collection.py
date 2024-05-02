from __future__ import annotations

import os
from datetime import datetime
from typing import Final

import pystac
import rasterio as rio
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pyproj import Transformer
from pystac import Extent, SpatialExtent, TemporalExtent
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.link import Link
from pystac.provider import ProviderRole
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from shapely.geometry import Polygon, box

# KEY = "/Users/xiaomanhuang/pl/ETCDI_STAC/uabh_samples/AT001_WIEN_UA2012_DHM_v020/data/AT001_WIEN_UA2012_DHM_V020.tif"
KEY = "/Users/xiaomanhuang/pl/ETCDI_STAC/uabh_samples/AT001_WIEN_UA2012_DHM_v020"
head, tail = os.path.split(KEY)
(product_id, product_version) = tail.rsplit("_", 1)
PATH_Dataset = os.path.join(KEY, "Dataset/" + tail + ".tif")

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
COLLECTION_title = "Urban Atlas Building Height 10m"
COLLECTION_description = "Urban Atlas building height over capital cities."
COLLECTION_keywords = ["Buildings", "Building height", "Elevation"]

# links
CLMS_LICENSE: Final[Link] = Link(
    rel="license",
    target="https://land.copernicus.eu/en/data-policy",
    title="Legal notice on the use of CLMS data",
)

WORKING_DIR = os.getcwd()
CLMS_CATALOG_LINK: Final[Link] = Link(
    rel=pystac.RelType.ROOT,
    target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, "stacs/clms_catalog.json")),
    title="CLMS Catalog",
)

CLMS_PARENT_LINK: Final[Link] = Link(
    rel=pystac.RelType.PARENT,
    target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, "stacs/clms_catalog.json")),
    title="CLMS Catalog",
)


def get_metadata_from_tif(key: str) -> tuple[BoundingBox, CRS, int, int]:
    with rio.open(key) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    tif.close()
    return (bounds, crs, height, width)


def get_geom_wgs84(bounds: BoundingBox, crs: CRS) -> Polygon:
    transformer = Transformer.from_crs(crs.to_epsg(), 4326)
    miny, minx = transformer.transform(bounds.left, bounds.bottom)
    maxy, maxx = transformer.transform(bounds.right, bounds.top)
    bbox = (minx, miny, maxx, maxy)
    return box(*bbox)


def get_datetime(product_id: str) -> tuple[datetime, datetime]:
    year = int(product_id.split("_")[2][2:])
    return (datetime(year=year, month=1, day=1), datetime(year=year, month=12, day=31))


def get_collection_extent(bbox, start_datetime) -> Extent:
    spatial_extent = SpatialExtent(bboxes=bbox)
    temporal_extent = TemporalExtent(intervals=[[start_datetime, None]])
    return Extent(spatial=spatial_extent, temporal=temporal_extent)


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
    geom_wgs84 = get_geom_wgs84(bounds, crs)
    start_datetime, end_datetime = get_datetime(product_id)
    COLLECTION_extent = get_collection_extent(list(geom_wgs84.bounds), start_datetime)
    COLLECTION_summaries = pystac.Summaries({"proj:epsg": [crs.to_epsg()]})

    collection = pystac.Collection(
        stac_extensions=[
            "https://stac-extensions.github.io/item-assets/v1.0.0/schema.json",
            "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
        ],
        id=COLLECTION_id,
        title=COLLECTION_title,
        description=COLLECTION_description,
        keywords=COLLECTION_keywords,
        extent=COLLECTION_extent,
        summaries=COLLECTION_summaries,
        providers=[HOST_AND_LICENSOR],
    )

    # add item assets
    add_item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    add_item_assets.item_assets = {
        "dataset": AssetDefinition(
            {"title": "Building height raster", "media_type": pystac.MediaType.GEOTIFF, "roles": ["data"]}
        ),
        "quality_check_report": AssetDefinition(
            {"title": "Quality check report", "media_type": pystac.MediaType.PDF, "roles": ["metadata"]}
        ),
        "metadata": AssetDefinition({"title": "Metadata", "media_type": pystac.MediaType.XML, "roles": ["metadata"]}),
        "quality_control_report": AssetDefinition(
            {"title": "Quality control report", "media_type": pystac.MediaType.PDF, "roles": ["metadata"]}
        ),
        "pixel_based_info_shp": AssetDefinition(
            {"title": "Pixel based info shape format", "media_type": "application/octet-stream", "roles": ["metadata"]}
        ),
        "pixel_based_info_shx": AssetDefinition(
            {"title": "Pixel based info shape index", "media_type": "application/octet-stream", "roles": ["metadata"]}
        ),
        "pixel_based_info_dbf": AssetDefinition(
            {"title": "Pixel based info attribute", "media_type": "application/x-dbf", "roles": ["metadata"]}
        ),
        "pixel_based_info_prj": AssetDefinition(
            {
                "title": "Pixel based info projection description",
                "media_type": pystac.MediaType.TEXT,
                "roles": ["metadata"],
            }
        ),
        "pixel_based_info_cpg": AssetDefinition(
            {"title": "Pixel based info character encoding", "media_type": pystac.MediaType.TEXT, "roles": ["metadata"]}
        ),
        "compressed_dataset": AssetDefinition(
            {"title": "Compressed building height raster", "media_type": "application/zip", "roles": ["data"]}
        ),
    }

    # add links
    collection.links.append(CLMS_LICENSE)
    collection.links.append(CLMS_CATALOG_LINK)
    collection.links.append(CLMS_PARENT_LINK)

    collection.set_self_href("scripts/vabh/test_collection.json")
    collection.save_object()

    # validate
    validator = get_stac_validator("./schema/products/uabh.json")
    error_msg = best_match(validator.iter_errors(collection.to_dict()))
    if error_msg is not None:
        print(error_msg)
