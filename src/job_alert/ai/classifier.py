import logging
import json
from typing import Optional
from openai import OpenAI
from src.job_alert.config import config
from src.job_alert.ai.schemas import JobClassification
from src.job_alert.ai.prompts import CLASSIFIER_SYSTEM_PROMPT
from src.job_alert.normalization.schemas import NormalizedJob

logger = logging.getLogger(__name__)

class AIClassifier:
    def __init__(self):
        self.groq_key = config.groq_api_key
        self.openai_key = config.openai_api_key
        
        if self.groq_key:
            logger.info("Initializing AI Classifier with Groq API (llama-3.3-70b-versatile)...")
            self.client = OpenAI(
                api_key=self.groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = "llama-3.3-70b-versatile"
            self.provider = "groq"
        elif self.openai_key:
            logger.info("Initializing AI Classifier with OpenAI API (gpt-4o-mini)...")
            self.client = OpenAI(api_key=self.openai_key)
            self.model = "gpt-4o-mini"
            self.provider = "openai"
        else:
            self.client = None
            self.provider = None

    def classify_job(self, job: NormalizedJob) -> Optional[JobClassification]:
        if not self.client:
            logger.warning("Neither GROQ_API_KEY nor OPENAI_API_KEY configured; skipping AI classification")
            return None

        content = (
            f"Title: {job.title}\n"
            f"Company: {job.company_name}\n"
            f"Location: {job.location}\n"
            f"Description: {job.raw_description or 'None'}"
        )

        try:
            if self.provider == "openai":
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                        {"role": "user", "content": content}
                    ],
                    response_format=JobClassification,
                )
                return response.choices[0].message.parsed
            else:
                # Groq API via OpenAI SDK
                sys_prompt = (
                    CLASSIFIER_SYSTEM_PROMPT +
                    "\n\nYou MUST respond with raw JSON strictly matching this schema:\n"
                    "{\n"
                    '  "student_eligible": boolean,\n'
                    '  "is_internship": boolean,\n'
                    '  "is_graduate_role": boolean,\n'
                    '  "is_target_technical_role": boolean,\n'
                    '  "excluded_role": boolean,\n'
                    '  "technical_domain": string,\n'
                    '  "role_family": string,\n'
                    '  "summary": string\n'
                    "}"
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                raw_json = response.choices[0].message.content
                data = json.loads(raw_json)
                import time
                time.sleep(0.5)
                return JobClassification(**data)

        except Exception as e:
            logger.error(f"Classification failed via {self.provider}: {e}")
            return None
