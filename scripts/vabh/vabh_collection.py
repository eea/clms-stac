from __future__ import annotations

import os
from datetime import datetime
from typing import Final

import pystac
import rasterio as rio
from pyproj import Transformer
from pystac import Extent, SpatialExtent, TemporalExtent
from pystac.provider import ProviderRole
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from shapely.geometry import Polygon, box, mapping

# KEY = "/Users/xiaomanhuang/pl/ETCDI_STAC/uabh_samples/AT001_WIEN_UA2012_DHM_v020/data/AT001_WIEN_UA2012_DHM_V020.tif"
KEY = "/Users/xiaomanhuang/pl/ETCDI_STAC/uabh_samples/AT001_WIEN_UA2012_DHM_v020"
head, tail = os.path.split(KEY)
(product_id,product_version) = tail.rsplit("_", 1)

HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides geographical information on land cover and its changes, land"
        " use, ground motions, vegetation state, water cycle and Earth's surface energy variables to a broad range of"
        " users in Europe and across the World in the field of environmental terrestrial applications."
    ),
    roles=[ProviderRole.HOST, ProviderRole.LICENSOR],
    url="https://land.copernicus.eu",
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


def get_description(product_id: str) -> str:
    country, city, year, product, version = product_id.split("_")
    return f"{year[2:]} {city.title()} building height"


def get_datetime(product_id: str) -> tuple[datetime, datetime]:
    year = int(product_id.split("_")[2][2:])
    return (datetime(year=year, month=1, day=1), datetime(year=year, month=12, day=31))


def get_collection_extent(bbox, start_datetime) -> Extent:
    spatial_extent = SpatialExtent(bboxes=bbox)
    temporal_extent = TemporalExtent(intervals=[[start_datetime, None]])
    return Extent(spatial=spatial_extent, temporal=temporal_extent)


def create_asset(asset_key: str) -> pystac.Asset:
    parameter = asset_key.split("_")[-1].split(".")[0]
    version = asset_key.split("_")[-3]
    return pystac.Asset(
        href=f"s3://{BUCKET}/" + asset_key,
        media_type=pystac.MediaType.GEOTIFF,
        title=TITLE_MAP[parameter] + f" {version}",
        roles=["data"],
    )

def get_item_assets()

def get_links()



if __name__ == "__main__":
    head, tail = os.path.split(KEY)
    (product_id,) = tail.split(".")[0].rsplit("_", 0)
    bounds, crs, height, width = get_metadata_from_tif(KEY)
    geom_wgs84 = get_geom_wgs84(bounds, crs)
    description = get_description(product_id)
    start_datetime, end_datetime = get_datetime(product_id)
    collection_extent = get_collection_extent(list(geom_wgs84.bounds), start_datetime)
    summaries = pystac.Summaries({"proj:epsg": [crs.to_epsg()]})

    collection = pystac.Collection(
        stac_extensions=["https://stac-extensions.github.io/item-assets/v1.0.0/schema.json",
            "https://stac-extensions.github.io/projection/v1.1.0/schema.json"],
        id="urban-atlas-building-height",
        title="Urban Atlas Building Height 10m",
        description="Urban Atlas building height over capital cities.",
        keywords=["Buildings", "Building height", "Elevation"],
        extent=collection_extent,
        summaries=summaries,
        providers=[HOST_AND_LICENSOR],
    )

    collection.set_self_href("scripts/vabh/test_collection.json")
    collection.save_object()