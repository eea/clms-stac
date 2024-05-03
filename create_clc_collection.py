import logging

from scripts.clc.collection import create_collection, populate_collection

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(filename="create_clc_collection.log")
    collection = create_collection()
    populate_collection(collection, data_root="../CLC_100m")