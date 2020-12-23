import requests
import time
import json
import sys
from future_manager import *

f = open('./log/LOG_EURUSD.txt', 'a')
sys.stdout = f
sys.stderr = f

if __name__ == "__main__":
    future_manager = Future_Manager()
    while True:
        future_manager.run()