import logging
import re
from typing import Dict, List, Any, Optional
import json
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_speaker_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate speaker profile using OpenAI API.
    
    Args:
        data: Dictionary with source data
        
    Returns:
        Dictionary with generated profile
    """
    try:
        # Combine all text sources
        all_text = ""
        
        # Add PDF text
        if 'pdf_text' in data and data['pdf_text']:
            for text_chunk in data['pdf_text']:
                all_text += text_chunk + "\n\n"
        
        # Add YouTube text
        if 'youtube_data' in data and 'processed_text' in data['youtube_data']:
            for text_chunk in data['youtube_data']['processed_text']:
                all_text += text_chunk + "\n\n"
        
        # Add Website text
        if 'website_text' in data and 'processed_text' in data['website_text']:
            for text_chunk in data['website_text']['processed_text']:
                all_text += text_chunk + "\n\n"
        
        # Add LinkedIn text
        if 'linkedin_data' in data and 'processed_text' in data['linkedin_data']:
            for text_chunk in data['linkedin_data']['processed_text']:
                all_text += text_chunk + "\n\n"
        
        # Check if we have any text to process
        if not all_text.strip():
            return {'error': 'No text data to process'}
        
        # Create prompt for OpenAI
        prompt = f"""
The following is content extracted from a user's PDF documents, YouTube channel, website, and LinkedIn profile. Please create a profile for this person based on this. What to include:
- Name (if applicable)
- Key topic/expertise
- Target audience
- Personal branding tone
- Activity summary
- Strengths and differentiators

[start text]
{all_text}
[end text]

Please format your response using this template:
**Name:** 
**Expertise:** 
**Target audience:** 
**Activity summary:** 
**Personal tone:** 
**Strengths:** 
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that creates professional speaker profiles based on provided information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.5
        )
        
        # Extract the generated profile
        profile_text = response.choices[0].message.content
        
        # Parse the profile text
        parsed_profile = parse_profile_text(profile_text)
        
        return parsed_profile
    
    except Exception as e:
        logger.error(f"Error generating speaker profile: {str(e)}")
        return {'error': str(e)}

def parse_profile_text(profile_text: str) -> Dict[str, Any]:
    """
    Parse profile text from OpenAI response into structured data.
    
    Args:
        profile_text: Profile text from OpenAI
        
    Returns:
        Dictionary with parsed profile data
    """
    profile = {
        'name': '',
        'expertise': [],
        'target_audience': [],
        'activity_summary': '',
        'personal_tone': '',
        'strengths': []
    }
    
    try:
        # Extract name
        name_match = re.search(r'\*\*Name:\*\*(.*?)(?=\*\*|\Z)', profile_text, re.DOTALL)
        if name_match:
            profile['name'] = name_match.group(1).strip()
        
        # Extract expertise
        expertise_match = re.search(r'\*\*Expertise:\*\*(.*?)(?=\*\*|\Z)', profile_text, re.DOTALL)
        if expertise_match:
            expertise_text = expertise_match.group(1).strip()
            # Split by commas and clean
            profile['expertise'] = [item.strip() for item in expertise_text.split(',') if item.strip()]
        
        # Extract target audience
        audience_match = re.search(r'\*\*Target audience:\*\*(.*?)(?=\*\*|\Z)', profile_text, re.DOTALL)
        if audience_match:
            audience_text = audience_match.group(1).strip()
            # Split by commas and clean
            profile['target_audience'] = [item.strip() for item in audience_text.split(',') if item.strip()]
        
        # Extract activity summary
        summary_match = re.search(r'\*\*Activity summary:\*\*(.*?)(?=\*\*|\Z)', profile_text, re.DOTALL)
        if summary_match:
            profile['activity_summary'] = summary_match.group(1).strip()
        
        # Extract personal tone
        tone_match = re.search(r'\*\*Personal tone:\*\*(.*?)(?=\*\*|\Z)', profile_text, re.DOTALL)
        if tone_match:
            profile['personal_tone'] = tone_match.group(1).strip()
        
        # Extract strengths
        strengths_match = re.search(r'\*\*Strengths:\*\*(.*?)(?=\*\*|\Z)', profile_text, re.DOTALL)
        if strengths_match:
            strengths_text = strengths_match.group(1).strip()
            # Split by commas and clean
            profile['strengths'] = [item.strip() for item in strengths_text.split(',') if item.strip()]
    
    except Exception as e:
        logger.error(f"Error parsing profile text: {str(e)}")
    
    return profile