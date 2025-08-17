from dependency_injector import containers, providers

from gmail_helper.api.email_service.router import EmailRouter
from gmail_helper.api.email_service.service import EmailService
from gmail_helper.common.config import Config
from gmail_helper.common.contracts.emails_interface import EmailsInterface

# Simulated RPC: bind contract to worker implementation today
from gmail_helper.worker.emails_store import EmailsStore


class ApiContainer(containers.DeclarativeContainer):
    """Application DI container for the API layer."""

    wiring_config = containers.WiringConfiguration(
        packages=[
            "gmail_helper.api.email_service",
        ]
    )

    # Config file
    config = providers.Singleton(Config)

    # Stores
    emails_store = providers.Singleton(
        EmailsStore,
        db_path=providers.Callable(lambda c: c.DB_PATH, config),
    )  # type: providers.Provider[EmailsInterface]

    # Services
    email_service = providers.Factory(
        EmailService,
        store=emails_store,
    )

    # Routers
    email_router = providers.Factory(
        EmailRouter,
        service=email_service,
    )
