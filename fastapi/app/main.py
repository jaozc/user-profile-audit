from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router

# Initialize the FastAPI application with metadata
app = FastAPI(
    title="User Audit API",
    description="This API manages user audit events, providing functionality to track changes and actions performed on user profiles.",
    version="1.0.0",
    contact={"name": "Joao Costa", "email": "jgabrielzcost@gmail.com"},
    license_info={"name": "MIT License"}
)

# CORS (Cross-Origin Resource Sharing) configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow credentials to be included in requests
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include the API router with a specified prefix
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def read_root():
    """
    Root endpoint that returns a welcome message for the User Audit API.
    
    Returns:
        dict: A JSON object containing a welcome message.
    """
    return {"message": "Welcome to the User Audit API!"}

