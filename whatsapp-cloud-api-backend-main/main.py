import uvicorn
import os
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", settings.PORT)),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
