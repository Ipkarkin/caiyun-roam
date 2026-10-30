"""Constants for the Caiyun Roam integration."""

DOMAIN = "caiyun_roam"
DEFAULT_NAME = "Caiyun Roam"
DEFAULT_INTERVAL = 5  # minutes
CONF_TRACKER = "tracker_entity"
API_BASE = "https://api.caiyunapp.com/v2.5"
ATTRIBUTION = "Data provided by Colorfulclouds"

SKYCON_MAP = {
    "CLEAR_DAY": "sunny",
    "CLEAR_NIGHT": "clear-night",
    "PARTLY_CLOUDY_DAY": "partlycloudy",
    "PARTLY_CLOUDY_NIGHT": "partlycloudy",
    "CLOUDY": "cloudy",
    "LIGHT_HAZE": "fog",
    "MODERATE_HAZE": "fog",
    "HEAVY_HAZE": "fog",
    "FOG": "fog",
    "LIGHT_RAIN": "rainy",
    "MODERATE_RAIN": "rainy",
    "HEAVY_RAIN": "pouring",
    "STORM_RAIN": "lightning-rainy",
    "LIGHT_SNOW": "snowy",
    "MODERATE_SNOW": "snowy",
    "HEAVY_SNOW": "snowy",
    "STORM_SNOW": "snowy",
    "SLEET": "snowy-rainy",
    "HAIL": "hail",
    "WIND": "windy",
}
