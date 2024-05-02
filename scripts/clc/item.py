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

from constants import *

# from .constants import (
#     DOM_DICT,
#     TITLE_DICT,
#     MEDIA_TYPE_DICT,
#     ROLES_DICT,
#     ITEM_DESCRIPTION,
#     CLC_PROVIDER,
#     ITEM_LICENSE
# )

def deconstruct_clc_name(filename: str):
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
        return(m.groupdict() | filename_split)
    else:
        return(filename_split)


def create_asset(filename: str, DOM_code: str):
    filename_elements = deconstruct_clc_name(filename)
    suffix = filename_elements['suffix'].replace('.', '_')
    
    label = DOM_DICT[DOM_code]
    
    asset = pystac.Asset(href=filename, title=TITLE_DICT[suffix].format(label=label), media_type=MEDIA_TYPE_DICT[suffix], roles=ROLES_DICT[suffix])
    return(f"{filename_elements['id']}_{suffix}", asset)

def get_img_paths(path: str):    
    img_paths=[]
    for root, dirs, files in os.walk(path):
        if root.endswith(('DATA', 'French_DOMs')):
            for file in files:
                if file.endswith('.tif'):
                    img_paths.append(os.path.join(root, file))

    return(img_paths)


def get_asset_files(path, clc_name):

    clc_name_elements = deconstruct_clc_name(clc_name)

    asset_files = []
    
    for root, dirs, files in os.walk(path):
        if not clc_name_elements['DOM_code'] and 'French_DOMs' in root:
            continue
        
        if clc_name_elements['DOM_code'] and ('Legend' in root and not 'French_DOMs' in root):
            continue
        
        for file in files:
            if (file.startswith(clc_name + '.') or 
                file.endswith((f'{clc_name_elements["DOM_code"]}.tif.lyr', 'QGIS.txt',)) and 
                clc_name in file):
                asset_files.append(os.path.join(root, file))

    return(asset_files)
 
def project_bbox(img, target_epsg=4326):
    target_crs = rio.crs.CRS.from_epsg(target_epsg)
    bbox_warped = rio.warp.transform_bounds(img.crs, target_crs, *img.bounds)
    return(bbox_warped)

def create_item(img_path, root):

    clc_name_elements = deconstruct_clc_name(img_path)

    asset_files = get_asset_files(root, clc_name=clc_name_elements['id'])
    asset_files = [f for f in asset_files if not f.endswith('aux')]
    year = clc_name_elements.get('reference_year')
    props = {'description': ITEM_DESCRIPTION.format(year=year),
            'created': None,
            'providers': CLC_PROVIDER.to_dict(),
    }

    with rio.open(img_path) as img:

        bbox = project_bbox(img)
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

    
    links = [CLMS_LICENSE, CLMS_CATALOG_LINK, ITEM_PARENT_LINK, COLLECTION_LINK]
    item.add_links(links)

    return(item)

