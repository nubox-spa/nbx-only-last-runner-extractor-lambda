import json
import os
import logging
import sys
import requests
import structlog
from typing import Dict, Any, Optional

#################### Logger Configuration ################
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
    force=True
)

# Configure structured logging
structlog.configure(
    processors=[structlog.stdlib.add_logger_name,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.CallsiteParameterAdder(
                    {
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    }
                ),
                structlog.processors.EventRenamer(to="message"),
                structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

def call_endpoint(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, 
                  data: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Call an HTTP endpoint and return the response.
    
    Args:
        url: The endpoint URL to call
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers to include in the request
        data: Optional data to send with the request
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary containing response status, headers, and data
    """
    try:
        logger.info("Calling endpoint", url=url, method=method, headers=headers)
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers or {},
            json=data,
            timeout=timeout
        )
        
        # Log response details
        logger.info(
            "Endpoint response received",
            url=url,
            status_code=response.status_code,
            response_time=response.elapsed.total_seconds(),
            content_length=len(response.content)
        )
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": response_data,
            "elapsed_time": response.elapsed.total_seconds()
        }
        
    except requests.exceptions.Timeout:
        logger.error("Request timeout", url=url, timeout=timeout)
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Request failed", url=url, error=str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error during request", url=url, error=str(e))
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event data (not used for configuration)
        context: Lambda context
    
    Returns:
        Dictionary containing the result of the endpoint call
    """
    logger.info("Lambda function started", 
                function_name=context.function_name,
                function_version=context.function_version,
                request_id=context.aws_request_id)
    
    try:
        # Get endpoint configuration from environment variables only
        endpoint_url = os.environ.get('ENDPOINT_URL')
        if not endpoint_url:
            error_msg = "No endpoint URL provided. Set ENDPOINT_URL environment variable."
            logger.error(error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }
        
        # Get configuration from environment variables
        method = os.environ.get('HTTP_METHOD', 'POST')
        timeout = int(os.environ.get('REQUEST_TIMEOUT', '30'))
        
        # Parse headers from environment variable (JSON string)
        headers = {}
        headers_env = os.environ.get('REQUEST_HEADERS')
        if headers_env:
            try:
                headers = json.loads(headers_env)
            except json.JSONDecodeError:
                logger.warning("Invalid REQUEST_HEADERS JSON format, using empty headers")
        
        # Parse data from environment variable (JSON string)
        data = None
        data_env = os.environ.get('REQUEST_DATA')
        if data_env:
            try:
                data = json.loads(data_env)
            except json.JSONDecodeError:
                logger.warning("Invalid REQUEST_DATA JSON format, ignoring data")
        
        # Log configuration
        logger.info("Using configuration from environment variables",
                   endpoint_url=endpoint_url,
                   method=method,
                   timeout=timeout,
                   has_headers=bool(headers),
                   has_data=bool(data))
        
        # Call the endpoint
        result = call_endpoint(
            url=endpoint_url,
            method=method,
            headers=headers,
            data=data,
            timeout=timeout
        )
        
        # Log the complete result
        logger.info("Endpoint call completed successfully", 
                   url=endpoint_url,
                   status_code=result['status_code'],
                   elapsed_time=result['elapsed_time'])
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Endpoint called successfully",
                "result": result
            })
        }
        
    except Exception as e:
        logger.error("Lambda function failed", error=str(e), exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }
