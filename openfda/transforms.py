from typing import List, Optional, Dict, Any
import logging
from pydantic import ValidationError

from function_schemas import RecallRecord

logger = logging.getLogger(__name__)

class RecallTransformer:
    def transform_one(self, data: Dict[str, Any]) -> Optional[RecallRecord]:
        try:
            return RecallRecord(**data)
        except ValidationError as e:
            logger.warning(f"Validation error for recall {data.get('recall_number', 'unknown')}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error transforming recall: {e}")
            return None

    def transform_many(self, data: List[Dict[str, Any]]) -> List[RecallRecord]:
        return [
            record for item in data
            if (record := self.transform_one(item)) is not None
        ]