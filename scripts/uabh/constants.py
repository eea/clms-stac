import os
from typing import Final

import pystac
from pystac.link import Link
from pystac.provider import ProviderRole

HOST_AND_LICENSOR: Final[pystac.Provider] = pystac.Provider(
    name="Copernicus Land Monitoring Service",
    description=(
        "The Copernicus Land Monitoring Service provides "
        "geographical information on land cover and its "
        "changes, land use, ground motions, vegetation state, "
        "water cycle and Earth's surface energy variables to "
        "a broad range of users in Europe and across the "
        "World in the field of environmental terrestrial "
        "applications."
    ),
    roles=[ProviderRole.LICENSOR, ProviderRole.HOST],
    url="https://land.copernicus.eu",
)

COLLECTION_ID = "urban-atlas-building-height"

CLMS_LICENSE: Final[Link] = Link(rel="license", target="https://land.copernicus.eu/en/data-policy")

WORKING_DIR = os.getcwd()
STAC_DIR = "stac_tests"
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
