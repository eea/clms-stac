import json
import os
from datetime import datetime

import pystac
import rasterio as rio
from pyproj import Transformer
from pystac.extensions.projection import ProjectionExtension
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from shapely.geometry import Polygon, box, mapping

from .constants import (
    CLMS_CATALOG_LINK,
    CLMS_LICENSE,
    COLLECTION_ID,
    COLLECTION_LINK,
    ITEM_PARENT_LINK,
    STAC_DIR,
    WORKING_DIR,
)


def read_metadata_from_tiff(tile: str):
    with rio.open(tile) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    return (bounds, crs, height, width)


def get_geom_wgs84(bounds: BoundingBox, crs: CRS) -> Polygon:
    transformer = Transformer.from_crs(crs.to_proj4(), 4326)
    miny, minx = transformer.transform(bounds.left, bounds.bottom)
    maxy, maxx = transformer.transform(bounds.right, bounds.top)
    bbox = (minx, miny, maxx, maxy)
    return box(*bbox)


def get_description(product_id: str) -> str:
    product, year, tile_res, extent, epsg = product_id.split("_")
    return f"{year} imperviousness built-up product {extent}"


def get_datetime(product_id: str) -> tuple[datetime, datetime]:
    year = int(product_id.split("_")[1])
    return (datetime(year=year, month=1, day=1), datetime(year=year, month=12, day=31))


def create_assets(tile: str, worldfile: str) -> list[list[str, pystac.Asset]]:
    tile_asset_id = "builtup_map"
    tile_asset = pystac.Asset(href=tile, media_type=pystac.MediaType.GEOTIFF, title="Built-up Map", roles=["data"])
    worldfile_asset_id = "builtup_map_database"
    worldfile_asset = pystac.Asset(href=worldfile, media_type="application/dbf", title="Built-up Map", roles=["data"])
    database_asset_id = "builtup_map_worldfile"
    database_asset = pystac.Asset(href=tile, media_type=pystac.MediaType.TEXT, title="Built-up Map", roles=["data"])
    return [[tile_asset_id, tile_asset], [worldfile_asset_id, worldfile_asset], [database_asset_id, database_asset]]


def create_item(tile: str, worldfile: str) -> pystac.Item:
    _, tail = os.path.split(tile)
    product_id, asset = tail.split(".")[0].rsplit("_", 1)
    bounds, crs, height, width = read_metadata_from_tiff(tile)
    geom_wgs84 = get_geom_wgs84(bounds, crs)
    description = get_description(product_id)
    start_datetime, end_datetime = get_datetime(product_id)
    created = datetime.now().isoformat()

    # common metadata
    item = pystac.Item(
        id=product_id,
        geometry=mapping(geom_wgs84),
        bbox=list(geom_wgs84.bounds),
        datetime=None,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        properties={"created": created, "description": description},
        collection="imperviousness-built-up-10m",
    )

    # extensions
    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = int(product_id.split("_")[4][1:5])
    projection.bbox = [int(bounds.left), int(bounds.bottom), int(bounds.right), int(bounds.top)]
    projection.shape = [height, width]

    # links
    links = [CLMS_LICENSE, CLMS_CATALOG_LINK, ITEM_PARENT_LINK, COLLECTION_LINK]
    for link in links:
        item.links.append(link)

    # assets
    for asset_id, asset in create_assets(tile, worldfile):
        item.add_asset(asset_id, asset)

    return item


def create_ibu10m_item(tile: str, worldfile: str) -> None:
    item = create_item(tile, worldfile)
    item_json = item.to_dict()
    items_dir = os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}")
    if not os.path.exists(items_dir):
        os.makedirs(items_dir)

    file_path = os.path.join(items_dir, f"{item.id}.json")

    with open(file_path, "w") as f:
        json.dump(item_json, f, indent=4)
