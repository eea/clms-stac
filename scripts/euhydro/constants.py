import os
from datetime import datetime
from typing import Final

import pystac
from pystac.link import Link
from pystac.provider import ProviderRole

COLLECTION_ID = "eu-hydro"
COLLECTION_DESCRIPTION = (
    "EU-Hydro is a dataset for all EEA38 countries and the United Kingdom providing photo-interpreted river network,"
    " consistent of surface interpretation of water bodies (lakes and wide rivers), and a drainage model (also called"
    " Drainage Network), derived from EU-DEM, with catchments and drainage lines and nodes."
)
COLLECTION_EXTENT = pystac.Extent(
    spatial=pystac.SpatialExtent([[-61.906047, -21.482245, 55.935919, 71.409109]]),
    temporal=pystac.TemporalExtent([[datetime(year=2006, month=1, day=1), datetime(year=2012, month=12, day=31)]]),
)
COLLECTION_TITLE = "EU-Hydro River Network Database"
COLLECTION_KEYWORDS = [
    "Hydrography",
    "Land cover",
    "River",
    "Environment",
    "Ocean",
    "Catchment area",
    "Land",
    "Hydrographic network",
    "Drainage system",
    "Hydrology",
    "Landscape alteration",
    "Inland water",
    "Canal",
    "Drainage",
    "Catchment",
    "Water body",
]
EUHYDRO_HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides geographical information on land cover and its changes, land"
        " use, ground motions, vegetation state, water cycle and Earth's surface energy variables to a broad range of"
        " users in Europe and across the World in the field of environmental terrestrial applications."
    ),
    roles=[ProviderRole.LICENSOR, ProviderRole.HOST],
    url="https://land.copernicus.eu",
)
CLMS_LICENSE: Final[Link] = Link(rel="license", target="https://land.copernicus.eu/en/data-policy")
WORKING_DIR = os.getcwd()
STAC_DIR = "stac_tests"
