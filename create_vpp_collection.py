import logging

from scripts.vpp.collection import create_collection
from scripts.vpp.constants import COLLECTION_ID, STAC_DIR, WORKING_DIR

LOGGER = logging.getLogger(__name__)
if __name__ == "__main__":
    logging.basicConfig(filename="create_vpp_collection.log")
    create_collection(f"{WORKING_DIR}/{STAC_DIR}/{COLLECTION_ID}/**/VPP*.json")
