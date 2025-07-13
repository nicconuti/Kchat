# Milvus Setup Guide for K-Array Chat System

## Overview
The K-Array Chat System requires Milvus vector database for high-performance similarity search and retrieval. This guide covers installation and setup.

## Quick Start (Docker - Recommended)

### 1. Install Docker
Ensure Docker is installed and running on your system.

### 2. Start Milvus Standalone
```bash
# Download and start Milvus
curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
bash standalone_embed.sh start

# Or using docker-compose
wget https://github.com/milvus-io/milvus/releases/download/v2.4.0/milvus-standalone-docker-compose.yml -O docker-compose.yml
docker-compose up -d
```

### 3. Verify Installation
```bash
# Check if Milvus is running
docker ps | grep milvus

# Test connection
python3 -c "
from pymilvus import connections
try:
    connections.connect('default', host='localhost', port='19530')
    print('✅ Milvus connection successful')
except Exception as e:
    print(f'❌ Milvus connection failed: {e}')
"
```

## Configuration

### Environment Variables
Add to your `.env` file:
```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
VECTOR_STORE_DIRECTORY=./data/vector_store
```

### Default Ports
- **Milvus gRPC**: 19530
- **Milvus REST API**: 9091
- **Etcd**: 2379
- **MinIO**: 9000

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if Milvus is running
   docker ps | grep milvus
   
   # Restart if needed
   docker restart milvus-standalone
   ```

2. **Port Conflicts**
   ```bash
   # Check what's using port 19530
   netstat -tlnp | grep 19530
   
   # Kill conflicting processes or change Milvus port
   ```

3. **Memory Issues**
   ```bash
   # Milvus requires at least 8GB RAM
   # Check available memory
   free -h
   ```

### Health Check
```bash
# Check Milvus status
curl -X GET "http://localhost:9091/health"

# Expected response: {"status":"ok"}
```

## Performance Tuning

### For Development
```yaml
# docker-compose.yml
environment:
  ETCD_CONFIG_PATH: /milvus/configs/advanced/etcd.yaml
  MINIO_CONFIG_PATH: /milvus/configs/advanced/minio.yaml
  PULSAR_CONFIG_PATH: /milvus/configs/advanced/pulsar.yaml
```

### For Production
- Allocate at least 16GB RAM
- Use SSD storage for better performance
- Consider distributed deployment for high load

## Useful Commands

```bash
# Start Milvus
docker start milvus-standalone

# Stop Milvus
docker stop milvus-standalone

# View logs
docker logs milvus-standalone

# Backup data
docker exec milvus-standalone cp -r /var/lib/milvus /backup/

# Remove all data (CAUTION!)
docker exec milvus-standalone rm -rf /var/lib/milvus/*
```

## Integration with K-Array Chat

Once Milvus is running:

1. **Setup the chat system**:
   ```bash
   python setup_chat.py
   ```

2. **Start the chat interface**:
   ```bash
   python k_array_chat.py
   ```

3. **Access the chat**: http://localhost:7860

## References
- [Milvus Documentation](https://milvus.io/docs)
- [Docker Installation](https://docs.docker.com/get-docker/)
- [Milvus Python SDK](https://milvus.io/docs/install-pymilvus.md)