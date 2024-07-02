import logging
from glob import glob

from scripts.ibu10m.collection import create_ibu10m_collection, get_stac_validator
from scripts.ibu10m.constants import COLLECTION_ID, STAC_DIR, WORKING_DIR

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename="create_ibu10m_collection.log")
    item_list = glob(f"{WORKING_DIR}/{STAC_DIR}/{COLLECTION_ID}/**/*.json")
    validator = get_stac_validator("schema/products/ibu10m.json")
    create_ibu10m_collection(item_list, validator)


if __name__ == "__main__":
    main()
