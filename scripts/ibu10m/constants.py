import os
from datetime import datetime
from typing import Final

import pystac
from pystac.link import Link
from pystac.provider import ProviderRole

CLMS_LICENSE: Final[Link] = Link(rel="license", target="https://land.copernicus.eu/en/data-policy")
COLLECTION_ID = "imperviousness-built-up-10m"
COLLECTION_TITLE = "High Resolution Layer Imperviousness Built-up 10m"
COLLECTION_DESCRIPTION = (
    "The Impervious Built-up layer is a thematic product showing the binary information of building (class 1)"
    " and no building (class 0) within the sealing outline derived from the IMD 2018 for the period 2018 for the"
    " EEA-39 area."
)
COLLECTION_EXTENT = pystac.Extent(
    spatial=pystac.SpatialExtent([[-31.285, 27.642, 44.807, 71.165]]),
    temporal=pystac.TemporalExtent([[datetime(year=2018, month=1, day=1), None]]),
)
COLLECTION_KEYWORDS = [
    "Copernicus",
    "Imperviousness",
    "Built-up",
    "IBU",
    "High Resolution Layer",
    "Land cover",
    "Buildings",
]
COLLECTION_SUMMARIES = pystac.Summaries({"proj:epsg": [3035]})
IBU10M_HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides geographical information on land cover and its changes, land"
        " use, ground motions, vegetation state, water cycle and Earth's surface energy variables to a broad range of"
        " users in Europe and across the World in the field of environmental terrestrial applications."
    ),
    roles=[ProviderRole.LICENSOR, ProviderRole.HOST],
    url="https://land.copernicus.eu/en",
)
STAC_DIR = "stac_tests"
WORKING_DIR = os.getcwd()
CLMS_CATALOG_LINK: Final[Link] = Link(
    rel=pystac.RelType.ROOT, target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, "stacs/clms_catalog.json"))
)
COLLECTION_LINK: Final[Link] = Link(
    rel=pystac.RelType.COLLECTION,
    target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"stacs/{COLLECTION_ID}/{COLLECTION_ID}.json")),
)
ITEM_PARENT_LINK: Final[Link] = Link(
    rel=pystac.RelType.PARENT,
    target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, f"stacs/{COLLECTION_ID}/{COLLECTION_ID}.json")),
)
IBU10M_DATA_DIR = "/Users/chung-xianghong/Downloads/ibu10m_samples"
