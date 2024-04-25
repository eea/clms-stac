import os
from typing import Final

import pystac
from pystac.link import Link
from pystac.provider import ProviderRole

WORKING_DIR = os.getcwd()
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
CLMS_LICENSE: Final[Link] = Link(rel="license", target="https://land.copernicus.eu/en/data-policy")
CLMS_CATALOG: Final[Link] = Link(
    rel=pystac.RelType.ROOT, target=pystac.STACObject.from_file(os.path.join(WORKING_DIR, "stacs/clms_catalog.json"))
)
PARENT: Final[Link] = Link(
    rel=pystac.RelType.PARENT,
    target=pystac.STACObject.from_file(
        os.path.join(
            WORKING_DIR, "stacs/vegetation-phenology-and-productivity/vegetation-phenology-and-productivity.json"
        )
    ),
)
COLLECTION: Final[Link] = Link(
    rel=pystac.RelType.COLLECTION,
    target=pystac.STACObject.from_file(
        os.path.join(
            WORKING_DIR, "stacs/vegetation-phenology-and-productivity/vegetation-phenology-and-productivity.json"
        )
    ),
)
