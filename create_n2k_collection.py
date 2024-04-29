import logging

from scripts.n2k.collection import create_collection

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(filename="create_n2k_collection.log")
    create_collection("<path-to-n2k-root-directory>")
