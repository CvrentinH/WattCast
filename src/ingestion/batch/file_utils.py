import zipfile
from io import BytesIO
import pandas as pd

def _unzip(zip_bytes):
    zip_ref = zipfile.ZipFile(BytesIO(zip_bytes))
    file_zip = zip_ref.namelist()[0]
    return zip_ref.open(file_zip)

def _xls_to_csv(xls_stream):
    df = pd.read_csv(xls_stream, sep="\t", encoding="latin-1", low_memory=False)
    return df.to_csv(index=False).encode("utf-8")
