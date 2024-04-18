import io

import boto3
import rasterio as rio

AWS_SESSION = boto3.Session(profile_name="hrvpp")
BUCKET = "HRVPP"
KEY = "CLMS/Pan-European/Biophysical/VPP/v01/2023/s2/VPP_2023_S2_T40KCC-010m_V105_s2_TPROD.tif"


def read_metadata_from_s3(bucket, key, aws_session):
    s3 = aws_session.resource("s3")
    obj = s3.Object(bucket, key)
    body = obj.get()["Body"].read()
    with rio.open(io.BytesIO(body)) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    return {"bounds": bounds, "crs": crs, "height": height, "width": width}


def read_metadata_from_url(url):
    with rio.open(url) as tif:
        bounds = tif.bounds
        crs = tif.crs
        height = tif.height
        width = tif.width
    return {"bounds": bounds, "crs": crs, "height": height, "width": width}
