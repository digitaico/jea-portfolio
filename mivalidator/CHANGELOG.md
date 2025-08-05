# Changelog

## [1.1.0] - 2024-01-15

### Added

- **Modern Docker Compose Support**: Updated to use `docker compose` (v2.0+) instead of deprecated `docker-compose`
- **Custom Network**: Added `dicom-network` bridge network for service communication
- **Restart Policies**: Added `restart: unless-stopped` for all services
- **Health Checks**: Implemented health checks for all services
  - Redis: `redis-cli ping`
  - API Gateway: `curl -f http://localhost:8000/health`
  - Status Service: `curl -f http://localhost:8003/health`
  - Validator Service: `pgrep -f python.*main.py`
  - Descriptor Service: `pgrep -f python.*main.py`
- **Service Dependencies**: Enhanced dependency management with health check conditions
- **Container Names**: Added descriptive container names for easier management

### Changed

- **File Rename**: Renamed `docker-compose.yml` to `compose.yaml` (modern standard)
- **Version Field**: Removed deprecated `version` field from compose.yaml
- **Dockerfile Updates**: Added system dependencies for health checks
  - API Gateway & Status Service: Added `curl` for HTTP health checks
  - Validator & Descriptor Services: Added `procps` for process health checks
- **Documentation**: Updated README.md to reflect new Docker Compose commands

### Technical Details

- **Network**: `dicom-network` bridge network for isolated service communication
- **Health Check Intervals**: 30s intervals with 10s timeouts and 3 retries
- **Start Period**: 40s grace period for services to initialize
- **Volume Management**: Improved volume configuration with local driver
- **Environment Variables**: Maintained existing environment variable structure

### Migration Notes

- Update deployment scripts to use `docker compose` instead of `docker-compose`
- No breaking changes to API or service functionality
- Existing data volumes will be preserved
- Services will automatically restart on failure with new restart policies
