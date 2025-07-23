# mNAV API - Mutual Fund Net Asset Value API

A Flask-based REST API for mutual fund Net Asset Value (mNAV) data with webhook support. This API provides endpoints for fetching mNAV data and receiving webhook notifications.

## Features

- 🚀 RESTful API endpoints
- 📊 mNAV data retrieval
- 🔔 Webhook support for real-time updates
- 🏥 Health check endpoint
- 🌐 CORS enabled
- 🐳 Docker containerized
- 🚂 Railway deployment ready
- 🔄 CI/CD with GitHub Actions
- 📺 **NEW: Big display mode** - Shows mNAV value in large, centered text

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mnav-api.git
   cd mnav-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Test the API**
   ```bash
   curl http://localhost:5000/api/health
   ```

### Docker

1. **Build the image**
   ```bash
   docker build -t mnav-api .
   ```

2. **Run the container**
   ```bash
   docker run -p 5000:8080 mnav-api
   ```

## API Endpoints

### 1. Root Endpoint (Big Display Mode)
- **URL**: `/`
- **Method**: `GET`
- **Description**: Shows mNAV value in large, centered display
- **Query Parameters**:
  - `fund_code` (optional): Specify fund code (default: 'default')
- **Features**:
  - Large, centered NAV value display
  - Fund name shown above the value
  - Change indicator with color coding (green for positive, red for negative)
  - Auto-refreshes every 30 seconds
  - Dark theme for easy viewing
  - Responsive design for mobile devices

### 2. Health Check
- **URL**: `/api/health`
- **Method**: `GET`
- **Description**: Health status of the API
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00.000000",
    "service": "mnav-api",
    "version": "1.0.0"
  }
  ```

### 3. Get mNAV Data
- **URL**: `/api/mnav`
- **Method**: `GET`
- **Query Parameters**:
  - `fund_code` (optional): Specific fund code
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "fund_code": "FUND123",
      "fund_name": "Sample Fund FUND123",
      "nav": 125.45,
      "date": "2024-01-01",
      "change": 1.23,
      "change_percent": 0.99,
      "currency": "USD"
    }
  }
  ```

### 4. Webhook Endpoint
- **URL**: `/webhook/mnav`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "fund_code": "FUND123",
    "nav": 125.45,
    "date": "2024-01-01"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Webhook received successfully",
    "id": 1
  }
  ```

### 5. Webhook History
- **URL**: `/webhook/mnav/history`
- **Method**: `GET`
- **Query Parameters**:
  - `page` (default: 1)
  - `per_page` (default: 10)
- **Description**: View webhook history for debugging

## Deployment

### Railway (Recommended)

1. **Fork/Clone this repository**

2. **Connect to Railway**
   - Go to [Railway](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Configure environment** (optional)
   - Add any required environment variables

4. **Deploy**
   - Railway automatically builds and deploys

### Heroku

1. **Install Heroku CLI**

2. **Create app**
   ```bash
   heroku create your-app-name
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

### Manual Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## Environment Variables

- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: False)

## Testing

### Run local tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest
```

### Test endpoints
```bash
# View big display mode (open in browser)
open http://localhost:5000

# View display for specific fund
open http://localhost:5000?fund_code=TECH

# Health check
curl http://localhost:5000/api/health

# Get mNAV data
curl http://localhost:5000/api/mnav?fund_code=FUND123

# Send webhook
curl -X POST http://localhost:5000/webhook/mnav \
  -H "Content-Type: application/json" \
  -d '{"fund_code":"FUND123","nav":125.45,"date":"2024-01-01"}'
```

### Display Mode Example
When you visit the root URL (`/`), you'll see:
```
     SAMPLE FUND DEFAULT
         125.45
      +1.23 (0.99%)
    Last updated: 15:35:22
```
The display features:
- Extra large font size for the NAV value
- Color-coded change indicator (green/red)
- Dark background for reduced eye strain
- Auto-refresh every 30 seconds
- Mobile responsive design

## Development

### Project Structure
```
mnav-api/
├── app.py                # Main application
├── requirements.txt      # Dependencies
├── Dockerfile           # Container config
├── railway.json         # Railway config
├── Procfile            # Process file
├── README.md           # This file
├── DEPLOYMENT_GUIDE.md # Deployment guide
└── .github/
    └── workflows/
        └── deploy.yml  # CI/CD workflow
```

### Adding New Endpoints

1. Add route to `app.py`
2. Update documentation
3. Add tests
4. Deploy

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

Built with ❤️ using Flask and deployed on Railway