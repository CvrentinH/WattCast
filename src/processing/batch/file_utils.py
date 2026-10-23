import zipfile
from io import BytesIO
from typing import IO

import pandas as pd


def unzip(zip_bytes: bytes) -> IO[bytes]:
	zip_ref = zipfile.ZipFile(BytesIO(zip_bytes))
	return zip_ref.open(zip_ref.namelist()[0])


def xls_to_csv(xls_stream: IO[bytes]) -> bytes:
	df = pd.read_csv(xls_stream, sep="\t", encoding="latin-1", low_memory=False)
	return df.to_csv(index=False).encode("utf-8")
