import os
import re

import pystac
import pystac.item
import pystac.link
from pystac.provider import ProviderRole
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.item_assets import AssetDefinition

from pyproj import Transformer
from shapely.geometry import GeometryCollection, box, shape, mapping

from datetime import datetime, UTC

import rasterio as rio
import rasterio.warp
from rasterio.warp import Resampling

# from .constants import *

from .constants import (
    DOM_DICT,
    TITLE_DICT,
    MEDIA_TYPE_DICT,
    ROLES_DICT,
    ITEM_DESCRIPTION,
    CLC_PROVIDER,
    CLMS_LICENSE,
    WORKING_DIR,
    STAC_DIR,
    COLLECTION_ID
)

def deconstruct_clc_name(filename: str) -> dict[str]:
    p = re.compile('^(?P<id>[A-Z0-9a-z_]*).(?P<suffix>.*)$')
    m = p.search(os.path.basename(filename))

    filename_split = m.groupdict()

    p = re.compile(("U(?P<update_campaign>[0-9]{4})_"
                    "(?P<theme>CLC|CHA)(?P<reference_year>[0-9]{4})_"
                    "V(?P<release_year>[0-9]{4})_(?P<release_number>[0-9a-z]*)"
                    "_?(?P<country_code>[A-Z]*)?"
                    "_?(?P<DOM_code>[A-Z]*)?"))
    m = p.search(filename_split['id'])
    
    if m:
        return m.groupdict() | filename_split
    else:
        return filename_split


def create_asset(filename: str, DOM_code: str) -> pystac.Asset:
    filename_elements = deconstruct_clc_name(filename)
    id = filename_elements['id']
    suffix = filename_elements['suffix'].replace('.', '_')
    
    if id.startswith('readme'):
        key = 'readme_' + suffix
    elif id.endswith('QGIS'):
        key = 'legend_' + suffix
    else:
        key = suffix

    label = DOM_DICT[DOM_code]
    
    asset = pystac.Asset(href=filename, title=TITLE_DICT[key].format(label=label), media_type=MEDIA_TYPE_DICT[key], roles=ROLES_DICT[key])
    return f"{filename_elements['id']}_{suffix}", asset

def get_img_paths(data_root: str) -> list[str]:    
    img_paths=[]
    for root, _, files in os.walk(data_root):
        if root.endswith(('DATA', 'French_DOMs')):
            for file in files:
                if file.endswith('.tif'):
                    img_paths.append(os.path.join(root, file))

    return img_paths


def get_asset_files(data_root: str, img_path: str) -> list[str]:

    clc_name_elements = deconstruct_clc_name(img_path)
    id = clc_name_elements['id']
    dom_code = clc_name_elements['DOM_code']

    asset_files = []
    
    for root, _, files in os.walk(data_root):
        if not dom_code and 'French_DOMs' in root:
           continue

        if dom_code and 'Legend' in root and not 'French_DOMs' in root:
            continue
        
        if not 'U{update_campaign}_{theme}{reference_year}_V{release_year}'.format(**clc_name_elements).lower() in root:
            continue
    
        for file in files:

            if (file.startswith(id + '.') or 
                file.endswith(f'{dom_code}.tif.lyr') or 
                file.endswith('QGIS.txt',) or 
                file == f'readme_{id}.txt'):

                asset_files.append(os.path.join(root, file))

    return asset_files
 
def project_bbox(src: rio.io.DatasetReader, dst_crs: rio.CRS = rio.CRS.from_epsg(4326)) -> tuple[float]:
    bbox = rio.warp.transform_bounds(src.crs, dst_crs, *src.bounds)
    return(bbox)

def project_data_window_bbox(src: rio.io.DatasetReader, dst_crs: rio.CRS = rio.CRS.from_epsg(4326), dst_resolution: tuple = (0.25, 0.25)) -> tuple[float]:
     data, transform = rio.warp.reproject(source=src.read(),
                                          src_transform=src.transform,
                                          src_crs=src.crs,
                                          dst_crs=dst_crs,
                                          dst_nodata=src.nodata,
                                          dst_resolution=dst_resolution,
                                          resampling=rio.warp.Resampling.max)
     
     data_window = rio.windows.get_data_window(data, nodata=src.nodata)
     bbox = rio.windows.bounds(data_window, transform=transform)    
     return bbox

def create_item(img_path: str, data_root: str) -> pystac.Item:

    clc_name_elements = deconstruct_clc_name(img_path)

    asset_files = get_asset_files(data_root, img_path)
    asset_files = [f for f in asset_files if not f.endswith('aux')]
    year = clc_name_elements.get('reference_year')
    props = {'description': ITEM_DESCRIPTION.format(year=year),
             'created': None,
             'providers': CLC_PROVIDER.to_dict(),
    }

    with rio.open(img_path) as img:

        #bbox = project_bbox(img)
        bbox = project_data_window_bbox(img)

        params = {
            'id': clc_name_elements.get('id'),
            'bbox': bbox,
            'geometry': mapping(box(*bbox)),
            'datetime': None,
            'start_datetime': datetime(int(year), 1, 1, microsecond=0, tzinfo=UTC),
            'end_datetime': datetime(int(year), 12, 31, microsecond=0, tzinfo=UTC),
            'properties': props,
        }

    item = pystac.Item(**params)
    
    for asset_file in asset_files:
        try:
            key, asset = create_asset(asset_file, DOM_code=clc_name_elements.get('DOM_code'))
            item.add_asset(
                key=key,
                asset=asset,
            )
        except KeyError as e:
            print("An error occured:", e)


    proj_ext = ProjectionExtension.ext(item.assets[os.path.basename(img_path).replace('.', '_')], add_if_missing=True)
    proj_ext.apply(epsg=rio.crs.CRS(img.crs).to_epsg(),
                   bbox=img.bounds,
                   shape=[_ for _ in img.shape],
                   transform=[_ for _ in img.transform] + [0.0, 0.0, 1.0],
                   )

    CLMS_CATALOG_LINK = pystac.link.Link(
        rel=pystac.RelType.ROOT, target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"{STAC_DIR}/clms_catalog.json"))
    )
    COLLECTION_LINK = pystac.link.Link(
        rel=pystac.RelType.COLLECTION,
        target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{COLLECTION_ID}.json")),
    )
    ITEM_PARENT_LINK = pystac.link.Link(
        rel=pystac.RelType.PARENT,
        target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"{STAC_DIR}/{COLLECTION_ID}/{COLLECTION_ID}.json")),
    )
        
    links = [CLMS_LICENSE, CLMS_CATALOG_LINK, ITEM_PARENT_LINK, COLLECTION_LINK]
    item.add_links(links)

    return item

