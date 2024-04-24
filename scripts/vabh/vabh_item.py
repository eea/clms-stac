from __future__ import annotations

import os
from datetime import datetime
from typing import Final

import pystac
import rasterio as rio
from pyproj import Transformer
from pystac.provider import ProviderRole
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from shapely.geometry import Polygon, box, mapping

KEY = "/Users/xiaomanhuang/pl/ETCDI_STAC/uabh_samples/AT001_WIEN_UA2012_DHM_v020/data/AT001_WIEN_UA2012_DHM_V020.tif"

VPP_HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides geographical information on land cover and its changes, land"
        " use, ground motions, vegetation state, water cycle and Earth's surface energy variables to a broad range of"
        " users in Europe and across the World in the field of environmental terrestrial applications."
    ),
    roles=[ProviderRole.HOST, ProviderRole.LICENSOR],
    url="https://land.copernicus.eu",
)

VPP_PRODUCER_AND_PROCESSOR: Final[pystac.Provider] = pystac.Provider(
    name="VITO NV",
    description=(
        "VITO is an independent Flemish research organisation in the area of cleantech and sustainable development."
    ),
    roles=[ProviderRole.PROCESSOR, ProviderRole.PRODUCER],
    url="https://vito.be",
)


def read_metadata_from_tif(key: str) -> tuple[BoundingBox, CRS, int, int]:
    with rio.open(key) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    tif.close()
    return (bounds, crs, height, width)  # obj.last_modified


def read_metadata_from_xml(key: str) -> tuple[BoundingBox, CRS, int, int]:
    return (bounds, crs, height, width, created)


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
    year = int(product_id.split("_")[1])
    return (datetime(year=year, month=1, day=1), datetime(year=year, month=12, day=31))


if __name__ == "__main__":
    head, tail = os.path.split(KEY)
    (product_id,) = tail.split(".")[0].rsplit("_", 0)
    bounds, crs, height, width = read_metadata_from_tif(KEY)
    geom_wgs84 = get_geom_wgs84(bounds, crs)
    description = get_description(product_id)
    start_datetime, end_datetime = get_datetime(product_id)

    item = pystac.Item(
        id=product_id,
        geometry=mapping(geom_wgs84),
        bbox=geom_wgs84.bounds,
        datetime=None,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        properties={"created": created.strftime("%Y-%m-%dT%H:%M:%SZ"), "description": description},
        collection="urban-atlas-building-height",
    )

    item.common_metadata.providers = [VPP_HOST_AND_LICENSOR, VPP_PRODUCER_AND_PROCESSOR]
    item.set_self_href("scripts/vpp/test_item.json")
    item.save_object()
