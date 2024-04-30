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



def deconstruct_clc_name(filename: str):
    id = os.path.basename(filename).split('.')[0]
    p = re.compile(("U(?P<update_campaign>[0-9]{4})_"
                    "(?P<theme>CLC|CHA)(?P<reference_year>[0-9]{4})_"
                    "V(?P<release_year>[0-9]{4})_(?P<release_number>[0-9a-z]*)"
                    "_?(?P<country_code>[A-Z]*)?"
                    "_?(?P<DOM_code>[A-Z]*)?"))
    m = p.search(id)

    return(m.groupdict())


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
    
    DOM_DICT = {
        'GLP': 'Guadeloupe',
        'GUF': 'French Guyana',
        'MTQ': 'Martinique',
        'MYT': 'Mayotte',
        'REU': 'Réunion',
        '': 'Europe',
    }

    MEDIA_TYPE_DICT = {
        'tif': pystac.MediaType.COG,
        'tif_xml': pystac.MediaType.XML,
        'tif_aux_xml': pystac.MediaType.XML,
        'tif_ovr': 'image/tiff; application=geotiff; profile=pyramid',
        'tif_vat_cpg': pystac.MediaType.TEXT,
        'tif_vat_dbf': 'application/dbf',
        'txt': pystac.MediaType.TEXT,
        'tif_lyr': 'image/tiff; application=geotiff; profile=layer',
        'tfw': pystac.MediaType.TEXT,
        'xml': pystac.MediaType.XML,
    }
    
    label = DOM_DICT[DOM_code]
    
    TITLE_DICT = {
        'tif': f'Single Band Land Classification {label}',
        'tif_xml': f'TIFF Metadata {label}',
        'tif_aux_xml': f'TIFF Statistics {label}',
        'tif_ovr': f'Pyramid {label}',
        'tif_vat_cpg': f'Encoding {label}',
        'tif_vat_dbf': f'Database {label}',
        'txt': f'Legends {label}',
        'tif_lyr': f'Legend Layer {label}',
        'tfw': f'World File {label}',
        'xml': f'Single Band Land Classification Metadata {label}',
    }

    ROLES_DICT = {
        'tif': ['data', 'visual'],
        'tif_xml': ['metadata'],
        'tif_aux_xml': ['metadata'],
        'tif_ovr': ['metadata'],
        'tif_vat_cpg': ['metadata'],
        'tif_vat_dbf': ['metadata'],
        'txt': ['metadata'],
        'tif_lyr': ['metadata'],
        'tfw': ['metadata'],
        'xml': ['metadata'],
    }

    asset = pystac.Asset(href=filename, title=TITLE_DICT[suffix], media_type=MEDIA_TYPE_DICT[suffix], roles=ROLES_DICT[suffix])
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
            if file.startswith(clc_name + '.') or file.endswith((f'{clc_name_elements["DOM_code"]}.tif.lyr', 'QGIS.txt',)):
                asset_files.append(os.path.join(root, file))

    return(asset_files)
 
def project_bbox(img, target_epsg=4326):
    target_crs = rio.crs.CRS.from_epsg(target_epsg)
    bbox_warped = rio.warp.transform_bounds(img.crs, target_crs, *img.bounds)
    return(bbox_warped)


def create_item(img_path: str):
    clc_name_elements = deconstruct_clc_name(img_path)
    
    asset_files = get_asset_files(root, clc_name=clc_name_elements['id'])
    asset_files = [f for f in asset_files if not f.endswith('aux')]

    year = clc_name_elements.get('reference_year')

    CLC_PROVIDER = pystac.provider.Provider(
        name='Copernicus Land Monitoring Service',
        description=('The Copernicus Land Monitoring Service provides '
                    'geographical information on land cover and its '
                    'changes, land use, ground motions, vegetation state, '
                    'water cycle and Earth\'s surface energy variables to '
                    'a broad range of users in Europe and across the World '
                    'in the field of environmental terrestrial applications.'),
        roles=[ProviderRole.LICENSOR, ProviderRole.HOST],
        url='https://land.copernicus.eu'
    )

    props = {'description': (f'Corine Land Cover {year} (CLC{year}) is one of the Corine Land Cover (CLC) ' 
                             f'datasets produced within the frame the Copernicus Land Monitoring Service '
                             f'referring to land cover / land use status of year {year}. '
                             f'CLC service has a long-time heritage (formerly known as \"CORINE Land Cover Programme\"), '
                             f'coordinated by the European Environment Agency (EEA). It provides consistent '
                             f'and thematically detailed information on land cover and land cover changes across Europe. '
                             f'CLC datasets are based on the classification of satellite images produced by the national '
                             f'teams of the participating countries - the EEA members and cooperating countries (EEA39). '
                             f'National CLC inventories are then further integrated into a seamless land cover map of Europe. '
                             f'The resulting European database relies on standard methodology and nomenclature with following '
                             f'base parameters: 44 classes in the hierarchical 3-level CLC nomenclature; '
                             f'minimum mapping unit (MMU) for status layers is 25 hectares; '
                             f'minimum width of linear elements is 100 metres. '
                             f'Change layers have higher resolution, i.e. minimum mapping unit (MMU) is 5 hectares '
                             f'for Land Cover Changes (LCC), and the minimum width of linear elements is 100 metres. '
                             f'The CLC service delivers important data sets supporting the implementation of key priority '
                             f'areas of the Environment Action Programmes of the European Union as e.g. protecting ecosystems, '
                             f'halting the loss of biological diversity, tracking the impacts of climate change, '
                             f'monitoring urban land take, assessing developments in agriculture or dealing with '
                             f'water resources directives. CLC belongs to the Pan-European component of the '
                             f'Copernicus Land Monitoring Service (https://land.copernicus.eu/), part of the '
                             f'European Copernicus Programme coordinated by the European Environment Agency, '
                             f'providing environmental information from a combination of air- and space-based observation '
                             f'systems and in-situ monitoring. Additional information about CLC product description including '
                             f'mapping guides can be found at https://land.copernicus.eu/user-corner/technical-library/. '
                             f'CLC class descriptions can be found at '
                             f'https://land.copernicus.eu/user-corner/technical-library/corine-land-cover-nomenclature-guidelines/html/.'),
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
        # print(asset_file)
        key, asset = create_asset(asset_file, DOM_code=clc_name_elements.get('DOM_code'))
        item.add_asset(
            key=key,
            asset=asset,
        )

    proj_ext = ProjectionExtension.ext(item.assets[os.path.basename(img_path).replace('.', '_')], add_if_missing=True)
    proj_ext.apply(epsg=rio.crs.CRS(img.crs).to_epsg(),
                   bbox=img.bounds,
                   shape=[_ for _ in img.shape],
                   transform=[_ for _ in img.transform] + [0.0, 0.0, 1.0],
                   )

    license = pystac.link.Link(rel='LICENSE', target="https://land.copernicus.eu/en/data-policy")
    item.add_link(license)

    return(item)