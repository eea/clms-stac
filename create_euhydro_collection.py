import logging

from scripts.euhydro.collection import create_euhydro_collection

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(filename="create_euhydro_collection.log")
    create_euhydro_collection("<euhydro-root>")
