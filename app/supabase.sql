-- Create tables for the Speaker Profile Automation Platform

-- Create users table
CREATE TABLE public.users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Add RLS policies for users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Allow users to read only their own data
CREATE POLICY users_select_policy ON public.users
    FOR SELECT
    USING (auth.uid() = id);

-- Allow authenticated users to update their own data
CREATE POLICY users_update_policy ON public.users
    FOR UPDATE
    USING (auth.uid() = id);

-- Rename existing profiles table to generated_profiles if it exists
ALTER TABLE IF EXISTS public.profiles 
RENAME TO generated_profiles;

-- Create generated_profiles table if it doesn't exist after rename
CREATE TABLE IF NOT EXISTS public.generated_profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT,
    expertise JSONB DEFAULT '[]',
    target_audience JSONB DEFAULT '[]',
    activity_summary TEXT,
    personal_tone TEXT,
    strengths JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS policies for generated_profiles table
ALTER TABLE public.generated_profiles ENABLE ROW LEVEL SECURITY;

-- Allow users to read only their own profiles
CREATE POLICY generated_profiles_select_policy ON public.generated_profiles
    FOR SELECT
    USING (auth.uid() = user_id);

-- Allow users to insert their own profiles
CREATE POLICY generated_profiles_insert_policy ON public.generated_profiles
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Allow users to update their own profiles
CREATE POLICY generated_profiles_update_policy ON public.generated_profiles
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Allow users to delete their own profiles
CREATE POLICY generated_profiles_delete_policy ON public.generated_profiles
    FOR DELETE
    USING (auth.uid() = user_id);

-- Create new profiles table for user information
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    street_address TEXT,
    street_address_line_2 TEXT,
    city TEXT,
    state_province TEXT,
    postal_zip_code TEXT,
    country TEXT,
    phone_number TEXT,
    birthday DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS policies for profiles table
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Allow users to read only their own profile information
CREATE POLICY profiles_select_policy ON public.profiles
    FOR SELECT
    USING (auth.uid() = user_id);

-- Allow users to insert their own profile information
CREATE POLICY profiles_insert_policy ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Allow users to update their own profile information
CREATE POLICY profiles_update_policy ON public.profiles
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Allow users to delete their own profile information
CREATE POLICY profiles_delete_policy ON public.profiles
    FOR DELETE
    USING (auth.uid() = user_id);

-- Create storage buckets for files
-- This can also be done through the Supabase UI or using the API
-- The code in storage_service.py will create the bucket if it doesn't exist

-- Create API function to create a user (this is a simplified example)
CREATE OR REPLACE FUNCTION create_user(
    user_email TEXT,
    user_password TEXT
) RETURNS UUID AS $$
DECLARE
    new_user_id UUID;
BEGIN
    new_user_id := gen_random_uuid();
    
    INSERT INTO public.users (id, email, password, created_at)
    VALUES (new_user_id, user_email, user_password, NOW());
    
    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to handle authentication
CREATE OR REPLACE FUNCTION authenticate_user(
    user_email TEXT,
    user_password TEXT
) RETURNS public.users AS $$
DECLARE
    user_record public.users;
BEGIN
    SELECT * INTO user_record
    FROM public.users
    WHERE email = user_email AND password = user_password;
    
    IF FOUND THEN
        -- Update last login time
        UPDATE public.users
        SET last_login = NOW()
        WHERE id = user_record.id;
        
        RETURN user_record;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Note: In a real application, you would use Supabase Auth instead of
-- handling authentication manually, and you would not store passwords
-- in plain text. The FastAPI backend in this project handles proper
-- password hashing and authentication.