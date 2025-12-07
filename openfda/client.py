import requests
import os


class OpenFDAClient:
    def __init__(self):
        self.base_url = os.getenv("OPENFDA_API_URL", "https://api.fda.gov/drug/enforcement.json")
    
    def _build_params(self, limit, skip, count, search):
        params = {}
        if limit != -1:
            params["limit"] = limit
        if skip != -1:
            params["skip"] = skip
        if count:
            params["count"] = count
        if search:
            params["search"] = search
        return params
    
    def fetch_recalls(self, limit=-1, skip=-1, count=None, search=""):
        params = self._build_params(limit, skip, count, search)
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    def search_enforcements(self, search_query="", limit=10, skip=0):
        return self.fetch_recalls(limit=limit, skip=skip, search=search_query)
    
    def count_enforcements(self, field_name):
        return self.fetch_recalls(count=field_name)