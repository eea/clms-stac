import os
from datetime import datetime
from typing import Final

import boto3
import pystac
from pystac.link import Link
from pystac.provider import ProviderRole

AWS_SESSION = boto3.Session(profile_name="hrvpp")
BUCKET = "HRVPP"
CLMS_LICENSE: Final[Link] = Link(rel="license", target="https://land.copernicus.eu/en/data-policy")
COLLECTION_DESCRIPTION = (
    "Vegetation Phenology and Productivity Parameters (VPP) product is part of the Copernicus Land Monitoring Service"
    " (CLMS), pan-European High Resolution Vegetation Phenology and Productivity (HR-VPP) product suite. The VPP"
    " product is comprised of 13 parameters that describe specific stages of the seasonal vegetation growth cycle."
    " These parameters are extracted from Seasonal Trajectories of the Plant Phenology Index (PPI) derived from"
    " Sentinel-2 satellite observations at 10m resolution. Since growing seasons can traverse years, VPP parameters are"
    " provided for a maximum of two growing seasons per year. The parameters include (1) start of season (date, PPI"
    " value and slope), (2) end of season (date, PPI value and slope), (3)length of season, (4) minimum of season, (4)"
    " peak of the season (date and PPI value), (5) amplitude, (6) small integrated value and (7) large integrated"
    " value."
)
COLLECTION_EXTENT = pystac.Extent(
    spatial=pystac.SpatialExtent([[-25, 26, 45, 72]]),
    temporal=pystac.TemporalExtent([[datetime(year=2017, month=1, day=1), None]]),
)
COLLECTION_ID = "vegetation-phenology-and-productivity"
COLLECTION_KEYWORDS = [
    "agriculture",
    "clms",
    "derived data",
    "open data",
    "phenology",
    "plant phenology index",
    "vegetation",
]
COLLECTION_SUMMARIES = pystac.Summaries(
    {
        "proj:epsg": [
            32620,
            32621,
            32622,
            32625,
            32626,
            32627,
            32628,
            32629,
            32630,
            32631,
            32632,
            32633,
            32634,
            32635,
            32636,
            32637,
            32638,
            32738,
            32740,
        ]
    }
)
COLLECTION_TITLE = "Vegetation Phenology and Productivity Parameters"
STAC_DIR = "stac_tests"
TITLE_MAP = {
    "AMPL": "Season Amplitude",
    "EOSD": "Day of End-of-Season",
    "EOSV": "Vegetation Index Value at EOSD",
    "LENGTH": "Length of Season",
    "LSLOPE": "Slope of The Greening Up Period",
    "MAXD": "Day of Maximum-of-Season",
    "MAXV": "Vegetation Index Value at MAXD",
    "MINV": "Average Vegetation Index Value of Minima on Left and Right Sides of Each Season",
    "QFLAG": "Quality Flag",
    "RSLOPE": "Slope of The Senescent Period",
    "SOSD": "Day of Start-of-Season",
    "SOSV": "Vegetation Index Value at SOSD",
    "SPROD": "Seasonal Productivity",
    "TPROD": "Total Productivity",
}
VPP_HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides geographical information on land cover and its changes, land"
        " use, ground motions, vegetation state, water cycle and Earth's surface energy variables to a broad range of"
        " users in Europe and across the World in the field of environmental terrestrial applications."
    ),
    roles=[ProviderRole.LICENSOR, ProviderRole.HOST],
    url="https://land.copernicus.eu",
)
VPP_PRODUCER_AND_PROCESSOR: Final[pystac.Provider] = pystac.Provider(
    name="VITO NV",
    description=(
        "VITO is an independent Flemish research organisation in the area of cleantech and sustainable development."
    ),
    roles=[ProviderRole.PROCESSOR, ProviderRole.PRODUCER],
    url="https://vito.be",
)
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
