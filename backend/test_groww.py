import os
from growwapi import GrowwAPI

token = os.environ.get("GROWW_ACCESS_TOKEN", "")
print("Token loaded:", len(token))
