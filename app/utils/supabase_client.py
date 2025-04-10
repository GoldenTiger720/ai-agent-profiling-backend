from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client instance.
    """
    try:
        # Create a Supabase client using the settings
        supabase_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
        return supabase_client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise

# Create a global client instance
supabase = get_supabase_client()