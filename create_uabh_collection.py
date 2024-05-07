import logging
from glob import glob

from scripts.uabh.collection import create_uabh_collection, get_stac_validator
from scripts.uabh.constants import COLLECTION_ID, STAC_DIR, WORKING_DIR

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename="create_uabh_collection.log")
    item_list = glob(f"{WORKING_DIR}/{STAC_DIR}/{COLLECTION_ID}/**/*.json")
    validator = get_stac_validator("schema/products/uabh.json")
    create_uabh_collection(item_list, validator)


if __name__ == "__main__":
    main()
