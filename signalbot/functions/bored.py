"""Bored module."""

import urllib3
import json


class Bored:
    """Defining base class for inheritence."""

    @staticmethod
    def bored():
        """Get random recommendations from boredapi."""
        http = urllib3.PoolManager()
        req_return = http.request('GET', 'https://www.boredapi.com/api/activity?type=recreational')
        activity_data = json.loads(req_return.data.decode('utf-8'))
        return activity_data['activity']
