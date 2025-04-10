import logging
import re
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import cv2
import numpy as np
import requests
from io import BytesIO
from datetime import datetime, timedelta
from app.config import settings
from app.utils.text_cleaning import clean_text, process_text_for_ai

logger = logging.getLogger(__name__)

def extract_channel_id(youtube_url: str) -> Optional[str]:
    """
    Extract channel ID from YouTube URL.
    
    Args:
        youtube_url: YouTube channel URL
        
    Returns:
        Channel ID if found, None otherwise
    """
    # Pattern for channel ID in URL
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([^\/\?\&]+)',  # /channel/UC...
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/c\/([^\/\?\&]+)',        # /c/ChannelName
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/user\/([^\/\?\&]+)',     # /user/Username
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([^\/\?\&]+)'           # /@HandleName
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    return None

def get_youtube_client():
    """
    Create and return a YouTube API client.
    
    Returns:
        YouTube API client
    """
    return build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)

def get_channel_info(channel_id: str) -> Dict[str, Any]:
    """
    Get channel information from YouTube API.
    
    Args:
        channel_id: YouTube channel ID
        
    Returns:
        Dictionary with channel information
    """
    youtube = get_youtube_client()
    channel_info = {}
    
    try:
        # Get channel details
        channel_response = youtube.channels().list(
            part='snippet,statistics,brandingSettings',
            id=channel_id
        ).execute()
        
        if not channel_response['items']:
            logger.error(f"No channel found with ID: {channel_id}")
            return channel_info
        
        channel_data = channel_response['items'][0]
        
        # Extract basic channel info
        channel_info['title'] = channel_data['snippet'].get('title', '')
        channel_info['description'] = channel_data['snippet'].get('description', '')
        channel_info['customUrl'] = channel_data['snippet'].get('customUrl', '')
        channel_info['publishedAt'] = channel_data['snippet'].get('publishedAt', '')
        channel_info['country'] = channel_data['snippet'].get('country', '')
        channel_info['viewCount'] = channel_data['statistics'].get('viewCount', 0)
        channel_info['subscriberCount'] = channel_data['statistics'].get('subscriberCount', 0)
        channel_info['videoCount'] = channel_data['statistics'].get('videoCount', 0)
        
        # Get channel keywords from branding settings if available
        if 'brandingSettings' in channel_data and 'channel' in channel_data['brandingSettings']:
            channel_info['keywords'] = channel_data['brandingSettings']['channel'].get('keywords', '')
        
    except HttpError as e:
        logger.error(f"Error getting channel info: {str(e)}")
    
    return channel_info

def get_recent_videos(channel_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent videos from a YouTube channel.
    
    Args:
        channel_id: YouTube channel ID
        max_results: Maximum number of videos to retrieve
        
    Returns:
        List of videos with their details
    """
    youtube = get_youtube_client()
    videos = []
    
    try:
        # Get channel's uploads playlist ID
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not channel_response['items']:
            logger.error(f"No channel found with ID: {channel_id}")
            return videos
        
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from uploads playlist
        playlist_response = youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=max_results
        ).execute()
        
        # Extract video IDs
        video_ids = [item['contentDetails']['videoId'] for item in playlist_response['items']]
        
        # Get video details
        if video_ids:
            videos_response = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()
            
            for video in videos_response['items']:
                video_data = {
                    'id': video['id'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],
                    'publishedAt': video['snippet']['publishedAt'],
                    'tags': video['snippet'].get('tags', []),
                    'viewCount': video['statistics'].get('viewCount', 0),
                    'likeCount': video['statistics'].get('likeCount', 0),
                    'commentCount': video['statistics'].get('commentCount', 0),
                    'duration': video['contentDetails']['duration'],
                    'thumbnailUrl': video['snippet']['thumbnails']['high']['url']
                }
                videos.append(video_data)
    
    except HttpError as e:
        logger.error(f"Error getting recent videos: {str(e)}")
    
    return videos

def get_popular_videos(channel_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Get most popular videos from a YouTube channel.
    
    Args:
        channel_id: YouTube channel ID
        max_results: Maximum number of videos to retrieve
        
    Returns:
        List of popular videos with their details
    """
    youtube = get_youtube_client()
    videos = []
    
    try:
        # Search for videos from the channel
        search_response = youtube.search().list(
            part='id',
            channelId=channel_id,
            maxResults=50,  # Get more results to sort later
            type='video',
            order='viewCount'  # Sort by view count
        ).execute()
        
        # Extract video IDs
        video_ids = [item['id']['videoId'] for item in search_response['items']]
        
        # Get video details
        if video_ids:
            # Limit to max_results
            video_ids = video_ids[:max_results]
            
            videos_response = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()
            
            for video in videos_response['items']:
                video_data = {
                    'id': video['id'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],
                    'publishedAt': video['snippet']['publishedAt'],
                    'tags': video['snippet'].get('tags', []),
                    'viewCount': video['statistics'].get('viewCount', 0),
                    'likeCount': video['statistics'].get('likeCount', 0),
                    'commentCount': video['statistics'].get('commentCount', 0),
                    'duration': video['contentDetails']['duration'],
                    'thumbnailUrl': video['snippet']['thumbnails']['high']['url']
                }
                videos.append(video_data)
    
    except HttpError as e:
        logger.error(f"Error getting popular videos: {str(e)}")
    
    return videos

def analyze_thumbnails(videos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze video thumbnails for common visual elements.
    
    Args:
        videos: List of videos with thumbnail URLs
        
    Returns:
        Dictionary with thumbnail analysis results
    """
    # Skip if no videos with thumbnails
    if not videos or all('thumbnailUrl' not in video for video in videos):
        return {}
    
    thumbnail_analysis = {
        'color_schemes': [],
        'has_text': False,
        'has_faces': False,
    }
    
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Process up to 5 thumbnails
        thumbnails_processed = 0
        dominant_colors = []
        
        for video in videos:
            if thumbnails_processed >= 5:
                break
                
            if 'thumbnailUrl' not in video:
                continue
                
            # Download thumbnail
            response = requests.get(video['thumbnailUrl'])
            if response.status_code != 200:
                continue
                
            # Convert to OpenCV format
            img_array = np.array(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                continue
                
            # Analyze for faces
            if not thumbnail_analysis['has_faces']:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces) > 0:
                    thumbnail_analysis['has_faces'] = True
            
            # Get dominant colors
            img_small = cv2.resize(img, (64, 64))
            pixels = img_small.reshape(-1, 3)
            
            # Use k-means to find dominant colors
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, _, centers = cv2.kmeans(np.float32(pixels), 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert colors to hex
            for color in centers:
                b, g, r = [int(c) for c in color]
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                dominant_colors.append(hex_color)
            
            thumbnails_processed += 1
        
        # Get unique colors
        thumbnail_analysis['color_schemes'] = list(set(dominant_colors))
        
    except Exception as e:
        logger.error(f"Error analyzing thumbnails: {str(e)}")
    
    return thumbnail_analysis

def get_channel_analytics(channel_id: str) -> Dict[str, Any]:
    """
    Analyze a YouTube channel and collect comprehensive data.
    
    Args:
        channel_id: YouTube channel ID
        
    Returns:
        Dictionary with channel analytics
    """
    analytics = {}
    
    try:
        # Get basic channel info
        channel_info = get_channel_info(channel_id)
        analytics['channel_info'] = channel_info
        
        # Get recent videos (last 10)
        recent_videos = get_recent_videos(channel_id, max_results=10)
        analytics['recent_videos'] = recent_videos
        
        # Get popular videos (top 5)
        popular_videos = get_popular_videos(channel_id, max_results=5)
        analytics['popular_videos'] = popular_videos
        
        # Analyze thumbnails
        thumbnail_analysis = analyze_thumbnails(popular_videos)
        analytics['thumbnail_analysis'] = thumbnail_analysis
        
        # Extract topics from video titles and descriptions
        all_titles = [video['title'] for video in recent_videos + popular_videos]
        all_descriptions = [video['description'] for video in recent_videos + popular_videos]
        all_tags = []
        for video in recent_videos + popular_videos:
            if 'tags' in video and video['tags']:
                all_tags.extend(video['tags'])
        
        # Get unique tags
        unique_tags = list(set(all_tags))
        analytics['top_tags'] = unique_tags[:20] if len(unique_tags) > 20 else unique_tags
        
        # Extract upload frequency
        if len(recent_videos) > 1:
            upload_dates = [datetime.fromisoformat(video['publishedAt'].replace('Z', '+00:00')) 
                            for video in recent_videos]
            upload_dates.sort()
            
            if len(upload_dates) >= 2:
                total_days = (upload_dates[-1] - upload_dates[0]).days
                if total_days > 0:
                    avg_days_between = total_days / (len(upload_dates) - 1)
                    analytics['upload_frequency'] = {
                        'avg_days_between_uploads': avg_days_between,
                        'uploads_per_month': 30 / avg_days_between if avg_days_between > 0 else 0
                    }
    
    except Exception as e:
        logger.error(f"Error getting channel analytics: {str(e)}")
    
    return analytics

def process_youtube_channel(youtube_url: str) -> Dict[str, Any]:
    """
    Process a YouTube channel URL to extract relevant information.
    
    Args:
        youtube_url: YouTube channel URL
        
    Returns:
        Dictionary with processed channel data
    """
    try:
        # Extract channel ID from URL
        channel_id = extract_channel_id(youtube_url)
        
        if not channel_id:
            logger.error(f"Could not extract channel ID from URL: {youtube_url}")
            return {'error': 'Invalid YouTube channel URL'}
        
        # Get channel analytics
        analytics = get_channel_analytics(channel_id)
        
        # Process text for AI
        channel_description = analytics.get('channel_info', {}).get('description', '')
        video_descriptions = [video.get('description', '') for video in 
                             analytics.get('recent_videos', []) + analytics.get('popular_videos', [])]
        
        # Combine all text
        all_text = channel_description + "\n\n" + "\n\n".join(video_descriptions)
        
        # Process text
        processed_text = process_text_for_ai(all_text)
        
        # Prepare result
        result = {
            'channel_info': analytics.get('channel_info', {}),
            'video_count': analytics.get('channel_info', {}).get('videoCount', 0),
            'subscriber_count': analytics.get('channel_info', {}).get('subscriberCount', 0),
            'top_tags': analytics.get('top_tags', []),
            'upload_frequency': analytics.get('upload_frequency', {}),
            'processed_text': processed_text,
            'recent_video_titles': [video.get('title', '') for video in analytics.get('recent_videos', [])[:5]],
            'popular_video_titles': [video.get('title', '') for video in analytics.get('popular_videos', [])[:5]]
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing YouTube channel: {str(e)}")
        return {'error': str(e)}