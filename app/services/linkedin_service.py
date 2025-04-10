import logging
import re
import time
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from app.config import settings
from app.utils.text_cleaning import clean_text, process_text_for_ai

logger = logging.getLogger(__name__)

def extract_linkedin_username(linkedin_url: str) -> Optional[str]:
    """
    Extract username from LinkedIn URL.
    
    Args:
        linkedin_url: LinkedIn profile URL
        
    Returns:
        Username if found, None otherwise
    """
    patterns = [
        r'linkedin\.com\/in\/([^\/\?]+)',
        r'linkedin\.com\/company\/([^\/\?]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, linkedin_url)
        if match:
            return match.group(1)
    
    return None

def scrape_linkedin_profile(linkedin_url: str) -> Dict[str, Any]:
    """
    Scrape LinkedIn profile using Playwright.
    
    Args:
        linkedin_url: LinkedIn profile URL
        
    Returns:
        Dictionary with profile data
    """
    result = {}
    
    try:
        # Validate URL
        if not linkedin_url.startswith(('http://', 'https://')):
            linkedin_url = 'https://' + linkedin_url
        
        if 'linkedin.com' not in linkedin_url:
            return {'error': 'Not a valid LinkedIn URL'}
        
        # Extract username for later use
        username = extract_linkedin_username(linkedin_url)
        if not username:
            return {'error': 'Could not extract LinkedIn username from URL'}
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # Create new page
            page = context.new_page()
            
            # Go to LinkedIn
            page.goto(linkedin_url, wait_until='networkidle', timeout=60000)
            
            # LinkedIn may show a login page for non-authenticated users
            # We'll try to extract public information anyway
            
            # Wait for content to load
            page.wait_for_timeout(3000)
            
            # Get page content
            content = page.content()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract profile data
            profile_data = extract_profile_data(soup, username)
            result.update(profile_data)
            
            # Close browser
            browser.close()
    
    except Exception as e:
        logger.error(f"Error scraping LinkedIn profile: {str(e)}")
        result['error'] = str(e)
    
    return result

def extract_profile_data(soup: BeautifulSoup, username: str) -> Dict[str, Any]:
    """
    Extract profile data from BeautifulSoup object.
    
    Args:
        soup: BeautifulSoup object
        username: LinkedIn username
        
    Returns:
        Dictionary with profile data
    """
    profile_data = {
        'username': username,
        'name': '',
        'headline': '',
        'summary': '',
        'experience': [],
        'education': [],
        'skills': [],
        'full_text': ''
    }
    
    try:
        # Extract name
        name_tag = soup.find('h1', {'class': re.compile(r'text-heading-xlarge.*')})
        if name_tag:
            profile_data['name'] = name_tag.get_text().strip()
        
        # Extract headline
        headline_tag = soup.find('div', {'class': re.compile(r'text-body-medium.*')})
        if headline_tag:
            profile_data['headline'] = headline_tag.get_text().strip()
        
        # Extract summary/about
        summary_section = soup.find('section', {'id': re.compile(r'about-section')}) or \
                          soup.find('section', {'class': re.compile(r'summary.*')})
        if summary_section:
            summary_text = summary_section.find('div', {'class': re.compile(r'display-flex.*')})
            if summary_text:
                profile_data['summary'] = summary_text.get_text().strip()
        
        # Extract experience
        experience_section = soup.find('section', {'id': re.compile(r'experience-section')})
        if experience_section:
            experience_items = experience_section.find_all('li', {'class': re.compile(r'experience-item')}) or \
                               experience_section.find_all('div', {'class': re.compile(r'experience-item')})
            
            for item in experience_items:
                company = item.find('h4') or item.find('h3')
                title = item.find('h3') or item.find('h4')
                date_range = item.find('div', {'class': re.compile(r'date-range')})
                
                experience = {}
                if company:
                    experience['company'] = company.get_text().strip()
                if title:
                    experience['title'] = title.get_text().strip()
                if date_range:
                    experience['date_range'] = date_range.get_text().strip()
                
                if experience:
                    profile_data['experience'].append(experience)
        
        # Extract education
        education_section = soup.find('section', {'id': re.compile(r'education-section')})
        if education_section:
            education_items = education_section.find_all('li', {'class': re.compile(r'education.*')}) or \
                              education_section.find_all('div', {'class': re.compile(r'education.*')})
            
            for item in education_items:
                school = item.find('h3')
                degree = item.find('h4') or item.find('div', {'class': re.compile(r'degree')})
                date_range = item.find('div', {'class': re.compile(r'date-range')})
                
                education = {}
                if school:
                    education['school'] = school.get_text().strip()
                if degree:
                    education['degree'] = degree.get_text().strip()
                if date_range:
                    education['date_range'] = date_range.get_text().strip()
                
                if education:
                    profile_data['education'].append(education)
        
        # Extract skills
        skills_section = soup.find('section', {'id': re.compile(r'skills-section')}) or \
                         soup.find('section', {'class': re.compile(r'skills.*')})
        if skills_section:
            skill_items = skills_section.find_all('li') or skills_section.find_all('div', {'class': re.compile(r'skill.*')})
            
            for item in skill_items:
                skill = item.get_text().strip()
                if skill and len(skill) > 0:
                    profile_data['skills'].append(skill)
        
        # Get full text from page for further processing
        profile_data['full_text'] = soup.get_text()
    
    except Exception as e:
        logger.error(f"Error extracting profile data: {str(e)}")
    
    return profile_data

def process_linkedin_profile(linkedin_url: str) -> Dict[str, Any]:
    """
    Process LinkedIn profile and prepare data for AI.
    
    Args:
        linkedin_url: LinkedIn profile URL
        
    Returns:
        Dictionary with processed profile data
    """
    # Scrape profile
    profile_data = scrape_linkedin_profile(linkedin_url)
    
    # Check for errors
    if 'error' in profile_data:
        return profile_data
    
    # Process full text for AI
    full_text = profile_data.get('full_text', '')
    if full_text:
        profile_data['processed_text'] = process_text_for_ai(full_text)
        # Remove raw full text to save space
        del profile_data['full_text']
    
    return profile_data