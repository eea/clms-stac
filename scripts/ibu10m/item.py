import os
from datetime import datetime

import pystac
import rasterio as rio
from lxml import etree
from pyproj import CRS
from pystac.extensions.projection import ProjectionExtension
from rasterio.coords import BoundingBox
from rasterio.warp import transform_bounds
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


def read_metadata_from_xml(metadata: str):
    tree = etree.parse(metadata)
    root = tree.getroot()
    date = root.findall('.//{*}CI_DateTypeCode[@codeListValue="creation"]')[0]
    ci_date = date.getparent().getparent()
    creation_date = ci_date.find(".//{*}Date")
    return creation_date.text


def get_geom_wgs84(bounds: BoundingBox, crs: CRS) -> Polygon:
    bbox = rio.coords.BoundingBox(
        *transform_bounds(crs.to_epsg(), 4326, bounds.left, bounds.bottom, bounds.right, bounds.top)
    )
    return box(*(bbox.left, bbox.bottom, bbox.right, bbox.top))


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


def create_item(tile: str, worldfile: str, metadata: str) -> pystac.Item:
    _, tail = os.path.split(tile)
    product_id, asset = tail.split(".")[0].rsplit("_", 1)
    bounds, _, height, width = read_metadata_from_tiff(tile)
    crs = CRS("epsg:" + product_id.split("_")[4][1:5])
    geom_wgs84 = get_geom_wgs84(bounds, crs)
    description = get_description(product_id)
    start_datetime, end_datetime = get_datetime(product_id)
    created = read_metadata_from_xml(metadata)

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


def create_ibu10m_item(tile: str, worldfile: str, metadata: str) -> None:
    item = create_item(tile, worldfile, metadata)

    items_dir = os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}")
    if not os.path.exists(items_dir):
        os.makedirs(items_dir)

    file_path = os.path.join(items_dir, f"{item.id}.json")
    item.set_self_href(file_path)
    item.save_object()
