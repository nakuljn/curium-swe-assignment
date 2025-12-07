import json
import logging
from typing import Dict, Any, List

from openfda.client import OpenFDAClient
from openfda.transforms import RecallTransformer
from function_schemas import SearchRecallsInput, RecallClassification

logger = logging.getLogger(__name__)

class ToolService:
    def __init__(self):
        self.client = OpenFDAClient()
        self.transformer = RecallTransformer()

    def search_recalls(self, args: Dict[str, Any]) -> str:
        try:
            input_data = SearchRecallsInput(**args)
        except Exception as e:
            logger.error(f"Invalid arguments for search_recalls: {e}")
            return json.dumps({"error": f"Invalid arguments: {str(e)}"})

        query_parts = []
        if input_data.classification:
            query_parts.append(f'classification:"{input_data.classification.value}"')
        
        if input_data.year:
            # Date range filter for the specified year
            query_parts.append(f'recall_initiation_date:[{input_data.year}0101+TO+{input_data.year}1231]')
        
        if input_data.query:
            query_parts.append(f'(product_description:"{input_data.query}"+OR+reason_for_recall:"{input_data.query}")')

        search_query = "+AND+".join(query_parts) if query_parts else ""

        try:
            raw_data = self.client.search_enforcements(
                search_query=search_query, 
                limit=input_data.limit
            )
            
            if not raw_data or "results" not in raw_data:
                return json.dumps([])

            records = self.transformer.transform_many(raw_data["results"])
            return json.dumps([r.model_dump(mode='json') for r in records])
            
        except Exception as e:
            logger.error(f"Error executing search_recalls: {e}")
            return json.dumps({"error": "Failed to fetch recalls"})

    def get_recall_stats(self, args: Dict[str, Any] = None) -> str:
        try:
            # 1. Count by classification
            class_counts = self.client.count_enforcements("classification.exact")
            
            # 2. Count by status
            status_counts = self.client.count_enforcements("status.exact")
            
            # 3. Top recalling firms
            firm_counts = self.client.count_enforcements("recalling_firm.exact")

            stats = {
                "by_classification": class_counts.get("results", []) if class_counts else [],
                "by_status": status_counts.get("results", []) if status_counts else [],
                "top_firms": firm_counts.get("results", [])[:5] if firm_counts else []
            }
            
            return json.dumps(stats)
            
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return json.dumps({"error": "Failed to fetch statistics"})

    def get_assistant_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_recalls",
                    "description": "Search FDA drug recalls by keyword, classification, or year",
                    "parameters": SearchRecallsInput.model_json_schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recall_stats",
                    "description": "Get statistics about drug recalls (counts by classification, status, top firms)",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

    def execute(self, name: str, args_json: str) -> str:
        args = json.loads(args_json) if args_json else {}
        if name == "search_recalls":
            return self.search_recalls(args)
        elif name == "get_recall_stats":
            return self.get_recall_stats(args)
        return json.dumps({"error": f"Unknown tool: {name}"})