"""
Run the FastAPI application
Migrated from Flask to FastAPI
"""
import logging
import uvicorn

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logging.info("Starting the FastAPI app on port 5000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
