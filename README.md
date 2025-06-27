# nbx-only-last-runner-extractor-lambda

A Lambda function that calls HTTP endpoints and logs the results with structured logging and New Relic monitoring.

## Features

- **HTTP Endpoint Calling**: Supports GET, POST, PUT, DELETE, and other HTTP methods
- **Structured Logging**: Uses `structlog` for comprehensive JSON-formatted logging
- **New Relic Integration**: Built-in monitoring and distributed tracing
- **Error Handling**: Robust error handling with detailed logging
- **Environment-Based Configuration**: All configuration via environment variables
- **VPC Support**: Can run within VPC for private endpoint access

## Configuration

### Environment Variables

All configuration is done through environment variables:

- `ENDPOINT_URL`: The endpoint URL to call (required)
- `HTTP_METHOD`: HTTP method to use (default: "GET")
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: "30")
- `REQUEST_HEADERS`: JSON string of request headers (optional)
- `REQUEST_DATA`: JSON string of request data for POST/PUT requests (optional)
- `deployedVersion`: Application version (set by CloudFormation)

### CloudFormation Parameters

The following parameters can be set during deployment:

- `EndpointUrl`: The endpoint URL to call
- `HttpMethod`: HTTP method (GET, POST, PUT, DELETE, PATCH)
- `RequestTimeout`: Request timeout in seconds
- `RequestHeaders`: JSON string of request headers
- `RequestData`: JSON string of request data

## Usage Examples

### GET Request Configuration

Set these environment variables:
```bash
ENDPOINT_URL=https://httpbin.org/get
HTTP_METHOD=GET
REQUEST_HEADERS={"User-Agent": "Lambda-Endpoint-Caller/1.0", "Accept": "application/json"}
REQUEST_TIMEOUT=30
```

### POST Request Configuration

Set these environment variables:
```bash
ENDPOINT_URL=https://httpbin.org/post
HTTP_METHOD=POST
REQUEST_HEADERS={"Content-Type": "application/json", "Accept": "application/json"}
REQUEST_DATA={"message": "Hello from Lambda!", "timestamp": "2024-01-01T00:00:00Z"}
REQUEST_TIMEOUT=30
```

## Response Format

The Lambda function returns responses in the following format:

### Success Response

```json
{
  "statusCode": 200,
  "body": {
    "message": "Endpoint called successfully",
    "result": {
      "status_code": 200,
      "headers": {...},
      "data": {...},
      "elapsed_time": 0.123
    }
  }
}
```

### Error Response

```json
{
  "statusCode": 400,
  "body": {
    "error": "No endpoint URL provided"
  }
}
```

## Logging

The function uses structured logging with the following information:

- **Request Details**: URL, method, headers, timeout
- **Response Details**: Status code, response time, content length
- **Error Information**: Detailed error messages with stack traces
- **Lambda Context**: Function name, version, request ID
- **Configuration**: Environment variables used for the request

### Log Examples

```json
{
  "event": "Using configuration from environment variables",
  "endpoint_url": "https://httpbin.org/get",
  "method": "GET",
  "timeout": 30,
  "has_headers": true,
  "has_data": false,
  "timestamp": "2024-01-01T00:00:00.000Z",
  "level": "info"
}
```

## Deployment

### Prerequisites

- AWS SAM CLI
- Python 3.11
- VPC configuration (if calling private endpoints)

### Deploy with Default Configuration

```bash
# Build the application
sam build

# Deploy to AWS with default parameters
sam deploy --guided
```

### Deploy with Custom Configuration

```bash
# Deploy with custom endpoint and method
sam deploy --parameter-overrides \
  envName=dev \
  EndpointUrl=https://api.example.com/endpoint \
  HttpMethod=POST \
  RequestHeaders='{"Authorization": "Bearer token"}' \
  RequestData='{"key": "value"}'
```

### Environment-Specific Deployment

```bash
# Deploy to dev environment
sam deploy --parameter-overrides envName=dev

# Deploy to prod environment
sam deploy --parameter-overrides envName=prod
```

## Testing

### Local Testing

```bash
# Test with empty event (configuration from environment)
sam local invoke -e events/event.json
```

### AWS Testing

```bash
# Invoke deployed function with empty event
aws lambda invoke \
  --function-name dev-only-last-runner-extractor-lambda \
  --payload file://events/event.json \
  response.json
```

## Monitoring

The function integrates with New Relic for:

- **Distributed Tracing**: Track requests across services
- **Performance Monitoring**: Response times and error rates
- **Custom Metrics**: Endpoint-specific metrics
- **Log Aggregation**: Centralized log management

## Security

- **VPC Support**: Can run within private subnets
- **Security Groups**: Configurable network access
- **IAM Roles**: Least privilege access
- **Environment Variables**: Secure configuration management

## Dependencies

- `requests`: HTTP client library
- `structlog`: Structured logging
- `newrelic-lambda`: New Relic monitoring (via Lambda layer)

## License

[Add your license information here]