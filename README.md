# Project Structure

This project contains 4 parts including `/stacs`, `/schema`, `/tests`, `/scripts`, and `/stac_prod`.

In the /stacs directory there are stac item and stac collection samples of a list of [Copernicus Land Monitoring Service products](https://git.sinergise.com/sh-vas/sh-vas/-/issues/1603) (CLMS products) and a stac catalog sample.

The /schema directory contains [JSON scehma](https://json-schema.org/) for validating STAC items and collections of CLMS products. Each CLMS product is paired with a shema which defines the schema of the item and the collection.

The /tests directory contains tests to validate STAC items, collections, and catalogs against the core STAC specification, the extensions, and the corresponding product schemas.

The /scripts directory contains the STAC generation package for 5 CLMS products, which can read either the GeoTIFF or XML to collect the necessary metadata and compile STAC items and collections. The scripts have been adapted to run in the Crunch environment.

The /stac_prod directory contains the STAC items and collections created in Crunch. Note that here we do not include STAC files of the full archive as GitHub is not a place for data storage.

<pre>
clms-stac/
│
├── .gitignore                    # Gitignore file to specify ignored files and directories
├── .github/workflows             # GitHub CI actions
├── .pre-commit-config.yaml        # Basic pre-commit config file
├── pyproject.toml                # TOML configuration file often used for tool settings and project metadata
├── README.md                     # Project README with an overview, setup, and usage instructions
├── requirements.txt              # File listing project dependencies
├── requirements-dev.txt          # File listing project dependencies for development
├── schema/                       # Directory for product schemas
├── tests/                        # Directory for tests
├── stacs/                        # Directory for STAC samples
├── scripts/                      # Directory for STAC generation package
├── stac_prod/                    # Directory for STAC files created in Crunch
├── create_clc_collection.py      # Wrapper to create Corine Land Cover STAC items and STAC collection in Crunch
├── create_euhydro_collection.py  # Wrapper to create EU-Hydro STAC collection in Crunch
├── create_n2k_collection.py      # Wrapper to create Natura2000 STAC collection in Crunch
├── create_uabh_item.py           # Wrapper to create Urban Atlas Building Height STAC items in Crunch
├── create_uabh_collection.py     # Wrapper to create Urban Atlas Building Height STAC collection in Crunch
├── create_vpp_items.py           # Wrapper to create High-resolution Vegetation Phenology and Productivity STAC items
└── create_vpp_collection.py      # Wrapper to create High-resolution Vegetation Phenology and Productivity STAC collection
</pre>

# Create STAC Items and Collections in Crunch

## Step 1: Create a Conda Environment

To isolate your project's dependencies in Crunch, create and activate a virtual environment with Anaconda.

```bash
# create a virtual environment named stac-prod
conda create -n env python=3.12

# acitvate the virtual environment
conda activate env
```

## Step 2: Install requirements

Next, install the requirements and requirements-dev.

```bash
conda install -c conda-forge boto3 pyproj pystac rasterio shapely jsonschema referencing
```

## Step 3: Execute the wrappers

To create Corine Land Cover items and collections:

```bash
python create_clc_collection.py
```

To create EU-Hydro collection:

```bash
python create_euhydro_collection.py
```

To create Natura2000 collection:

```bash
python create_n2k_collection.py
```

To create Urban Atlas Building Height items:

```bash
python create_uabh_items.py
```

To create Urban Atlas Building Height collection:

```bash
python create_uabh_collection.py
```

**Note** that `create_vpp_items.py` and `create_vpp_collection.py` can't be executed in Crunch as it requires access to the `s3://HRVPP/` bucket deployed at `http://data.cloudferro.com`.

# Setting Up a Virtual Environment and Running Pre-commit Hooks

## Step 1: Create and Activate a Virtual Environment

To isolate your project's dependencies, create and activate a virtual environment using Python's built-in `venv`:

```bash
# Create a virtual environment named "env"
python3 -m venv env

# Activate the virtual environment
#For Linux/MacOs
source env/bin/activate

# For Windows
.\env\Scripts\activate

```

## Step 2: Install requirements

Next, install requirements and requirements-dev.

```bash
# Ensure you are inside the activated virtual environment
# Install requirements using pip
pip install -r requirements-dev.txt -r requirements.txt
```

## Step 3: Install the Hooks

Install the pre-commit hooks defined in your configuration:

```bash
pre-commit install
```

## Step 4: Run the Hooks

The pre-commit hooks will now run automatically when you attempt to commit changes. To run the hooks manually, use the following command:

```bash
pre-commit run --all-files
```

This will execute the configured hooks on all files in the repository.

Now, whenever you attempt to commit changes, the hooks will be triggered, ensuring consistent formatting and code quality.
