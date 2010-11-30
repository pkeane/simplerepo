import re
import time

def rfc3339():
  return time.strftime('%Y-%m-%dT%H:%M:%S%z')

def dirify(str):
    str = re.sub('\&amp\;|\&', ' and ', str)
    str = re.sub('[-\s]+', '_', str)
    return re.sub('[^\w\s-]', '', str).strip().lower()
