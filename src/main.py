from fastapi import FastAPI

app = FastAPI(
    title="AI Literature Review Assistant",
    description="Backend API for an AI-powered literature review assistant",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "AI Literature Review Assistant",
        "version": "0.1.0",
    }