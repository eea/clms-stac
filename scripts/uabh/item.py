from __future__ import annotations

import json
import logging
import os
import re
import xml.etree.ElementTree as ETree
from datetime import datetime
from glob import glob

import pystac
import rasterio as rio
from jsonschema import Draft7Validator
from jsonschema.exceptions import best_match
from pystac.extensions.projection import ProjectionExtension
from pystac.media_type import MediaType
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
    HOST_AND_LICENSOR,
    ITEM_PARENT_LINK,
    STAC_DIR,
    WORKING_DIR,
)

LOGGER = logging.getLogger(__name__)


class ItemCreationError(Exception):
    pass


def get_metadata_from_tif(root_dir: str, product_id: str) -> tuple[BoundingBox, CRS, int, int]:
    tif_path = os.path.join(root_dir, f"Dataset/{product_id}.tif")
    with rio.open(tif_path) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    return (bounds, crs, height, width)


def str_to_datetime(datetime_str: str):
    year, month, day = datetime_str[0:10].split("-")
    return datetime(year=int(year), month=int(month), day=int(day))


def get_namespace(tag: str, xml_string: str) -> str:
    return re.search(r"xmlns:" + tag + '="([^"]+)"', xml_string).group(0).split("=")[1][1:-1]


def get_metadata_from_xml(xml: str) -> tuple[datetime, datetime, datetime]:
    with open(xml, encoding="utf-8") as f:
        xml_string = f.read()
    gmd_namespace = get_namespace("gmd", xml_string)
    gml_namespace = get_namespace("gml", xml_string)
    tree = ETree.parse(xml)
    root = tree.getroot()
    start_datetime = root.findall("".join((".//{", gml_namespace, "}beginPosition")))[0].text  # noqa: FLY002
    end_datetime = root.findall("".join((".//{", gml_namespace, "}endPosition")))[0].text  # noqa: FLY002
    created = root.findall(
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
    return (str_to_datetime(start_datetime), str_to_datetime(end_datetime), str_to_datetime(created))


def get_geom_wgs84(bounds: BoundingBox, crs: CRS) -> Polygon:
    bbox = rio.coords.BoundingBox(
        *transform_bounds(crs.to_epsg(), 4326, bounds.left, bounds.bottom, bounds.right, bounds.top)
    )
    return box(*(bbox.left, bbox.bottom, bbox.right, bbox.top))


def get_description(product_id: str) -> str:
    word_list = product_id.split("_")
    version = word_list.pop()
    year = word_list.pop(-2)
    city = " ".join(word_list[1:-1])
    return f"{year[2:]} {city.title()} building height {version}"


def get_files(uabh_root: str, city_code: str, asset_type: str) -> list[str]:
    files = []
    for dirpath, _, filenames in os.walk(uabh_root):
        files += [
            os.path.join(dirpath, filename)
            for filename in filenames
            if filename.startswith(city_code) and dirpath.endswith(asset_type)
        ]
    return files


def get_zip(uabh_root: str, city_code: str) -> str:
    files = []
    for dirpath, _, filenames in os.walk(uabh_root):
        files += [
            os.path.join(dirpath, filename)
            for filename in filenames
            if filename.startswith(city_code) and filename.endswith(".zip")
        ]
    return files


def collect_assets(uabh_root: str, city_code: str) -> dict[str, pystac.Asset]:
    asset_list = (
        get_files(uabh_root, city_code, "Dataset")
        + get_files(uabh_root, city_code, "Doc")
        + get_files(uabh_root, city_code, "Metadata")
        + get_files(uabh_root, city_code, "PixelBasedInfo")
        + get_files(uabh_root, city_code, "QC")
        + get_zip(uabh_root, city_code)
    )
    assets = {}
    for asset_path in asset_list:
        asset_id, asset = create_asset(asset_path)
        assets[asset_id] = asset
    return assets


def create_asset(asset_path: str) -> tuple[str, pystac.Asset]:
    _, tail = os.path.split(asset_path)
    asset_id = tail.replace(".", "_")
    asset_type = asset_path.split(os.sep)[-2]
    extension = tail.split(".")[-1]
    media_type_map = {
        "tif": MediaType.GEOTIFF,
        "xml": MediaType.XML,
        "pdf": MediaType.PDF,
        "zip": "application/zip",
        "shp": "application/octet-stream",
        "shx": "application/octet-stream",
        "dbf": "application/x-dbf",
        "cpg": "text/plain",
        "prj": "text/plain",
    }
    title_map = {
        "Dataset": "Building Height Dataset",
        "Doc": "Quality Check Report",
        "Metadata": "Building Height Dataset Metadata",
        "PixelBasedInfo": f"pixel_based_info_{extension}",
        "QC": "Quality Control Report",
    }
    role_map = {
        "tif": ["data"],
        "xml": ["metadata"],
        "pdf": ["metadata"],
        "zip": ["data"],
        "shp": ["metadata"],
        "shx": ["metadata"],
        "dbf": ["metadata"],
        "cpg": ["metadata"],
        "prj": ["metadata"],
    }
    if extension == "zip":
        title = "Compressed Building Height Metadata"
    else:
        title = title_map[asset_type]
    return asset_id, pystac.Asset(
        href=asset_path, media_type=media_type_map[extension], title=title, roles=role_map[extension]
    )


def create_core_item(
    product_id: str,
    geometry: Polygon,
    start_datetime: datetime,
    end_datetime: datetime,
    created_datetime: datetime,
    description: str,
    collection: str,
):
    return pystac.Item(
        id=product_id,
        geometry=mapping(geometry),
        bbox=list(geometry.bounds),
        datetime=None,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        properties={
            "created": created_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": description,
        },
        collection=collection,
    )


def add_providers_to_item(item: pystac.Item, provider_list: list[pystac.Provider]) -> None:
    item.common_metadata.providers = provider_list


def add_projection_extension_to_item(item: pystac.Item, crs: CRS, bounds: BoundingBox, height: int, width: int) -> None:
    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = crs.to_epsg()
    projection.bbox = [int(bounds.left), int(bounds.bottom), int(bounds.right), int(bounds.top)]
    projection.shape = [height, width]


def add_links_to_item(item: pystac.Item, link_list: list[pystac.Link]) -> None:
    for link in link_list:
        item.links.append(link)


def add_assets_to_item(item: pystac.Item, asset_dict: dict[str, pystac.Asset]) -> None:
    for key, asset in asset_dict.items():
        item.add_asset(key, asset)


def create_item(zip_path: str) -> pystac.Item:
    try:
        head, tail = os.path.split(zip_path)
        product_id = tail.split(".")[0].upper()
        bounds, crs, height, width = get_metadata_from_tif(head, product_id)
        xml_path = glob(os.path.join(head, "Metadata", f"{product_id.split('_')[0]}*.xml"))[0]
        start_datetime, end_datetime, created_datetime = get_metadata_from_xml(xml_path)
        geom_wgs84 = get_geom_wgs84(bounds, crs)
        description = get_description(product_id)

        # create core item
        item = create_core_item(
            product_id, geom_wgs84, start_datetime, end_datetime, created_datetime, description, COLLECTION_ID
        )

        # common metadata
        provider_list = [HOST_AND_LICENSOR]
        add_providers_to_item(item, provider_list)

        # extensions
        add_projection_extension_to_item(item, crs, bounds, height, width)

        # links
        link_list = [CLMS_LICENSE, CLMS_CATALOG_LINK, ITEM_PARENT_LINK, COLLECTION_LINK]
        add_links_to_item(item, link_list)

        # assets
        asset_dict = collect_assets(head, product_id.split("_")[0])
        add_assets_to_item(item, asset_dict)
    except Exception as error:
        raise ItemCreationError(f"Failed to create {product_id} item. Reason: {error}.")
    return item


def create_uabh_item(zip_path: str, validator: Draft7Validator) -> None:
    try:
        item = create_item(zip_path)
        item.set_self_href(os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{item.id}/{item.id}.json"))
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
