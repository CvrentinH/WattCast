from ingestion.batch.fetchers import BaseFetcher
import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
from common.config import get_settings


class OpenMeteo(BaseFetcher):

    def __init__(self, settings):
        super().__init__(settings)        

    def fetch(self):
        for year in range(2021, 2025):
            url = "https://archive-api.open-meteo.com/v1/archive"
            s3_key = f"raw/meteo/year={year}/meteo_{year}.csv"

            cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
            retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
            openmeteo = openmeteo_requests.Client(session = retry_session)

            params = {
            "latitude": 46,
            "longitude": 2,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "hourly": ["temperature_2m", "apparent_temperature", "wind_speed_10m", "cloud_cover", "relative_humidity_2m"],
            }
            responses = openmeteo.weather_api(url, params = params)
            response = responses[0]

            hourly = response.Hourly()
            hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
            hourly_apparent_temperature = hourly.Variables(1).ValuesAsNumpy()
            hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
            hourly_cloud_cover = hourly.Variables(3).ValuesAsNumpy()
            hourly_relative_humidity_2m = hourly.Variables(4).ValuesAsNumpy()

            hourly_data = {
            "date": pd.date_range(
                start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
                end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
                freq = pd.Timedelta(seconds = hourly.Interval()),
                inclusive = "left"
            )
            }

            hourly_data["temperature_2m"] = hourly_temperature_2m
            hourly_data["apparent_temperature"] = hourly_apparent_temperature
            hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
            hourly_data["cloud_cover"] = hourly_cloud_cover
            hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m

            hourly_dataframe = pd.DataFrame(data = hourly_data)
            body = hourly_dataframe.to_csv(index=False, encoding="utf-8").encode("utf-8")

            self.upload_to_bronze(s3_key, body)

if __name__ == "__main__":
    settings = get_settings()
    OM = OpenMeteo(settings)
    OM.fetch()