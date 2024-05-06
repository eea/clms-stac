import logging
from glob import glob

from scripts.uabh.item import create_uabh_item, get_stac_validator

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename="create_uabh_items.log")
    validator = get_stac_validator("schema/products/uabh.json")
    zip_list = glob("/Users/chung-xianghong/Downloads/uabh_samples/**/*.zip")
    for zip_file in zip_list:
        create_uabh_item(zip_file, validator)


if __name__ == "__main__":
    main()
