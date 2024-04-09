import json

import jsonschema
import pytest
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

STAC_VERSION = "1.0.0"
PROJECT_ID = "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
ITEM_ASSETS_ID = "https://stac-extensions.github.io/item-assets/v1.0.0/schema.json"
RASTER_BANDS_ID = "https://stac-extensions.github.io/raster/v1.1.0/schema.json"


def test_core(stac_fixture, validator_fixture, stac_version="1.0.0"):
    for stac_dict in stac_fixture:
        assert validator_fixture.validate_core(stac_dict, stac_dict["type"], stac_version), f"{stac_dict.id} is invalid"


@pytest.mark.parametrize("extension_id", [PROJECT_ID, ITEM_ASSETS_ID])
def test_extensions(stac_fixture, validator_fixture, extension_id, stac_version=STAC_VERSION):
    for stac_dict in stac_fixture:
        if "stac_extensions" in stac_dict and extension_id in stac_dict["stac_extensions"]:
            validator_fixture.validate_extension(stac_dict, stac_dict["type"], stac_version, extension_id)


@pytest.mark.parametrize(
    ("product_id", "product_schema"),
    [
        ("corine-land-cover-raster", "schema/products/clc.json"),
        ("vegetation-phenology-and-productivity", "schema/products/vpp.json"),
        pytest.param(
            "river-and-lake-ice-extent-s2",
            "schema/products/rlie-s2.json",
            marks=pytest.mark.skip(reason="Schema not available"),
        ),
        pytest.param(
            "corine-land-cover-plus-raster",
            "schema/products/clcplus.json",
            marks=pytest.mark.skip(reason="Schema not available"),
        ),
        pytest.param(
            "imperviousness-built-up-10m",
            "schema/products/ibu.json",
            marks=pytest.mark.skip(reason="Schema not available"),
        ),
        pytest.param(
            "imperviousness-change-20m",
            "schema/products/imc.json",
            marks=pytest.mark.skip(reason="Schema not available"),
        ),
        pytest.param("natura20000", "schema/products/n2k.json", marks=pytest.mark.skip(reason="Schema not available")),
        pytest.param(
            "urban-atlas-building-height",
            "schema/products/uabh.json",
            marks=pytest.mark.skip(reason="Schema not available"),
        ),
        pytest.param(
            "urban-atlas-street-tree-layer",
            "schema/products/uastl.json",
            marks=pytest.mark.skip(reason="Schema not available"),
        ),
        pytest.param("eu-hydro", "schema/products/euhydro.json", marks=pytest.mark.skip(reason="Schema not available")),
    ],
)
def test_products(stac_fixture, product_id, product_schema):
    with open(product_schema) as f:
        schema = json.load(f)
    registry = Registry().with_resources(
        [("http://example.com/schema.json", Resource.from_contents(schema))],
    )
    validator = jsonschema.Draft7Validator({"$ref": "http://example.com/schema.json"}, registry=registry)
    for stac_dict in stac_fixture:
        is_collection = stac_dict["type"] == "Collection" and stac_dict["id"] == product_id
        is_item = stac_dict["type"] == "Feature" and stac_dict["collection"] == product_id
        if is_collection or is_item:
            error = best_match(validator.iter_errors(stac_dict))
            assert error is None, f"{stac_dict['id']} is invalid. Reason: {error.message}"
