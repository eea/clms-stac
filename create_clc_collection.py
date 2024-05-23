# crunch env setting
import os
import sys

os.environ["GDAL_DATA"] = os.path.join(f"{os.sep}".join(sys.executable.split(os.sep)[:-1]), "Library", "share", "gdal")

# common imports
import logging  # noqa: E402

from scripts.clc.collection import create_collection, populate_collection  # noqa: E402

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename="create_clc_collection.log")
    collection = create_collection()
    populate_collection(
        collection,
        data_root="A:\\Copernicus\\CorineLandCover\\CorineLandCoverLegacy\\CorineLandCover\\Raster\\CLC_100m",
    )


if __name__ == "__main__":
    main()
