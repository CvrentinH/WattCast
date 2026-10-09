from dataclasses import dataclass

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from numpy.typing import NDArray
from openmeteo_sdk.VariablesWithTime import VariablesWithTime
from retry_requests import retry

from ingestion.batch.const import (
    OPENMETEO_DATA_REQUEST,
    OPENMETEO_URL_BASE,
    S3_KEY_TEMPLATE,
)
from ingestion.batch.fetchers import BaseFetcher


@dataclass
class OpenMeteoRequest:
    year: int
    latitude: float
    longitude: float

    def to_raw(self) -> dict:
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
    freq: pd.Timedelta
    data: dict[str, NDArray[np.float32]]

    def __init__(self, hourly: VariablesWithTime) -> None:
        if hourly.VariablesLength() != len(OPENMETEO_DATA_REQUEST):
            raise ValueError(
                "Open-Meteo response has an unexpected hourly variable count"
            )

        self.start = pd.to_datetime(hourly.Time(), unit="s", utc=True)
        self.end = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True)
        self.freq = pd.Timedelta(seconds=hourly.Interval())
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
                freq=self.freq,
                inclusive="left",
            ),
            **self.data,
        }
        df = pd.DataFrame(data=hourly_data)
        return df.to_csv(index=False, encoding="utf-8").encode("utf-8")


class OpenMeteo(BaseFetcher):
    def __init__(self, settings, year: int, latitude: float, longitude: float):
        super().__init__(settings)
        self.url = OPENMETEO_URL_BASE
        self.s3_key = (
            S3_KEY_TEMPLATE
            .replace("$SOURCE", "openmeteo")
            .replace("$YEAR", str(year))
            .replace("$EXT", "csv")
        )
        self.request = OpenMeteoRequest(
            year=year,
            latitude=latitude,
            longitude=longitude,
        )
        cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)

    def fetch(self) -> None:
        response = self.client.weather_api(self.url, params=self.request.to_raw())
        raw_hourly = response[0].Hourly()
        if raw_hourly is None:
            raise ValueError("Open-Meteo response has no hourly data")

        self.bucket.write(self.s3_key, OpenMeteoResponse(raw_hourly).to_csv())
