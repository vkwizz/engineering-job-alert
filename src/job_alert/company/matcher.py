from src.job_alert.config import config, CompanyEntry
from typing import Optional
import re

def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    return re.sub(r'[^\w]', '', name.lower())

class CompanyMatcher:
    def __init__(self):
        self.companies = config.companies.companies
        self._build_index()
        
    def _build_index(self):
        self.lookup = {}
        for comp in self.companies:
            self.lookup[normalize_company_name(comp.canonical_name)] = comp
            for alias in comp.aliases:
                self.lookup[normalize_company_name(alias)] = comp
                
    def match(self, name: str) -> Optional[CompanyEntry]:
        if not name:
            return None
        norm_name = normalize_company_name(name)
        return self.lookup.get(norm_name)

# Singleton instance
matcher = CompanyMatcher()
