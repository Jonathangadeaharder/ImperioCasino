"""
FastAPI main application file
Migrated from Flask to FastAPI
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from imperioApp.utils.config import Config
import logging
import os

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Set up logging
log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s %(name)s : %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Create FastAPI app
app = FastAPI(
    title="ImperioCasino API",
    description="Multi-game online casino platform API",
    version="2.0.0"
)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all HTTP responses"""
    response = await call_next(request)
    
    # Prevent clickjacking attacks
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection in older browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Strict Transport Security (only in production with HTTPS)
    if Config.SESSION_COOKIE_SECURE:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response

# Mount static files
if os.path.exists("imperioApp/static"):
    app.mount("/static", StaticFiles(directory="imperioApp/static"), name="static")

# Include routers
try:
    from imperioApp.api import auth, games, coins
    app.include_router(auth.router, tags=["Authentication"])
    app.include_router(games.router, tags=["Games"])
    app.include_router(coins.router, tags=["Coins"])
except ImportError as e:
    logging.warning(f"Could not import routers: {e}. API routes may not be available.")

# Global error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    logging.warning(f"404 error: {request.url}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logging.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error"}
    )


@app.exception_handler(400)
async def bad_request_handler(request: Request, exc):
    """Handle 400 errors"""
    logging.warning(f"Bad request: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Bad request"}
    )


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    """Handle 401 errors"""
    logging.warning(f"Unauthorized access attempt: {exc}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Unauthorized"}
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint - redirects to dashboard or shows API info"""
    return {
        "message": "ImperioCasino API",
        "version": "2.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
