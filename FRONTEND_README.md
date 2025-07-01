# K-Array Chat Frontend

A modern React frontend for the K-Array Chat system, built with Vite and designed to match K-Array's brand identity.

## Features

- **Modern Chat Interface**: Real-time messaging with confidence indicators and source attribution
- **Document Upload**: Drag-and-drop file upload for knowledge base enhancement
- **System Monitoring**: Real-time status dashboard for all system components
- **K-Array Design**: Brand-compatible design system with proper colors and typography
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Quick Start

### Prerequisites

- Node.js 18+ 
- Python 3.9+ (for backend)
- The Kchat backend system

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server**:
   ```bash
   python start_server.py
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:3000`

## Development

### Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Layout.jsx       # Main layout with navigation
│   │   ├── ChatInterface.jsx # Chat interface
│   │   ├── DocumentUpload.jsx # File upload component
│   │   └── SystemStatus.jsx  # System monitoring
│   ├── App.jsx             # Main app component
│   ├── App.css            # K-Array design system
│   └── main.jsx           # React entry point
├── package.json           # Dependencies
└── vite.config.js        # Vite configuration
```

### Key Components

- **Layout**: Navigation, header, and footer with K-Array branding
- **ChatInterface**: Main chat UI with message history, confidence indicators, and source attribution
- **DocumentUpload**: File upload interface supporting PDF, Word, Excel, and other formats
- **SystemStatus**: Real-time monitoring dashboard for backend services

### API Integration

The frontend communicates with the backend through these endpoints:

- `POST /api/chat` - Send chat messages
- `POST /api/upload` - Upload documents
- `GET /api/status` - Get system status
- `GET /api/sessions` - View active sessions

### Design System

The frontend uses a custom CSS design system based on K-Array's brand guidelines:

- **Colors**: K-Array primary colors (#1a1a1a, #ff4444)
- **Typography**: Inter font family with proper hierarchy
- **Components**: Consistent buttons, cards, and form elements
- **Responsive**: Mobile-first design with breakpoints

## Production Build

1. **Build the frontend**:
   ```bash
   npm run build
   ```

2. **Preview the build**:
   ```bash
   npm run preview
   ```

The build output will be in the `dist/` directory, ready for deployment.

## Configuration

### Environment Variables

The frontend can be configured through the backend's environment variables:

- `KCHAT_API_HOST` - API server host (default: localhost)
- `KCHAT_API_PORT` - API server port (default: 8000)
- `KCHAT_DEBUG` - Enable debug mode (default: false)

### Proxy Configuration

Development server is configured to proxy API requests to `http://localhost:8000`. This can be modified in `vite.config.js`.

## Features in Detail

### Chat Interface

- Real-time messaging with typing indicators
- Confidence scores for AI responses
- Source attribution from RAG system
- Message history with timestamps
- Auto-scroll to latest messages

### Document Upload

- Drag-and-drop file upload
- Support for multiple file formats (PDF, Word, Excel, CSV, JSON, Images)
- Progress indicators during upload
- Background processing for knowledge base integration
- File validation and error handling

### System Status

- Real-time service monitoring
- Resource usage metrics (CPU, Memory, Disk)
- Response time tracking
- Error rate monitoring
- Connection status for all services

## Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Ensure backend is running on port 8000
   - Check CORS configuration in `api_server.py`

2. **File Upload Not Working**:
   - Check file size limits (50MB max)
   - Verify supported file formats
   - Ensure backend data directory exists

3. **Chat Not Responding**:
   - Check LLM service status
   - Verify Ollama is running
   - Check logs for error messages

### Development Tips

- Use browser developer tools to inspect API requests
- Check the backend logs for detailed error information
- Test with different file types and sizes for upload functionality
- Monitor network requests in browser dev tools

## License

This project is part of the K-Array Chat system and follows the same licensing terms.