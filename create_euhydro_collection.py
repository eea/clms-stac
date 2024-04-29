import logging

from scripts.euhydro.collection import create_collection

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(filename="create_euhydro_collection.log")
    create_collection("<euhydro-root>")
