from dependency_injector import containers, providers

from gmail_helper.api.email_service.orchestrator import GmailOrchestrator
from gmail_helper.api.email_service.router import EmailRouter
from gmail_helper.api.email_service.rules_processor import RulesProcessor
from gmail_helper.api.email_service.service import EmailService
from gmail_helper.common.config import Config
from gmail_helper.common.contracts.emails_interface import EmailsInterface
from gmail_helper.common.services.gmail_service import GmailClient
from gmail_helper.stores.emails_store import EmailsStore


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

    gmail_client = providers.Singleton(
        GmailClient,
        credentials_file=providers.Callable(lambda c: c.CREDENTIALS_FILE, config),
        token_file=providers.Callable(lambda c: c.TOKEN_FILE, config),
        scopes=providers.Callable(lambda c: c.SCOPES, config),
    )

    rp = providers.Singleton(
        RulesProcessor,
        store=emails_store,
        rules_file=providers.Callable(lambda c: c.RULES_FILE, config),
        gmail_client=gmail_client,  # pass the shared client
    )
    orchestrator = providers.Factory(
        GmailOrchestrator,
        gmail_client=gmail_client,
        store=emails_store,
        rules_processor=rp,
    )

    # Routers
    email_router = providers.Factory(
        EmailRouter,
        email_service=email_service,
    )
