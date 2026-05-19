from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, url: str) -> Dict[str, Any]:
        """Perform the scrape and return a dict with keys: raw_html, extracted_text, metadata"""
        raise NotImplementedError
