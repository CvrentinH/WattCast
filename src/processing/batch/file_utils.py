import zipfile
from io import BytesIO

import pandas as pd


def unzip(zip_bytes):
    zip_ref = zipfile.ZipFile(BytesIO(zip_bytes))
    names = [n for n in zip_ref.namelist() if not n.endswith("/") and not n.startswith("__MACOSX")]
    return zip_ref.open(names[0])

def convert_to_csv(xls_stream):
    df = pd.read_csv(xls_stream, sep="\t", encoding="latin-1", low_memory=False)
    return df.to_csv(index=False).encode("utf-8")
