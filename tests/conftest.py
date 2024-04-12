import json
from glob import glob

import pytest
from pystac.validation.stac_validator import JsonSchemaSTACValidator


@pytest.fixture(scope="session")
def stac_fixture():
    stac_list = glob("stacs/**/*.json", recursive=True)
    return [(stac.split("/")[-1].split(".")[0], read_stac(stac)) for stac in stac_list]


@pytest.fixture(scope="session")
def validator_fixture():
    return JsonSchemaSTACValidator()


def read_stac(path):
    with open(path) as f:
        return json.load(f)
