import requests
import time
import json
from future_manager import *

if __name__ == "__main__":
    future_manager = Future_Manager()
    while True:
        future_manager.run()