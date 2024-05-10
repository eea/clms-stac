import logging
import os
import re
from datetime import UTC, datetime

import pystac
import pystac.item
import pystac.link
import rasterio as rio
import rasterio.warp
from pystac.extensions.projection import ProjectionExtension
from shapely.geometry import box, mapping

from .constants import (
    CLC_PROVIDER,
    CLMS_LICENSE,
    COLLECTION_ID,
    DOM_MAP,
    ITEM_DESCRIPTION,
    ITEM_MEDIA_TYPE_MAP,
    ITEM_ROLES_MAP,
    ITEM_TITLE_MAP,
    STAC_DIR,
    WORKING_DIR,
)

LOGGER = logging.getLogger(__name__)


def deconstruct_clc_name(filename: str) -> dict[str]:
    filename_split = {"dirname": os.path.dirname(filename), "basename": os.path.basename(filename)}
    p = re.compile("^(?P<id>[A-Z0-9a-z_-]*)\\.(?P<suffix>.*)$")
    m = p.search(filename_split["basename"])

    if m:
        filename_split |= m.groupdict()

    p = re.compile(
        "U(?P<update_campaign>[0-9]{4})_"
        "(?P<theme>CLC|CHA)(?P<reference_year>[0-9]{4})_"
        "V(?P<release_year>[0-9]{4})_(?P<release_number>[0-9a-z]*)"
        "_?(?P<country_code>[A-Z]*)?"
        "_?(?P<DOM_code>[A-Z]*)?"
    )
    m = p.search(filename_split["id"])

    if m:
        filename_split |= m.groupdict()

    return filename_split


def create_item_asset(asset_file: str, DOM_code: str) -> pystac.Asset:
    filename_elements = deconstruct_clc_name(asset_file)
    id = filename_elements["id"]
    suffix = filename_elements["suffix"].replace(".", "_")

    if id.startswith("readme"):
        key = "readme_" + suffix
    elif id.endswith("QGIS"):
        key = "legend_" + suffix
    else:
        key = suffix

    label = DOM_MAP[DOM_code]

    asset = pystac.Asset(
        href=asset_file,
        title=ITEM_TITLE_MAP[key].format(label=label),
        media_type=ITEM_MEDIA_TYPE_MAP[key],
        roles=ITEM_ROLES_MAP[key],
    )
    return f"{filename_elements['id']}_{suffix}", asset


def get_img_paths(data_root: str) -> list[str]:
    img_paths = []
    for root, _, files in os.walk(data_root):
        if root.endswith(("DATA", "French_DOMs")):
            for file in files:
                if file.endswith(".tif"):
                    img_paths.append(os.path.join(root, file))

    return img_paths


def get_item_asset_files(data_root: str, img_path: str) -> list[str]:
    clc_name_elements = deconstruct_clc_name(img_path)
    id = clc_name_elements["id"]
    dom_code = clc_name_elements["DOM_code"]

    asset_files = []

    for root, _, files in os.walk(data_root):
        if not dom_code and "French_DOMs" in root:
            continue

        if dom_code and "Legend" in root and not "French_DOMs" in root:
            continue

        if not "U{update_campaign}_{theme}{reference_year}_V{release_year}".format(**clc_name_elements).lower() in root:
            continue

        for file in files:
            if (
                file.startswith(id + ".")
                or file.endswith(f"{dom_code}.tif.lyr")
                or file.endswith(
                    "QGIS.txt",
                )
                or file == f"readme_{id}.txt"
            ):
                asset_files.append(os.path.join(root, file))

    return asset_files


def project_bbox(src: rio.io.DatasetReader, dst_crs: rio.CRS = rio.CRS.from_epsg(4326)) -> tuple[float]:
    bbox = rio.warp.transform_bounds(src.crs, dst_crs, *src.bounds)
    return bbox


def project_data_window_bbox(
    src: rio.io.DatasetReader, dst_crs: rio.CRS = rio.CRS.from_epsg(4326), dst_resolution: tuple = (0.25, 0.25)
) -> tuple[float]:
    data, transform = rio.warp.reproject(
        source=src.read(),
        src_transform=src.transform,
        src_crs=src.crs,
        dst_crs=dst_crs,
        dst_nodata=src.nodata,
        dst_resolution=dst_resolution,
        resampling=rio.warp.Resampling.max,
    )

    data_window = rio.windows.get_data_window(data, nodata=src.nodata)
    bbox = rio.windows.bounds(data_window, transform=transform)
    return bbox


def create_item(img_path: str, data_root: str) -> pystac.Item:
    clc_name_elements = deconstruct_clc_name(img_path)

    asset_files = get_item_asset_files(data_root, img_path)
    asset_files = [f for f in asset_files if not f.endswith("aux")]
    year = clc_name_elements.get("reference_year")
    props = {
        "description": ITEM_DESCRIPTION.format(year=year),
        "created": None,
        "providers": CLC_PROVIDER.to_dict(),
    }

    with rio.open(img_path) as img:
        if clc_name_elements["DOM_code"]:
            bbox = project_bbox(img)
        else:
            bbox = project_data_window_bbox(img)

        params = {
            "id": clc_name_elements.get("id"),
            "bbox": bbox,
            "geometry": mapping(box(*bbox)),
            "datetime": None,
            "start_datetime": datetime(int(year), 1, 1, microsecond=0, tzinfo=UTC),
            "end_datetime": datetime(int(year), 12, 31, microsecond=0, tzinfo=UTC),
            "properties": props,
        }

    item = pystac.Item(**params)

    for asset_file in asset_files:
        try:
            key, asset = create_item_asset(asset_file, DOM_code=clc_name_elements.get("DOM_code"))
            item.add_asset(
                key=key,
                asset=asset,
            )
        except KeyError as error:
            LOGGER.error("An error occured:", error)

    # TODO: "Thumbnail" was originally put at collection level in the template, while it should perhaps be at item level? Individual previews should be added to each item
    key = "preview"
    asset = pystac.Asset(
        href="https://sdi.eea.europa.eu/public/catalogue-graphic-overview/960998c1-1870-4e82-8051-6485205ebbac.png",
        title=ITEM_TITLE_MAP["preview"].format(label=clc_name_elements["DOM_code"]),
        media_type=ITEM_MEDIA_TYPE_MAP[key],
        roles=ITEM_ROLES_MAP[key],
    )

    item.add_asset(key=key, asset=asset)

    proj_ext = ProjectionExtension.ext(item.assets[os.path.basename(img_path).replace(".", "_")], add_if_missing=True)
    proj_ext.apply(
        epsg=rio.crs.CRS(img.crs).to_epsg(),
        bbox=img.bounds,
        shape=[_ for _ in img.shape],
        transform=[_ for _ in img.transform] + [0.0, 0.0, 1.0],
    )

    CLMS_CATALOG_LINK = pystac.link.Link(
        rel=pystac.RelType.ROOT,
        target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"{STAC_DIR}/clms_catalog.json")),
    )
    COLLECTION_LINK = pystac.link.Link(
        rel=pystac.RelType.COLLECTION,
        target=pystac.STACObject.from_file(
            os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{COLLECTION_ID}.json")
        ),
    )
    ITEM_PARENT_LINK = pystac.link.Link(
        rel=pystac.RelType.PARENT,
        target=pystac.STACObject.from_file(
            os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{COLLECTION_ID}.json")
        ),
    )

    links = [CLMS_LICENSE, CLMS_CATALOG_LINK, ITEM_PARENT_LINK, COLLECTION_LINK]
    item.add_links(links)

    return item
