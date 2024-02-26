from os import getenv
from oso_cloud import Oso

oso = Oso(url=getenv("OSO_URL", "https://api.osohq.com"), api_key=getenv("OSO_AUTH"))
