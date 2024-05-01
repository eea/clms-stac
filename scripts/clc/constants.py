import os
from datetime import datetime, UTC

import pystac
from pystac.provider import ProviderRole



STAC_DIR = 'stac_tests'

# Collection
COLLECTION_ID = 'corine-land-cover-raster'
COLLECTION_TITLE = 'CORINE Land Cover Raster'
COLLECTION_DESCRIPTION = ("The European Commission launched the CORINE (Coordination of Information on the Environment) "
                          "program in an effort to develop a standardized methodology for producing continent-scale land "
                          "cover, biotope, and air quality maps. The CORINE Land Cover (CLC) product offers a pan-European "
                          "land cover and land use inventory with 44 thematic classes, ranging from broad forested areas "
                          "to individual vineyards.")
COLLECTION_KEYWORDS =  ["clms", "corine", "derived data", "land cover", "machine learning", "open data"]
COLLECTION_LICENSE = 'proprietary'

COLLITAS_TITLE_DICT = {
    'clc_map': 'Corine Land Cover Map',
    'clc_map_statistics': 'Corine Land Cover Map Statistics',
    'clc_map_pyramid': 'Pyramid',
    'clc_map_encoding': 'Encoding',
    'clc_map_database': 'Database',
    'clc_map_database_metadata': 'Database Metadata',
    'clc_map_tif_metadata': 'TIFF Metadata',
    'clc_map_metadata': 'Corine Land Cover Map Metadata',
}

COLLITAS_MEDIA_TYPE_DICT = {
    'clc_map': pystac.MediaType.COG,
    'clc_map_statistics': pystac.MediaType.XML,
    'clc_map_pyramid': 'image/tiff; application=geotiff; profile=pyramid',
    'clc_map_encoding': pystac.MediaType.TEXT,
    'clc_map_database': 'application/dbf',
    'clc_map_database_metadata': pystac.MediaType.TEXT,
    'clc_map_tif_metadata': 'image/tiff; application=geotiff; profile=layer',
    'clc_map_metadata': pystac.MediaType.XML,
}

COLLITAS_ROLES_DICT = {
    'clc_map': ['data'],
    'clc_map_statistics': ['metadata'],
    'clc_map_pyramid': ['metadata'],
    'clc_map_encoding': ['metadata'],
    'clc_map_database': ['metadata'],
    'clc_map_database_metadata': ['metadata'],
    'clc_map_tif_metadata': ['metadata'],
    'clc_map_metadata': ['metadata'],
}

# Items
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

TITLE_DICT = {
    'tif': 'Single Band Land Classification {label}',
    'tif_xml': 'TIFF Metadata {label}',
    'tif_aux_xml': 'TIFF Statistics {label}',
    'tif_ovr': 'Pyramid {label}',
    'tif_vat_cpg': 'Encoding {label}',
    'tif_vat_dbf': 'Database {label}',
    'txt': 'Legends {label}',
    'tif_lyr': 'Legend Layer {label}',
    'tfw': 'World File {label}',
    'xml': 'Single Band Land Classification Metadata {label}',
}

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


ITEM_DESCRIPTION = ('Corine Land Cover {year} (CLC{year}) is one of the Corine Land Cover (CLC) ' 
                    'datasets produced within the frame the Copernicus Land Monitoring Service '
                    'referring to land cover / land use status of year {year}. '
                    'CLC service has a long-time heritage (formerly known as \"CORINE Land Cover Programme\"), '
                    'coordinated by the European Environment Agency (EEA). It provides consistent '
                    'and thematically detailed information on land cover and land cover changes across Europe. '
                    'CLC datasets are based on the classification of satellite images produced by the national '
                    'teams of the participating countries - the EEA members and cooperating countries (EEA39). '
                    'National CLC inventories are then further integrated into a seamless land cover map of Europe. '
                    'The resulting European database relies on standard methodology and nomenclature with following '
                    'base parameters: 44 classes in the hierarchical 3-level CLC nomenclature; '
                    'minimum mapping unit (MMU) for status layers is 25 hectares; '
                    'minimum width of linear elements is 100 metres. '
                    'Change layers have higher resolution, i.e. minimum mapping unit (MMU) is 5 hectares '
                    'for Land Cover Changes (LCC), and the minimum width of linear elements is 100 metres. '
                    'The CLC service delivers important data sets supporting the implementation of key priority '
                    'areas of the Environment Action Programmes of the European Union as e.g. protecting ecosystems, '
                    'halting the loss of biological diversity, tracking the impacts of climate change, '
                    'monitoring urban land take, assessing developments in agriculture or dealing with '
                    'water resources directives. CLC belongs to the Pan-European component of the '
                    'Copernicus Land Monitoring Service (https://land.copernicus.eu/), part of the '
                    'European Copernicus Programme coordinated by the European Environment Agency, '
                    'providing environmental information from a combination of air- and space-based observation '
                    'systems and in-situ monitoring. Additional information about CLC product description including '
                    'mapping guides can be found at https://land.copernicus.eu/user-corner/technical-library/. '
                    'CLC class descriptions can be found at '
                    'https://land.copernicus.eu/user-corner/technical-library/corine-land-cover-nomenclature-guidelines/html/.')
