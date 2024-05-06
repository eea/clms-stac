from scripts.ibu10m.collection import create_collection
from scripts.ibu10m.constants import COLLECTION_ID, STAC_DIR, WORKING_DIR

if __name__ == "__main__":
    create_collection(f"{WORKING_DIR}/{STAC_DIR}/{COLLECTION_ID}/IBU*.json")
