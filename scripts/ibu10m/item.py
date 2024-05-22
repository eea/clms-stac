import json
import logging
import os
import re
import xml.etree.ElementTree as eTree
from datetime import datetime

import pystac
import rasterio as rio
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac.extensions.projection import ProjectionExtension
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from referencing import Registry, Resource
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

LOGGER = logging.getLogger(__name__)


class ItemCreationError(Exception):
    pass


def read_metadata_from_tiff(tile: str) -> tuple[BoundingBox, CRS, int, int]:
    with rio.open(tile) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    return (bounds, crs, height, width)


def get_namespace(tag: str, xml_string: str) -> str:
    return re.search(r"xmlns:" + tag + '="([^"]+)"', xml_string).group(0).split("=")[1][1:-1]


def read_metadata_from_xml(xml: str) -> str:
    with open(xml, encoding="utf-8") as f:
        xml_string = f.read()
    gmd_namespace = get_namespace("gmd", xml_string)
    tree = eTree.parse(xml)
    root = tree.getroot()
    return root.findall(
        "".join(  # noqa: FLY002
            (
                ".//{",
                gmd_namespace,
                "}CI_DateTypeCode[@codeListValue='creation']....//{",
                gmd_namespace,
                "}date/*",
            )
        )
    )[0].text


def get_geom_wgs84(bounds: BoundingBox, crs: CRS) -> Polygon:
    bbox = rio.coords.BoundingBox(*transform_bounds(crs, 4326, bounds.left, bounds.bottom, bounds.right, bounds.top))
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


def create_core_item(
    product_id: str,
    geometry: Polygon,
    start_datetime: datetime,
    end_datetime: datetime,
    created_datetime: datetime,
    description: str,
    collection: str,
) -> pystac.Item:
    return pystac.Item(
        id=product_id,
        geometry=mapping(geometry),
        bbox=list(geometry.bounds),
        datetime=None,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        properties={"created": created_datetime, "description": description},
        collection=collection,
    )


def add_projection_extension_to_item(
    item: pystac.Item, product_id: str, bounds: BoundingBox, height: int, width: int
) -> None:
    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = int(product_id.split("_")[4][1:5])
    projection.bbox = [int(bounds.left), int(bounds.bottom), int(bounds.right), int(bounds.top)]
    projection.shape = [height, width]


def add_links_to_item(item: pystac.Item, link_list: list[pystac.Link]) -> None:
    for link in link_list:
        item.links.append(link)


def add_assets_to_item(item: pystac.Item, assets: list[str, pystac.Asset]) -> None:
    for asset_id, asset in assets:
        item.add_asset(asset_id, asset)


def create_item(tile: str, worldfile: str, metadata: str) -> pystac.Item:
    try:
        _, tail = os.path.split(tile)
        product_id, asset = tail.split(".")[0].rsplit("_", 1)
        bounds, crs, height, width = read_metadata_from_tiff(tile)
        geom_wgs84 = get_geom_wgs84(bounds, crs)
        description = get_description(product_id)
        start_datetime, end_datetime = get_datetime(product_id)
        created_datetime = read_metadata_from_xml(metadata)

        # common metadata
        item = create_core_item(
            product_id, geom_wgs84, start_datetime, end_datetime, created_datetime, description, COLLECTION_ID
        )

        # extensions
        add_projection_extension_to_item(item, product_id, bounds, height, width)

        # links
        link_list = [CLMS_LICENSE, CLMS_CATALOG_LINK, ITEM_PARENT_LINK, COLLECTION_LINK]
        add_links_to_item(item, link_list)

        # assets
        assets = create_assets(tile, worldfile)
        add_assets_to_item(item, assets)
    except Exception as error:
        raise ItemCreationError(error)
    return item


def create_ibu10m_item(tile: str, worldfile: str, metadata: str, validator: Draft7Validator) -> None:
    try:
        item = create_item(tile, worldfile, metadata)
        items_dir = os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}")
        os.makedirs(items_dir, exist_ok=True)
        file_path = os.path.join(items_dir, f"{item.id}.json")
        item.set_self_href(file_path)
        error_msg = best_match(validator.iter_errors(item.to_dict()))
        assert error_msg is None, f"Failed to create {item.id} item. Reason: {error_msg}."
        item.save_object()
    except (AssertionError, ItemCreationError) as error:
        LOGGER.error(error)


def get_stac_validator(product_schema: str) -> Draft7Validator:
    with open(product_schema, encoding="utf-8") as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    return Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)
