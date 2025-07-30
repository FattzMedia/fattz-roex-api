# Roex Python Microservice

This microservice provides a bridge between your Supabase Edge Functions and the Roex audio processing API using the official `roex-python` library.

## Features

- **Official Roex Integration**: Uses the official `roex-python` library for type-safe API interactions
- **Automatic Polling**: Built-in job status polling and completion handling
- **Secure File Uploads**: Leverages Roex's temporary signed URL system
- **Error Handling**: Comprehensive error handling and logging
- **FastAPI**: Modern, fast Python web framework with automatic API documentation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
ROEX_API_KEY=your_roex_api_key_from_tonn_portal
ENVIRONMENT=production
```

### 3. Local Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`

### 4. API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Deployment

### Railway (Recommended)

1. Push code to GitHub repository
2. Connect repository to Railway
3. Set environment variables in Railway dashboard
4. Deploy automatically

### Docker

```bash
docker build -t roex-microservice .
docker run -p 8000:8000 -e ROEX_API_KEY=your_key roex-microservice
```

## API Endpoints

### Process Audio
`POST /process`

Process audio using various Roex services.

**Request:**
```json
{
  "service_type": "mastering_full",
  "file_url": "https://example.com/audio.wav",
  "musical_style": "POP",
  "webhook_url": "https://your-callback-url.com",
  "parameters": {}
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "roex_job_123",
  "service_type": "mastering_full",
  "status": "processing"
}
```

### Check Status
`POST /status`

Check the status of a processing job.

**Request:**
```json
{
  "job_id": "roex_job_123",
  "service_type": "mastering_full"
}
```

### Health Check
`GET /health`

Returns service health status.

## Supported Service Types

- `mastering_full` - AI mastering
- `mixing_full` - AI mixing
- `mix_enhance` - Mix enhancement
- `mix_analysis` - Audio analysis
- `cleanup` - Audio cleanup

## Integration with Supabase

Your Supabase Edge Functions should call this microservice instead of the Roex API directly:

```typescript
const pythonServiceUrl = 'https://your-python-service.railway.app';
const response = await fetch(`${pythonServiceUrl}/process`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    service_type: 'mastering_full',
    file_url: audioFileUrl,
    musical_style: 'POP'
  })
});
```

## Monitoring

- Logs are available in your deployment platform
- Health check endpoint for monitoring
- Error tracking and reporting included

## Security

- API key stored securely as environment variable
- CORS configured for web applications
- Input validation using Pydantic models