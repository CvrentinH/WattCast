from typing import Dict
from ingestion.batch.fetchers import BaseFetcher
import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
from dataclasses import dataclass, field
from ingestion.batch.const import (
    OPENMETEO_URL_BASE,
    S3_KEY_TEMPLATE,
    OPENMETEO_DATA_REQUEST,
)


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
    start: pd.Date
    end: pd.Date
    freq: pd.Delta
    data: Dict

    def __init__(self, hourly):
        self.start = pd.to_datetime(hourly.Time(), unit="s", utc=True)
        self.end = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True)
        self.freq = pd.Timedelta(seconds=hourly.Interval())
        i = 0
        for label in OPENMETEO_DATA_REQUEST:
            self.data[label] = hourly.Variables(i).ValuesAsNumpy()
            i += 1

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
        self.s3_key = S3_KEY_TEMPLATE.replace("$SOURCE", "openmeteo").replace(
            "$YEAR", str(year)
        )
        self.request = OpenMeteoRequest(
            year=year,
            latitude=latitude,
            longitude=longitude,
        )
        cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)

    def fetch(self):
        responses = self.client.weather_api(self.url, params=self.request.to_raw())
        raw_hourly = responses[0].Hourly()
        response = OpenMeteoResponse(raw_hourly)
        self.s3_body = response.to_csv()
        self.upload_to_bronze()
