from __future__ import annotations

import io
import itertools as it
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import boto3
import pystac
import rasterio as rio
from constants import (
    AWS_SESSION,
    BUCKET,
    CLMS_CATALOG_LINK,
    CLMS_LICENSE,
    COLLECTION_ID,
    COLLECTION_LINK,
    ITEM_PARENT_LINK,
    STAC_DIR,
    TITLE_MAP,
    VPP_HOST_AND_LICENSOR,
    VPP_PRODUCER_AND_PROCESSOR,
    WORKING_DIR,
)
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pyproj import Transformer
from pystac.extensions.projection import ProjectionExtension
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from referencing import Registry, Resource
from shapely.geometry import Polygon, box, mapping
from tqdm import tqdm

LOGGER = logging.getLogger(__name__)


def create_product_list(start_year: int, end_year: int) -> list[str]:
    product_list = []
    for year in range(start_year, end_year + 1):
        for season in ("s1", "s2"):
            product_list.append(f"CLMS/Pan-European/Biophysical/VPP/v01/{year}/{season}/")
    return product_list


def create_page_iterator(aws_session: boto3.Session, bucket: str, prefix: str):
    client = aws_session.client("s3")
    paginator = client.get_paginator("list_objects_v2")
    return paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="-", MaxKeys=10)


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
    product, year, _, tile_res, season = product_id.split("_")
    return f"The {year} season {season[-1]} {product} product of tile {tile_res[:6]} at {tile_res[8:10]} m resolution."


def get_datetime(product_id: str) -> tuple[datetime, datetime]:
    year = int(product_id.split("_")[1])
    return (datetime(year=year, month=1, day=1), datetime(year=year, month=12, day=31))


def create_asset(asset_key: str) -> pystac.Asset:
    parameter = asset_key.split("_")[-1].split(".")[0]
    version = asset_key.split("_")[-3]
    return pystac.Asset(
        href=f"s3://{BUCKET}/" + asset_key,
        media_type=pystac.MediaType.GEOTIFF,
        title=TITLE_MAP[parameter] + f" {version}",
        roles=["data"],
    )


def create_item(aws_session: boto3.Session, bucket: str, tile: str) -> pystac.Item:
    client = aws_session.client("s3")
    parameters = client.list_objects(Bucket=bucket, Prefix=tile, Delimiter=".")["CommonPrefixes"]
    asset_keys = [parameter["Prefix"] + "tif" for parameter in parameters]
    _, tail = os.path.split(asset_keys[0])
    product_id = "_".join((tail[:23], tail[29:31]))
    bounds, crs, height, width, created = read_metadata_from_s3(bucket, asset_keys[0], aws_session)
    geom_wgs84 = get_geom_wgs84(bounds, crs)
    description = get_description(product_id)
    start_datetime, end_datetime = get_datetime(product_id)

    # common metadata
    item = pystac.Item(
        id=product_id,
        geometry=mapping(geom_wgs84),
        bbox=list(geom_wgs84.bounds),
        datetime=None,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        properties={"created": created.strftime("%Y-%m-%dT%H:%M:%SZ"), "description": description},
        collection=COLLECTION_ID,
    )
    item.common_metadata.providers = [VPP_HOST_AND_LICENSOR, VPP_PRODUCER_AND_PROCESSOR]

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
    assets = {os.path.split(key)[-1][:-4].lower(): create_asset(key) for key in asset_keys}
    for key, asset in assets.items():
        item.add_asset(key, asset)
    return item


def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)


def create_vpp_item(aws_session: boto3.Session, bucket: str, validator: Draft7Validator, tile: str) -> None:
    item = create_item(aws_session, bucket, tile)
    item.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{item.id}/{item.id}.json"))
    error_msg = best_match(validator.iter_errors(item.to_dict()))
    try:
        assert error_msg is None, f"Failed to create {item.id} item. Reason: {error_msg}."
        item.save_object()
    except AssertionError as error:
        LOGGER.error(error)


def main():
    logging.basicConfig(filename="create_vpp_stac.log")
    validator = get_stac_validator("schema/products/vpp.json")

    product_list = create_product_list(2017, 2023)

    # remove [:1] for full implementation
    for product in product_list[:1]:
        page_iterator = create_page_iterator(AWS_SESSION, BUCKET, product)
        for page in page_iterator:
            tiles = [prefix["Prefix"] for prefix in page["CommonPrefixes"]]
            with ThreadPoolExecutor(max_workers=10) as executor:
                list(
                    tqdm(
                        executor.map(
                            create_vpp_item, it.repeat(AWS_SESSION), it.repeat(BUCKET), it.repeat(validator), tiles
                        ),
                        total=len(tiles),
                    )
                )

            # remove break for full implementation
            break


if __name__ == "__main__":
    main()
