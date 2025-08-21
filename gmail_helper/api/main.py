import os

from fastapi import FastAPI

from gmail_helper.api.containers import ApiContainer
from gmail_helper.api.email_service.router import EmailRouter
from gmail_helper.common.config import config
from gmail_helper.common.utils.api_framework import add_routers, routers_from_class

# Initialize DI container
container = ApiContainer()

app = FastAPI(title="Gmail Helper API", version="1.0.0")

# Mount routers using decorator framework + container factory
add_routers(app, routers_from_class(EmailRouter, container.email_router))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "gmail_helper.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
    )
