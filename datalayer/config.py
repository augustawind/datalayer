import os

DATETIME_FMT = os.getenv('DATETIME_FMT', '%Y-%m-%dT%H:%M:%S.%fZ')
QUERYSTRING_SEP = os.getenv('QUERYSTRING_SEP', '__')
