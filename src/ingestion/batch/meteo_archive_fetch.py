from ingestion.batch.fetchers import BaseFetcher
import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
from dataclasses import dataclass, field
from ingestion.batch.const import OPENMETEO_URL_BASE, S3_KEY_TEMPLATE

@dataclass
class OpenMeteoRequest:
    year: int
    latitude: float
    longitude: float
    hourly: list[str] = field(
        default_factory=lambda: [
            "temperature_2m",
            "apparent_temperature",
            "wind_speed_10m",
            "cloud_cover",
            "relative_humidity_2m",
        ]
    )

    def to_raw(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": f"{self.year}-01-01",
            "end_date": f"{self.year}-12-31",
            "hourly": self.hourly,
        }

class OpenMeteoResponse:
    def __init__(self, hourly):
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            ),
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
            "apparent_temperature": hourly.Variables(1).ValuesAsNumpy(),
            "wind_speed_10m": hourly.Variables(2).ValuesAsNumpy(),
            "cloud_cover": hourly.Variables(3).ValuesAsNumpy(),
            "relative_humidity_2m": hourly.Variables(4).ValuesAsNumpy(),
        }
        self.dataframe = pd.DataFrame(data=hourly_data)

    def to_csv(self) -> bytes:
        return self.dataframe.to_csv(index=False, encoding="utf-8").encode("utf-8")


class OpenMeteo(BaseFetcher):

    def __init__(self, settings, year: int, latitude: float, longitude: float):
        super().__init__(settings)
        self.url = OPENMETEO_URL_BASE
        self.s3_key = S3_KEY_TEMPLATE.replace("$SOURCE", "openmeteo").replace("$YEAR", str(year))
        self.request = OpenMeteoRequest(
                    year=year,
                    latitude=latitude,
                    longitude=longitude,
                )
        cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        self.client = openmeteo_requests.Client(session = retry_session)

    def fetch(self):
        responses = self.client.weather_api(self.url, params = self.request.to_raw())
        raw_hourly = responses[0].Hourly()
        response = OpenMeteoResponse(raw_hourly)
        self.s3_body = response.to_csv()
        self.upload_to_bronze()
