import os

from scripts.ibu10m.item import create_ibu10m_item

SAMPLE_DIR = "/Users/joshua.chung/clms-stac/sample_data"


def matching_files(directory: str) -> list[list[str]]:
    tif_files = {}
    tfw_files = {}

    for root, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)

            base_name, extension = os.path.splitext(file)

            if extension.lower() == ".tif" and base_name not in tif_files:
                tif_files[base_name] = full_path
            elif extension.lower() == ".tfw" and base_name not in tfw_files:
                tfw_files[base_name] = full_path

    return [(tif_files[base_name], tfw_files[base_name]) for base_name in tif_files if base_name in tfw_files]


def find_metadata(directory: str) -> str:
    metadata_path = ""
    for root, _, files in os.walk(directory):
        for file in files:
            base_name, extension = os.path.splitext(file)
            if extension.lower() == ".xml":
                metadata_path = os.path.join(root, file)
    return metadata_path


if __name__ == "__main__":
    metadata_path = find_metadata(SAMPLE_DIR)
    matching_files_list = matching_files(SAMPLE_DIR)
    if len(matching_files_list) == len(set(matching_files_list)):
        for tile_path, worldfile_path in matching_files_list:
            create_ibu10m_item(tile_path, worldfile_path, metadata_path)
