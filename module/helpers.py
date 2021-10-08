import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def get_with_retry(url, headers=None):
	"""
	WARNING: 1inch ALSO returns 500 if your args are wrong
	"""

	retries = Retry(total=5,
					backoff_factor=0.3,
					status_forcelist=[i for i in range(500, 600)])
	s = requests.Session()
	s.mount('https://', HTTPAdapter(max_retries=retries))
	r = s.get(url, headers=headers)

	return r
