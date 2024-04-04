# Project Structure

This project contains 4 parts including `/stacs`, `/schema`, `/tests`.

In the /stacs directory there are stac item and stac collection samples of a list of [Copernicus Land Monitoring Service products](https://git.sinergise.com/sh-vas/sh-vas/-/issues/1603) (CLMS products) and a stac catalog sample.

The /schema directory contains [JSON scehma](https://json-schema.org/) for validating STAC items and collections of CLMS products. Each CLMS product is paired with a shema which defines the schema of the item and the collection.

The /tests directory contains tests to validate STAC items, collections, and catalogs against the core STAC specification, the extensions, and the corresponding product schemas.

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
└── stacs/                        # Directory for STAC samples
</pre>

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
