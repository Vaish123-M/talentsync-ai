"""Multi-format resume parser supporting PDF, DOCX, LinkedIn, GitHub."""
import logging
import re
from typing import Optional, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class ResumeFormatHandler:
    """Detect and parse resumes in multiple formats."""

    SUPPORTED_FORMATS = {'.pdf', '.docx', '.doc'}
    URL_PATTERNS = {
        'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-]+)',
        'github': r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9\-]+)'
    }

    @staticmethod
    def detect_format(source: str) -> str:
        """Detect resume source format: 'pdf', 'docx', 'linkedin', 'github', or 'unknown'."""
        if not source or not isinstance(source, str):
            return 'unknown'

        source = source.strip().lower()
        
        # Check URL patterns
        if re.search(ResumeFormatHandler.URL_PATTERNS['linkedin'], source):
            return 'linkedin'
        if re.search(ResumeFormatHandler.URL_PATTERNS['github'], source):
            return 'github'
        
        # Check file extensions
        if source.endswith('.pdf'):
            return 'pdf'
        if source.endswith(('.docx', '.doc')):
            return 'docx'
        
        return 'unknown'

    @staticmethod
    def extract_from_docx(file_path: str) -> Optional[str]:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            return text if text else None
        except ImportError:
            logger.warning("event=docx_parse_skipped reason=python_docx_not_installed")
            return None
        except Exception as e:
            logger.exception("event=docx_extraction_failed path=%s error=%s", file_path, str(e))
            return None

    @staticmethod
    def extract_from_linkedin(profile_url: str) -> Optional[str]:
        """Scrape LinkedIn profile summary (requires public profile or API access)."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            normalized_url = profile_url if profile_url.startswith('http') else f'https://linkedin.com/in/{profile_url}'
            response = requests.get(normalized_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic profile info
            profile_data = {
                'name': '',
                'headline': '',
                'about': '',
                'experience': []
            }
            
            # Try to extract name and headline from page
            try:
                name_elem = soup.find('h1')
                if name_elem:
                    profile_data['name'] = name_elem.get_text(strip=True)
            except Exception:
                pass
            
            text = soup.get_text(separator='\n')
            return text[:2000] if text else None
            
        except ImportError:
            logger.warning("event=linkedin_scrape_skipped reason=requests_or_beautifulsoup_not_installed")
            return None
        except Exception as e:
            logger.exception("event=linkedin_scrape_failed url=%s error=%s", profile_url, str(e))
            return None

    @staticmethod
    def extract_from_github(github_username: str) -> Optional[str]:
        """Scrape GitHub profile and top repositories."""
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            username = github_username.split('/')[-1].strip()
            user_url = f'https://api.github.com/users/{username}'
            repos_url = f'https://api.github.com/users/{username}/repos?sort=stars&per_page=10'
            
            user_resp = requests.get(user_url, headers=headers, timeout=10)
            repos_resp = requests.get(repos_url, headers=headers, timeout=10)
            
            if not user_resp.ok or not repos_resp.ok:
                return None
            
            user_data = user_resp.json()
            repos_data = repos_resp.json()
            
            profile_text = f"""
GitHub Profile: {username}
Name: {user_data.get('name', '')}
Bio: {user_data.get('bio', '')}
Location: {user_data.get('location', '')}
Public Repos: {user_data.get('public_repos', 0)}
Followers: {user_data.get('followers', 0)}

Top Repositories:
""".strip()
            
            for repo in repos_data[:5]:
                profile_text += f"\n- {repo.get('name', '')}: {repo.get('description', '')}"
            
            return profile_text if len(profile_text) > 50 else None
            
        except ImportError:
            logger.warning("event=github_scrape_skipped reason=requests_not_installed")
            return None
        except Exception as e:
            logger.exception("event=github_scrape_failed username=%s error=%s", github_username, str(e))
            return None

    @staticmethod
    def parse_resume_source(source: str) -> Optional[str]:
        """
        Parse resume from any supported source (file path or URL).
        
        Args:
            source: File path, LinkedIn URL, or GitHub URL
            
        Returns:
            Extracted text or None if parsing fails
        """
        format_type = ResumeFormatHandler.detect_format(source)
        
        if format_type == 'pdf':
            # Use existing PDF extractor
            from app.utils.pdf_extractor import PDFExtractor
            extractor = PDFExtractor()
            result = extractor.extract_text_from_file(source)
            return result.get('text') if result and result.get('success') else None
        
        elif format_type == 'docx':
            return ResumeFormatHandler.extract_from_docx(source)
        
        elif format_type == 'linkedin':
            return ResumeFormatHandler.extract_from_linkedin(source)
        
        elif format_type == 'github':
            return ResumeFormatHandler.extract_from_github(source)
        
        return None
