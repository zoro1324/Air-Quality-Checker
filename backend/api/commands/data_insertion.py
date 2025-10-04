
from openaq import OpenAQ
import decouple
import pandas as pd
import json
client = OpenAQ(api_key=decouple.config("OPENAQ_API"))
data = client.locations.list()
locations = data.results[0].__dict__

for location in locations:
    print(location)