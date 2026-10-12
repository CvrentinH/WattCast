import zipfile
from io import BytesIO

import pandas as pd


def unzip(zip_bytes):
    zip_ref = zipfile.ZipFile(BytesIO(zip_bytes))
    return zip_ref.open(zip_ref.namelist()[0])

def convert_to_csv(xls_stream):
    df = pd.read_csv(xls_stream, sep="\t", encoding="latin-1", low_memory=False)
    return df.to_csv(index=False).encode("utf-8")
