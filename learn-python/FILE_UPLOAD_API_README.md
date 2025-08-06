# File Upload & Image Processing API

## 🎯 Overview

This is a comprehensive web-based image processing API that builds upon all previous stages with advanced file upload capabilities, real-time progress tracking, and a modern web interface.

## ✨ Features

### 🚀 Core Features

- **File Upload**: Drag-and-drop interface with file validation
- **Real-time Progress**: Live progress tracking during processing
- **Batch Processing**: Process multiple transformations simultaneously
- **Web Interface**: Modern, responsive web UI
- **Download Results**: Download transformed images directly
- **Image Preview**: Preview uploaded images before processing

### 🎨 Image Transformations

- **Brightness Adjustment**: Enhance image brightness
- **Contrast Enhancement**: Improve image contrast
- **Sepia Filter**: Apply vintage sepia effect
- **Grayscale Conversion**: Convert to black and white
- **Color Inversion**: Invert image colors
- **Gaussian Blur**: Apply blur effects
- **Pillow Effects**: Advanced Pillow-based transformations

### 📊 Database Integration

- **Transformation History**: Store all processing history
- **Progress Tracking**: Track processing time and status
- **Metadata Storage**: Store image metadata and parameters
- **Schema Management**: Uses `image_processor` schema

### 🔄 Real-time Features

- **Live Progress**: Real-time progress updates
- **Status Monitoring**: Monitor processing status
- **WebSocket Support**: Real-time communication (future)
- **Background Processing**: Non-blocking image processing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI App   │    │   PostgreSQL    │
│   (Port 8003)   │◄──►│   (file_upload_ │◄──►│   Database      │
│                 │    │    _api.py)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │  Image Processing│    │  Transformation │
│   & Validation  │    │   Engine        │    │   History       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Start the API

```bash
# Activate virtual environment
source venv/bin/activate

# Start the file upload API
python3 file_upload_api.py
```

### 2. Access the Web Interface

Open your browser and visit: **http://localhost:8003**

### 3. Upload and Process Images

1. **Drag & Drop**: Drag an image file onto the upload area
2. **Select File**: Or click "Choose File" to select an image
3. **Watch Progress**: Monitor real-time processing progress
4. **Download Results**: Download transformed images

## 📁 API Endpoints

### Web Interface

- `GET /` - Main web interface with drag-and-drop upload

### File Operations

- `POST /upload` - Upload image file
- `GET /preview/{upload_id}` - Get image preview
- `GET /download/{upload_id}/{transformation_type}` - Download transformed image

### Processing

- `POST /process/{upload_id}` - Start image processing
- `GET /status/{upload_id}` - Get processing status
- `GET /uploads` - List all uploads

### Example Usage

#### Upload File

```bash
curl -X POST "http://localhost:8003/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sources/1.jpg"
```

#### Process Image

```bash
curl -X POST "http://localhost:8003/process/{upload_id}"
```

#### Check Status

```bash
curl -X GET "http://localhost:8003/status/{upload_id}"
```

#### Download Result

```bash
curl -X GET "http://localhost:8003/download/{upload_id}/brightness" \
     --output brightness_result.jpg
```

## 🧪 Testing

### Run Tests

```bash
# Test the API functionality
python3 test_file_upload.py
```

### Manual Testing

1. **Start the API**: `python3 file_upload_api.py`
2. **Open Browser**: Visit `http://localhost:8003`
3. **Upload Image**: Drag and drop an image
4. **Monitor Progress**: Watch real-time processing
5. **Download Results**: Download transformed images

## 📊 File Structure

```
learn-python/
├── file_upload_api.py          # Main API application
├── test_file_upload.py         # Test script
├── FILE_UPLOAD_API_README.md   # This documentation
├── uploads/                    # Uploaded files
│   ├── {upload_id}.jpg         # Original uploaded files
│   └── previews/               # Image previews
├── output/                     # Processed images
│   └── processed/              # Transformed images
│       └── {upload_id}_{type}.jpg
└── sources/                    # Test images
    └── 1.jpg                   # Test image
```

## 🔧 Configuration

### Environment Variables

```bash
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=digitai
DB_USER=digitai
DB_PASSWORD=mahindra16

# File storage
UPLOAD_DIR=uploads
OUTPUT_DIR=output

# API configuration
API_HOST=0.0.0.0
API_PORT=8003
```

### Directory Structure

- **`uploads/`**: Original uploaded files
- **`output/processed/`**: Transformed images
- **`sources/`**: Test images

## 🎨 Web Interface Features

### Modern Design

- **Responsive Layout**: Works on desktop and mobile
- **Drag & Drop**: Intuitive file upload
- **Progress Tracking**: Real-time progress bars
- **Status Updates**: Live status messages
- **Result Display**: Grid layout for results

### User Experience

- **Visual Feedback**: Hover effects and animations
- **Error Handling**: Clear error messages
- **Loading States**: Loading indicators
- **Download Links**: Direct download buttons

## 🔄 Processing Workflow

1. **File Upload**

   - Validate file type and size
   - Generate unique upload ID
   - Save to uploads directory
   - Create processing status

2. **Image Processing**

   - Load image with ImageColorTransformer
   - Apply selected transformations
   - Save transformed images
   - Update processing status

3. **Database Storage**

   - Store transformation history
   - Track processing time
   - Save metadata and parameters

4. **Result Delivery**
   - Generate download links
   - Provide status updates
   - Enable result preview

## 🛠️ Development

### Adding New Transformations

1. **Update `apply_transformation` method** in `FileUploadProcessor`
2. **Add transformation logic** using `ImageColorTransformer`
3. **Update web interface** to include new transformation
4. **Test the new transformation**

### Example: Adding a New Transformation

```python
# In file_upload_api.py
elif transformation_type == "new_effect":
    transformer.apply_new_effect(parameters)
```

### Customizing the Web Interface

1. **Modify HTML/CSS** in the `root()` endpoint
2. **Update JavaScript** for new functionality
3. **Add new API endpoints** as needed
4. **Test the interface** thoroughly

## 🔍 Monitoring and Logging

### Status Tracking

- **Upload Status**: Track file upload progress
- **Processing Status**: Monitor transformation progress
- **Completion Status**: Track processing completion
- **Error Status**: Handle and log errors

### Database Monitoring

- **Transformation History**: View all processing history
- **Performance Metrics**: Track processing times
- **Usage Statistics**: Monitor API usage

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**: Configure production environment
2. **Database Setup**: Set up production database
3. **File Storage**: Configure production file storage
4. **Load Balancing**: Set up load balancer
5. **Monitoring**: Configure monitoring and logging

### Docker Deployment

```bash
# Build Docker image
docker build -t file-upload-api .

# Run container
docker run -p 8003:8003 file-upload-api
```

## 🔐 Security Considerations

### File Upload Security

- **File Type Validation**: Validate file extensions
- **File Size Limits**: Implement size restrictions
- **Virus Scanning**: Scan uploaded files
- **Access Control**: Implement user authentication

### API Security

- **Rate Limiting**: Prevent abuse
- **Input Validation**: Validate all inputs
- **Error Handling**: Secure error messages
- **CORS Configuration**: Configure CORS properly

## 📈 Performance Optimization

### Processing Optimization

- **Background Processing**: Non-blocking processing
- **Batch Processing**: Process multiple transformations
- **Caching**: Cache frequently used results
- **Compression**: Compress large images

### Database Optimization

- **Indexing**: Index frequently queried fields
- **Connection Pooling**: Optimize database connections
- **Query Optimization**: Optimize database queries

## 🎯 Future Enhancements

### Planned Features

- **WebSocket Support**: Real-time communication
- **Batch Upload**: Multiple file upload
- **Advanced Transformations**: More image effects
- **User Authentication**: User accounts and sessions
- **API Versioning**: Versioned API endpoints
- **Webhook Support**: External notifications

### Integration Opportunities

- **Cloud Storage**: AWS S3, Google Cloud Storage
- **CDN Integration**: Content delivery networks
- **ML Integration**: AI-powered transformations
- **Third-party APIs**: External image services

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**
3. **Implement changes**
4. **Add tests**
5. **Submit pull request**

### Code Standards

- **Python**: PEP 8 style guide
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit and integration tests
- **Type Hints**: Use type annotations

## 📄 License

This project is part of the Python Learning Path and is designed for educational purposes.

## 🎓 Learning Objectives

This API demonstrates:

- **FastAPI Development**: Modern web framework usage
- **File Upload**: Secure file handling
- **Real-time Features**: Progress tracking and updates
- **Database Integration**: PostgreSQL with SQLAlchemy
- **Web Interface**: Modern frontend development
- **API Design**: RESTful API design principles
- **Error Handling**: Comprehensive error management
- **Testing**: Automated testing strategies

---

**Happy Learning! 🚀**
