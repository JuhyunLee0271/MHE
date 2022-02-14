from pyowm import OWM

class Weather:
    
    def __init__(self):
        self.API_KEY = "cb7685dd2aef284e5946c10e5a3e559d"
        self.owm = OWM(self.API_KEY)
        self.manager = self.owm.weather_manager()
        self.dict = {
                        'Seoul': [37.5665, 126.9780],
                        'Incheon': [37.3849391, 126.642785], 
                        'Gunpo' : [37.3617, 126.9352]
                    }

    # Get Weather by Coordinates by pyOWM API
    def getWeatherByCoords(self, city):
        latitude, longitude = self.dict[city]
        observation = self.manager.weather_at_coords(latitude, longitude)

        location = F"{observation.location.country}/{observation.location.name}"
        status = observation.weather.status
        temperature = observation.weather.temp['temp']
        humidity = observation.weather.humidity     

        return location, status, temperature, humidity, latitude, longitude
    
