"""AI-powered resume parser using LangChain."""
import os
import json
import logging
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parse resume text into structured data using LangChain and OpenAI."""
    
    def __init__(self):
        """Initialize the resume parser with LangChain components."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. Parser will not function.")
            self.llm = None
        else:
            # Initialize OpenAI LLM
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                api_key=self.api_key
            )
        
        # Define the output schema
        self.response_schemas = [
            ResponseSchema(
                name="name",
                description="Full name of the candidate. Extract first and last name."
            ),
            ResponseSchema(
                name="email",
                description="Email address of the candidate. Return empty string if not found."
            ),
            ResponseSchema(
                name="phone",
                description="Phone number of the candidate. Return empty string if not found."
            ),
            ResponseSchema(
                name="skills",
                description="List of technical and professional skills. Return as comma-separated values."
            ),
            ResponseSchema(
                name="experience_years",
                description="Total years of professional experience as a number. If not clear, estimate based on job history."
            ),
            ResponseSchema(
                name="education",
                description="Highest education degree and institution. Format: 'Degree from Institution'."
            ),
            ResponseSchema(
                name="professional_summary",
                description="Brief professional summary (2-3 sentences) highlighting key qualifications and career focus."
            ),
            ResponseSchema(
                name="current_role",
                description="Most recent or current job title. Return empty string if not found."
            ),
            ResponseSchema(
                name="location",
                description="Current location or city. Return empty string if not found."
            )
        ]
        
        # Create output parser
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
        
        # Create prompt template
        self.prompt_template = PromptTemplate(
            template="""You are an expert HR analyst parsing resumes. Extract structured information from the following resume text.

Resume Text:
{resume_text}

{format_instructions}

Important:
- Be accurate and only extract information that is clearly stated
- For skills, include both technical and soft skills
- For experience_years, provide a numeric value (e.g., 5, 10)
- If information is not available, use empty string or 0
- Professional summary should be concise and highlight key strengths

Return only the JSON output, nothing else.""",
            input_variables=["resume_text"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
    
    def parse_resume(self, resume_text: str) -> Dict[str, any]:
        """
        Parse resume text into structured data.
        
        Args:
            resume_text: Raw text extracted from resume PDF
            
        Returns:
            Dictionary containing structured resume data
        """
        if not self.llm:
            logger.error("OpenAI API key not configured")
            return {
                'success': False,
                'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY in .env file.',
                'data': None
            }
        
        if not resume_text or not resume_text.strip():
            return {
                'success': False,
                'error': 'Empty resume text provided',
                'data': None
            }
        
        try:
            # Create the chain
            chain = self.prompt_template | self.llm | self.output_parser
            
            # Parse the resume
            result = chain.invoke({"resume_text": resume_text})
            
            # Post-process the result
            processed_result = self._post_process_result(result)
            
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
        
        # Split by comma and clean
        skills = [skill.strip() for skill in skills_str.split(',')]
        skills = [skill for skill in skills if skill]
        
        return skills
    
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
