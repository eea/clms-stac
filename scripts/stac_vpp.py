from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Final

import boto3
import pystac
import rasterio as rio
from pyproj import Transformer
from pystac.provider import ProviderRole
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from shapely.geometry import Polygon, box, mapping

AWS_SESSION = boto3.Session(profile_name="hrvpp")
BUCKET = "HRVPP"
KEY = "CLMS/Pan-European/Biophysical/VPP/v01/2023/s2/VPP_2023_S2_T40KCC-010m_V105_s2_TPROD.tif"

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


def read_metadata_from_s3(bucket: str, key: str, aws_session: boto3.Session) -> tuple[BoundingBox, CRS, int, int]:
    s3 = aws_session.resource("s3")
    obj = s3.Object(bucket, key)
    body = obj.get()["Body"].read()
    with rio.open(io.BytesIO(body)) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    return (bounds, crs, height, width, obj.last_modified)


def get_geom_wgs84(bounds: BoundingBox, crs: CRS) -> Polygon:
    transformer = Transformer.from_crs(crs.to_epsg(), 4326)
    miny, minx = transformer.transform(bounds.left, bounds.bottom)
    maxy, maxx = transformer.transform(bounds.right, bounds.top)
    bbox = (minx, miny, maxx, maxy)
    return box(*bbox)


def get_description(product_id: str) -> str:
    product, year, _, tile_res, version, season = product_id.split("_")
    return (
        f"The {year} season {season[-1]} version {version[1:]} {product} product of tile {tile_res[:6]} at"
        f" {tile_res[8:10]} m resolution."
    )


def get_datetime(product_id: str) -> tuple[datetime, datetime]:
    year = int(product_id.split("_")[1])
    return (datetime(year=year, month=1, day=1), datetime(year=year, month=12, day=31))


if __name__ == "__main__":
    head, tail = os.path.split(KEY)
    product_id, asset = tail.split(".")[0].rsplit("_", 1)
    bounds, crs, height, width, created = read_metadata_from_s3(BUCKET, KEY, AWS_SESSION)
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
        collection="vegetation-phenology-and-productivity",
    )

    item.common_metadata.providers = [VPP_HOST_AND_LICENSOR, VPP_PRODUCER_AND_PROCESSOR]
    item.set_self_href("scripts/test.json")
    item.save_object()
