import logging

from scripts.clcplus.collection import create_collection, populate_collection

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename="create_clcplus_collection.log")
    collection = create_collection()
    populate_collection(collection, data_root="../Raster")


if __name__ == "__main__":
    main()
