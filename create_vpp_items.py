import itertools as it
import logging
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

from scripts.vpp.constants import AWS_SESSION, BUCKET
from scripts.vpp.item import create_page_iterator, create_product_list, create_vpp_item, get_stac_validator

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename="create_vpp_items.log")
    validator = get_stac_validator("schema/products/vpp.json")
    product_list = create_product_list(2017, 2023)

    for product in product_list:
        page_iterator = create_page_iterator(AWS_SESSION, BUCKET, product)
        for page in page_iterator:
            tiles = [prefix["Prefix"] for prefix in page["CommonPrefixes"]]
            with ThreadPoolExecutor(max_workers=100) as executor:
                list(
                    tqdm(
                        executor.map(
                            create_vpp_item, it.repeat(AWS_SESSION), it.repeat(BUCKET), it.repeat(validator), tiles
                        ),
                        total=len(tiles),
                    )
                )


if __name__ == "__main__":
    main()
