"""AI-powered resume parser using LangChain."""
import os
import json
import logging
import re
import time
from typing import Dict, Optional, List
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    from langchain.prompts import PromptTemplate

try:
    from langchain_core.output_parsers import JsonOutputParser
except ImportError:
    from langchain.output_parsers import JsonOutputParser


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def _ensure_langchain_globals() -> None:
    """Ensure compatibility globals exist for mixed LangChain package installs."""
    try:
        import langchain

        if not hasattr(langchain, 'verbose'):
            langchain.verbose = False
        if not hasattr(langchain, 'debug'):
            langchain.debug = False
        if not hasattr(langchain, 'llm_cache'):
            langchain.llm_cache = None
    except Exception:
        # Do not block parser initialization if shim cannot be applied
        pass


class ResumeParser:
    """Parse resume text into structured data using LangChain and OpenAI."""
    
    def __init__(self):
        """Initialize the resume parser with LangChain components."""
        raw_api_key = os.getenv('OPENAI_API_KEY')
        self.api_key = raw_api_key if self._is_valid_api_key(raw_api_key) else None
        self.offline_mode = not bool(self.api_key)
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY missing or invalid. Using heuristic parsing fallback.")
            self.llm = None
        else:
            _ensure_langchain_globals()
            # Initialize OpenAI LLM
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                api_key=self.api_key
            )
        
        # Create output parser
        self.output_parser = JsonOutputParser()

        schema_requirements = """
Return a JSON object with EXACTLY these keys:
- name (string)
- email (string)
- phone (string)
- skills (array of strings)
- experience_years (number)
- education (string)
- professional_summary (string)
- current_role (string)
- location (string)
""".strip()
        
        # Create prompt template
        self.prompt_template = PromptTemplate(
            template="""You are an expert HR analyst parsing resumes. Extract structured information from the following resume text.

Resume Text:
{resume_text}

{schema_requirements}

{format_instructions}

Important:
- Be accurate and only extract information that is clearly stated
- For skills, include both technical and soft skills
- For experience_years, provide a numeric value (e.g., 5, 10)
- If information is not available, use empty string or 0
- Professional summary should be concise and highlight key strengths

Return only the JSON output, nothing else.""",
            input_variables=["resume_text"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions(),
                "schema_requirements": schema_requirements,
            }
        )
    
    def parse_resume(self, resume_text: str) -> Dict[str, any]:
        """
        Parse resume text into structured data.
        
        Args:
            resume_text: Raw text extracted from resume PDF
            
        Returns:
            Dictionary containing structured resume data
        """
        if not resume_text or not resume_text.strip():
            return {
                'success': False,
                'error': 'Empty resume text provided',
                'data': None
            }

        if not self.llm:
            logger.info("event=resume_parser_offline_mode")
            return self._heuristic_parse(resume_text)
        
        try:
            # Create the chain
            chain = self.prompt_template | self.llm | self.output_parser

            max_retries = int(os.getenv('LLM_RETRY_COUNT', '2') or 2)
            retry_delay = float(os.getenv('LLM_RETRY_DELAY', '0.75') or 0.75)
            result = None

            for attempt in range(max_retries + 1):
                try:
                    result = chain.invoke({"resume_text": resume_text})
                    break
                except Exception as retry_error:
                    if attempt >= max_retries:
                        raise retry_error
                    time.sleep(retry_delay * (attempt + 1))
            
            # Post-process the result
            processed_result = self._post_process_result(result or {})
            
            return {
                'success': True,
                'error': None,
                'data': processed_result
            }
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            
            # Fallback: Try to parse without structured output
            try:
                return self._fallback_parse(resume_text)
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {str(fallback_error)}")
                return {
                    'success': False,
                    'error': f'Failed to parse resume: {str(e)}',
                    'data': None
                }
    
    def _post_process_result(self, result: Dict) -> Dict:
        """
        Post-process parsed result to ensure data quality.
        
        Args:
            result: Raw parsed result from LLM
            
        Returns:
            Cleaned and validated result
        """
        processed = {
            'name': result.get('name', '').strip(),
            'email': result.get('email', '').strip(),
            'phone': result.get('phone', '').strip(),
            'skills': self._parse_skills(result.get('skills', '')),
            'experience_years': self._parse_experience_years(result.get('experience_years', '0')),
            'education': result.get('education', '').strip(),
            'professional_summary': result.get('professional_summary', '').strip(),
            'current_role': result.get('current_role', '').strip(),
            'location': result.get('location', '').strip()
        }
        
        return processed
    
    def _parse_skills(self, skills_str: str) -> list:
        """
        Parse skills string into a list.
        
        Args:
            skills_str: Comma-separated skills string
            
        Returns:
            List of skills
        """
        if not skills_str:
            return []

        if isinstance(skills_str, list):
            cleaned = [str(skill).strip() for skill in skills_str if str(skill).strip()]
            return cleaned
        
        # Split by comma and clean
        skills = [skill.strip() for skill in skills_str.split(',')]
        skills = [skill for skill in skills if skill]
        
        return skills

    @staticmethod
    def _is_valid_api_key(api_key: Optional[str]) -> bool:
        if not api_key:
            return False
        lowered = api_key.strip().lower()
        if not lowered:
            return False
        placeholders = (
            'your_openai_api_key_here',
            'your_openai_key_here',
            'your_api_key_here',
            'sk-your-key-here',
            'sk-...'
        )
        return lowered not in placeholders and 'your_' not in lowered

    def _heuristic_parse(self, resume_text: str) -> Dict[str, any]:
        """
        Heuristic parsing method without LLM dependency.
        """
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        lowered = resume_text.lower()

        email = self._extract_email(resume_text)
        phone = self._extract_phone(resume_text)
        name = self._extract_name(lines, email)
        experience_years = self._extract_experience_years(resume_text)
        skills = self._extract_known_skills(lowered)
        education = self._extract_education(lines)
        summary = self._extract_summary(lines)
        current_role = self._extract_current_role(lines)
        location = self._extract_location(lines)

        result = {
            'name': name,
            'email': email,
            'phone': phone,
            'skills': skills,
            'experience_years': experience_years,
            'education': education,
            'professional_summary': summary,
            'current_role': current_role,
            'location': location
        }

        return {
            'success': True,
            'error': None,
            'data': self._post_process_result(result)
        }

    @staticmethod
    def _extract_email(text: str) -> str:
        match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        return match.group(0) if match else ''

    @staticmethod
    def _extract_phone(text: str) -> str:
        match = re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', text)
        return match.group(1).strip() if match else ''

    @staticmethod
    def _extract_name(lines: List[str], email: str) -> str:
        for line in lines[:5]:
            if '@' in line:
                continue
            if email and email in line:
                continue
            if re.search(r'\d', line):
                continue
            words = [word for word in re.split(r'\s+', line) if word]
            if 1 < len(words) <= 4 and all(re.match(r"[A-Za-z\.'-]+$", w) for w in words):
                return line
        return ''

    @staticmethod
    def _extract_experience_years(text: str) -> int:
        patterns = [
            r'(?:minimum|min)\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(?:experience|exp)\s*(?:of\s*)?(\d+)\+?\s*years?'
        ]
        values = []
        for pattern in patterns:
            for match in re.findall(pattern, text.lower()):
                try:
                    values.append(int(match))
                except ValueError:
                    continue
        return max(values) if values else 0

    @staticmethod
    def _extract_known_skills(text: str) -> List[str]:
        known_skills = {
            'python', 'flask', 'django', 'fastapi', 'sql', 'postgresql', 'mysql', 'mongodb',
            'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'javascript', 'typescript',
            'react', 'node', 'node.js', 'java', 'spring', 'c++', 'c#', 'git', 'rest', 'graphql',
            'pandas', 'numpy', 'scikit-learn', 'machine learning', 'nlp', 'langchain'
        }
        return [skill for skill in sorted(known_skills) if skill in text]

    @staticmethod
    def _extract_education(lines: List[str]) -> str:
        patterns = [
            r'\b(bachelor|master|phd|mba|b\.sc|m\.sc|b\.e|m\.e|b\.tech|m\.tech)\b'
        ]
        for line in lines:
            lowered = line.lower()
            if any(re.search(pattern, lowered) for pattern in patterns):
                return line
        return ''

    @staticmethod
    def _extract_summary(lines: List[str]) -> str:
        headings = {'summary', 'professional summary', 'profile', 'about'}
        for idx, line in enumerate(lines):
            if line.lower().rstrip(':') in headings:
                snippet = []
                for next_line in lines[idx + 1: idx + 4]:
                    if next_line.isupper() or next_line.endswith(':'):
                        break
                    snippet.append(next_line)
                return ' '.join(snippet).strip()
        return ''

    @staticmethod
    def _extract_current_role(lines: List[str]) -> str:
        for line in lines:
            if 'current role' in line.lower() or 'current position' in line.lower():
                return line
        return ''

    @staticmethod
    def _extract_location(lines: List[str]) -> str:
        for line in lines[:5]:
            match = re.search(r'([A-Za-z][A-Za-z\s\.]+,\s*[A-Z]{2})', line)
            if match:
                return match.group(1)
        return ''
    
    def _parse_experience_years(self, exp_str: any) -> int:
        """
        Parse experience years to integer.
        
        Args:
            exp_str: Experience years as string or int
            
        Returns:
            Experience years as integer
        """
        try:
            if isinstance(exp_str, int):
                return max(0, exp_str)
            
            # Remove any non-numeric characters except decimal point
            cleaned = ''.join(c for c in str(exp_str) if c.isdigit() or c == '.')
            
            if not cleaned:
                return 0
            
            # Convert to int (round if decimal)
            return int(float(cleaned))
        except Exception:
            return 0
    
    def _fallback_parse(self, resume_text: str) -> Dict[str, any]:
        """
        Fallback parsing method using simple LLM call.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Dictionary with parsed data
        """
        prompt = f"""Extract the following information from this resume and return as JSON:
- name
- email
- phone
- skills (as array)
- experience_years (as number)
- education
- professional_summary
- current_role
- location

Resume:
{resume_text}

Return only valid JSON."""
        
        response = self.llm.invoke(prompt)
        
        # Try to parse JSON from response
        try:
            # Extract JSON from response
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to find JSON in the content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
                
                return {
                    'success': True,
                    'error': None,
                    'data': self._post_process_result(result)
                }
        except Exception as e:
            logger.error(f"Error parsing fallback response: {str(e)}")
        
        return {
            'success': False,
            'error': 'Could not parse resume with fallback method',
            'data': None
        }


# Global parser instance
_parser_instance = None


def get_parser() -> ResumeParser:
    """Get or create global parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ResumeParser()
    return _parser_instance
