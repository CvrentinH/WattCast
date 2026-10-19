from dataclasses import dataclass
from typing import Any

import niquests
import numpy as np
import openmeteo_requests
import pandas as pd
from niquests.exceptions import RequestException
from numpy.typing import NDArray
from openmeteo_requests.Client import OpenMeteoRequestsError
from openmeteo_sdk.VariablesWithTime import VariablesWithTime
from urllib3.util import Retry

from common.config import Settings
from common.exceptions import FetchError
from ingestion.batch.const import (
	OPENMETEO_BACKOFF_FACTOR,
	OPENMETEO_DATA_REQUEST,
	OPENMETEO_MAX_RETRIES,
	OPENMETEO_URL_BASE,
	S3_KEY_TEMPLATE,
)
from ingestion.batch.fetchers import BaseFetcher


@dataclass
class OpenMeteoRequest:
	year: int
	latitude: float
	longitude: float

	def to_raw(self) -> dict[str, Any]:
		return {
			"latitude": self.latitude,
			"longitude": self.longitude,
			"start_date": f"{self.year}-01-01",
			"end_date": f"{self.year}-12-31",
			"hourly": OPENMETEO_DATA_REQUEST,
		}


class OpenMeteoResponse:
	start: pd.Timestamp
	end: pd.Timestamp
	freq: int
	data: dict[str, NDArray[np.float32]]

	def __init__(self, hourly: VariablesWithTime) -> None:
		if hourly.VariablesLength() != len(OPENMETEO_DATA_REQUEST):
			raise ValueError("Open-Meteo response has an unexpected hourly variable count")

		self.start = pd.to_datetime(hourly.Time(), unit="s", utc=True)
		self.end = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True)
		self.freq = hourly.Interval()
		self.data = {}

		for i, label in enumerate(OPENMETEO_DATA_REQUEST):
			variable = hourly.Variables(i)
			if variable is None:
				raise ValueError(f"Missing hourly variable: {label}")

			values = variable.ValuesAsNumpy()
			if not isinstance(values, np.ndarray):
				raise TypeError(f"Missing hourly values: {label}")

			self.data[label] = values

	def to_csv(self) -> bytes:
		hourly_data = {
			"date": pd.date_range(
				start=self.start,
				end=self.end,
				freq= pd.Timedelta(seconds=self.freq),
				inclusive="left",
			),
			**self.data,
		}
		df = pd.DataFrame(data=hourly_data)
		return df.to_csv(index=False, encoding="utf-8").encode("utf-8")


class OpenMeteo(BaseFetcher):
	def __init__(self, settings: Settings, year: int, latitude: float, longitude: float) -> None:
		super().__init__(settings)
		self.url = OPENMETEO_URL_BASE
		self.s3_key = S3_KEY_TEMPLATE("openmeteo", str(year), "csv")
		self.request = OpenMeteoRequest(
			year=year,
			latitude=latitude,
			longitude=longitude,
		)
		session = niquests.Session(retries=Retry(total=OPENMETEO_MAX_RETRIES, backoff_factor=OPENMETEO_BACKOFF_FACTOR))
		self.client = openmeteo_requests.Client(session=session)

	def fetch(self) -> None:
		try:
			response = self.client.weather_api(self.url, params=self.request.to_raw())
		except (RequestException, OpenMeteoRequestsError) as e:
			raise FetchError(f"Open-Meteo request failed (year={self.request.year})") from e

		raw_hourly = response[0].Hourly()
		if raw_hourly is None:
			raise FetchError("Open-Meteo response has no hourly data")

		self.bucket.write(self.s3_key, OpenMeteoResponse(raw_hourly).to_csv())
