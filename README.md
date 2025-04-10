# Speaker Profile Automation Platform

This FastAPI backend automates the process of creating speaker profiles by analyzing various data sources (PDFs, YouTube channels, websites, LinkedIn profiles) and using OpenAI to generate comprehensive speaker summaries.

## Features

- 🔐 Authentication with Supabase
- 📄 PDF analysis (including OCR for scanned documents)
- 📺 YouTube channel analysis
- 🌐 Website crawling and analysis
- 👔 LinkedIn profile extraction
- 🧠 AI-powered speaker profile generation with OpenAI
- 📁 File storage with Supabase Storage

## Prerequisites

- Python 3.8+
- Supabase account
- OpenAI API key
- YouTube Data API v3 key
- (Optional) Tesseract OCR for processing scanned PDFs

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/speaker-profile-platform.git
cd speaker-profile-platform
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Supabase

1. Create a new Supabase project
2. Run the SQL in `supabase_setup.sql` in the Supabase SQL editor
3. Create a new storage bucket named `speaker-profiles`

### 5. Configure environment variables

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Fill in your API keys and Supabase credentials in the `.env` file

### 6. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
speaker_profile_platform/
├── app/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration settings
│   ├── models/                   # Database models
│   ├── routers/                  # API routes
│   ├── services/                 # Business logic
│   ├── schemas/                  # Pydantic schemas
│   └── utils/                    # Utility functions
├── requirements.txt              # Project dependencies
└── .env                          # Environment variables
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Register a new user
- `POST /api/v1/auth/login` - Login with email and password
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user profile

### File Uploads

- `POST /api/v1/uploads/pdf` - Upload a single PDF file
- `POST /api/v1/uploads/multiple-pdfs` - Upload multiple PDF files
- `GET /api/v1/uploads/pdfs` - List all uploaded PDF files
- `DELETE /api/v1/uploads/pdf/{file_path}` - Delete a PDF file

### Profiles

- `POST /api/v1/profiles/create` - Create a new speaker profile
- `GET /api/v1/profiles/list` - List all profiles for current user
- `GET /api/v1/profiles/{profile_id}` - Get a specific profile
- `DELETE /api/v1/profiles/{profile_id}` - Delete a profile

## Usage Example

To create a speaker profile, you'll need to:

1. Upload PDF files (speaker one-sheet, book, etc.)
2. Send a request to create a profile with URLs for the uploaded PDFs, YouTube channel, website, and LinkedIn profile

Example request:

```http
POST /api/v1/profiles/create?pdf_urls=https://storage-url/file1.pdf&pdf_urls=https://storage-url/file2.pdf

{
  "youtube_url": "https://www.youtube.com/channel/UC-example",
  "website_url": "https://example.com",
  "linkedin_url": "https://www.linkedin.com/in/example-profile"
}
```

## License

This project is licensed under the MIT License.
