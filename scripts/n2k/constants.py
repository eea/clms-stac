import os
from datetime import datetime
from typing import Final

import pystac
from pystac.link import Link
from pystac.provider import ProviderRole

COLLECTION_ID = "natura2000"
COLLECTION_DESCRIPTION = (
    "The Copernicus Land Cover/Land Use (LC/LU) status map as part of the Copernicus Land Monitoring Service (CLMS)"
    " Local Component, tailored to the needs of biodiversity monitoring in selected Natura2000 sites (4790 sites of"
    " natural and semi-natural grassland formations listed in Annex I of the Habitats Directive) including a 2km buffer"
    " zone surrounding the sites and covering an area of 631.820 km² across Europe. LC/LU is extracted from VHR"
    " satellite data and other available data."
)
COLLECTION_EXTENT = pystac.Extent(
    spatial=pystac.SpatialExtent([[-16.82, 27.87, 33.17, 66.79]]),
    temporal=pystac.TemporalExtent([[datetime(year=2006, month=1, day=1), None]]),
)
COLLECTION_TITLE = "Natura 2000 Land Cover/Land Use Status"
COLLECTION_KEYWORDS = [
    "Copernicus",
    "Satellite image interpretation",
    "Land monitoring",
    "Land",
    "Landscape alteration",
    "Land use",
    "Land cover",
    "Landscape",
]
N2K_HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
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
STAC_DIR = "stac_prod"
