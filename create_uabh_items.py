# crunch env setting
import os
import sys

os.environ["GDAL_DATA"] = os.path.join(f"{os.sep}".join(sys.executable.split(os.sep)[:-1]), "Library", "share", "gdal")

# common imports
import logging  # noqa: E402
from glob import glob  # noqa: E402

from scripts.uabh.item import create_uabh_item, get_stac_validator  # noqa: E402

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename="create_uabh_items.log")
    validator = get_stac_validator("schema/products/uabh.json")
    zip_list = glob("A:\\Copernicus\\UrbanAtlas\\BuildingHeight\\**\\*.zip")
    for zip_file in zip_list:
        create_uabh_item(zip_file, validator)


if __name__ == "__main__":
    main()
