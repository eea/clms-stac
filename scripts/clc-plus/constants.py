import os

import pystac
from pystac.provider import ProviderRole

# os.chdir('x:\\projects\\ETC-DI\\Task_18\\clms-stac')
WORKING_DIR = os.getcwd()

STAC_DIR = "stac_tests"

# Collection
COLLECTION_ID = "corine-land-cover-plus-raster"
COLLECTION_TITLE = "CORINE Land Cover Plus Backbone"
COLLECTION_DESCRIPTION = (
    "The CLC+ Backbone constitutes the first component of the CLMS's new 'CLC+ Product Suite', "
    "which represents a true paradigm change in European land cover/land use (LC/LU) monitoring, "
    "building on the rich legacy of the European CORINE Land Cover (CLC) flagship product. "
    "The CLC+ Backbone is an object-oriented, large scale, wall-to-wall (EEA-38 + UK), "
    "high-resolution (HR) inventory of European LC in a vector format accompanied by a "
    "raster product layer, providing a consistent pan-European geometric backbone of "
    "Landscape Objects with limited, but robust thematic detail, on which many other "
    "applications can be built."
)
COLLECTION_KEYWORDS = ["Copernicus", "Land Monitoring", "Land Cover", "CLC+"]
COLLECTION_LICENSE = "proprietary"


COLLECTION_TITLE_MAP = {
    "clc_country_coverage": "Coverage",
    "clc_file_naming": "Naming Convention Description",
    "readme": "Description",
}

COLLECTION_MEDIA_TYPE_MAP = {
    "clc_country_coverage": pystac.MediaType.PDF,
    "clc_file_naming": pystac.MediaType.TEXT,
    "readme": pystac.MediaType.TEXT,
}

COLLECTION_ROLES_MAP = {
    "clc_country_coverage": ["metadata"],
    "clc_file_naming": ["metadata"],
    "readme": ["metadata"],
}

# Items

CLMS_LICENSE = pystac.link.Link(
    rel=pystac.RelType.LICENSE,
    target="https://land.copernicus.eu/en/data-policy",
    title="Legal notice on the use of CLMS data",
)

EXTENT_MAP = {
    "gp": "Guadeloupe",
    "gf": "French Guyana",
    "mq": "Martinique",
    "yt": "Mayotte",
    "re": "Réunion",
    "eu": "Europe",
}

ITEM_MEDIA_TYPE_MAP = {
    "tif": pystac.MediaType.COG,
    "xml": pystac.MediaType.XML,
    "tif_aux_xml": pystac.MediaType.XML,
    "tif_clr": pystac.MediaType.TEXT,
    "tif_clr_txt": pystac.MediaType.TEXT,
    "tif_ovr": "image/tiff; application=geotiff; profile=pyramid",
    "tif_vat_cpg": pystac.MediaType.TEXT,
    "tif_vat_dbf": "application/dbf",
    "tif_vat_dbf_xml": pystac.MediaType.XML,
    "lyrx": "image/tiff; application=geotiff; profile=layer",
    "qml": "image/tiff; application=geotiff; profile=layer",
    "sld": pystac.MediaType.XML,
}

ITEM_ROLES_MAP = {
    "tif": ["data", "visual"],
    "xml": ["metadata"],
    "tif_aux_xml": ["metadata"],
    "tif_clr": ["metadata"],
    "tif_clr_txt": ["metadata"],
    "tif_ovr": ["metadata"],
    "tif_vat_cpg": ["metadata"],
    "tif_vat_dbf": ["metadata"],
    "tif_vat_dbf_xml": ["metadata"],
    "lyrx": ["metadata"],
    "qml": ["metadata"],
    "sld": ["metadata"],
}

ITEM_TITLE_MAP = {
    "tif": "Classification Map {label}",
    "xml": "Classification Map Metadata {label}",
    "tif_aux_xml": "Classification Map Auxiliary {label}",
    "tif_clr": "Classification Map Color Palette CLR {label}",
    "tif_clr_txt": "Classification Map Color Palette TXT CLR {label}",
    "tif_ovr": "Classification Map Pyramid {label}",
    "tif_vat_cpg": "Classification Map Encoding {label}",
    "tif_vat_dbf": "Classificaiton Map Database {label}",
    "tif_vat_dbf_xml": "Classificaiton Map Database XML {label}",
    "lyrx": "Classification Map ArcGIS Legend Layer {label}",
    "qml": "Classification Map QGIS Legend Layer {label}",
    "sld": "Classification Map OGC Legend Layer {label}",
}

ITEM_KEY_MAP = {
    "tif": "clcplus_map",
    "xml": "clcplus_map_metadata",
    "tif_aux_xml": "clcplus_map_auxiliary",
    "tif_clr": "clcplus_map_color_palette_clr",
    "tif_clr_txt": "clcplus_map_color_palette_txt",
    "tif_ovr": "clcplus_map_pyramid",
    "tif_vat_cpg": "clcplus_map_encoding",
    "tif_vat_dbf": "clcplus_map_database_dbf",
    "tif_vat_dbf_xml": "clcplus_map_database_xml",
    "lyrx": "clcplus_map_arcgis_legend_layer",
    "qml": "clcplus_map_qgis_legend_layer",
    "sld": "clcplus_map_ogc_legend_layer",
}

CLC_PROVIDER = pystac.provider.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides "
        "geographical information on land cover and its "
        "changes, land use, ground motions, vegetation state, "
        "water cycle and Earth's surface energy variables to "
        "a broad range of users in Europe and across the World "
        "in the field of environmental terrestrial applications."
    ),
    roles=[ProviderRole.LICENSOR, ProviderRole.HOST],
    url="https://land.copernicus.eu",
)


ITEM_DESCRIPTION = (
    "Corine Land Cover {year} (CLC{year}) is one of the Corine Land Cover (CLC) "
    "datasets produced within the frame the Copernicus Land Monitoring Service "
    "referring to land cover / land use status of year {year}. "
    'CLC service has a long-time heritage (formerly known as "CORINE Land Cover Programme"), '
    "coordinated by the European Environment Agency (EEA). It provides consistent "
    "and thematically detailed information on land cover and land cover changes across Europe. "
    "CLC datasets are based on the classification of satellite images produced by the national "
    "teams of the participating countries - the EEA members and cooperating countries (EEA39). "
    "National CLC inventories are then further integrated into a seamless land cover map of Europe. "
    "The resulting European database relies on standard methodology and nomenclature with following "
    "base parameters: 44 classes in the hierarchical 3-level CLC nomenclature; "
    "minimum mapping unit (MMU) for status layers is 25 hectares; "
    "minimum width of linear elements is 100 metres. "
    "Change layers have higher resolution, i.e. minimum mapping unit (MMU) is 5 hectares "
    "for Land Cover Changes (LCC), and the minimum width of linear elements is 100 metres. "
    "The CLC service delivers important data sets supporting the implementation of key priority "
    "areas of the Environment Action Programmes of the European Union as e.g. protecting ecosystems, "
    "halting the loss of biological diversity, tracking the impacts of climate change, "
    "monitoring urban land take, assessing developments in agriculture or dealing with "
    "water resources directives. CLC belongs to the Pan-European component of the "
    "Copernicus Land Monitoring Service (https://land.copernicus.eu/), part of the "
    "European Copernicus Programme coordinated by the European Environment Agency, "
    "providing environmental information from a combination of air- and space-based observation "
    "systems and in-situ monitoring. Additional information about CLC product description including "
    "mapping guides can be found at https://land.copernicus.eu/user-corner/technical-library/. "
    "CLC class descriptions can be found at "
    "https://land.copernicus.eu/user-corner/technical-library/corine-land-cover-nomenclature-guidelines/html/."
)
