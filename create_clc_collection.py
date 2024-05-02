import logging

from scripts.clc.collection import create_collection

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(filename="create_clc_collection.log")
    create_collection("<path-to-clc-root-directory>")