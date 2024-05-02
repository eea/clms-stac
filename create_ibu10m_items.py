import os

# from tqdm import tqdm
from scripts.ibu10m.item import create_ibu10m_item

SAMPLE_DIR = "/Users/joshua.chung/clms-stac/scripts/samples/ibu10m/IBU_2018_010m_al_03035_v010/DATA"


def matching_files(directory: str):
    tif_files = {}
    tfw_files = {}
    tif_vat_dbf_files = {}

    for root, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)

            if file.endswith(".tif.vat.dbf"):
                base_name = file[:-12]
                tif_vat_dbf_files[base_name] = full_path
            else:
                base_name, extension = os.path.splitext(file)

                if extension.lower() == ".tif":
                    tif_files[base_name] = full_path
                elif extension.lower() == ".tfw":
                    tfw_files[base_name] = full_path

    result = []

    for base_name in tif_files:
        if base_name in tfw_files and base_name in tif_vat_dbf_files:
            result.append([tif_files[base_name], tfw_files[base_name], tif_vat_dbf_files[base_name]])

    return result


if __name__ == "__main__":
    matching_files_list = matching_files(SAMPLE_DIR)
    for tile_path, worldfile_path, _ in matching_files_list:
        create_ibu10m_item(tile_path, worldfile_path)
