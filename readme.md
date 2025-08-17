# Gmail Service

- Authenticates with Gmail API using OAuth.  
- Fetches and stores emails in a local SQLite database.  
- Applies rule-based processing on stored emails (mark as read, move message, etc.).  
- Provides a FastAPI-based OpenAPI interface to query and test email fetching & rule execution.

To execute the service locally,
1. Create a Poetry virtual environment and setup poetry
2. Install dependencies with **poetry install** command
3. Run api/email_service/orchestrator.fetch_and_store() once, which redirects to oauth and fetches latest mails into in-memory store
4. Optionally, setup rules in rules.json
5. Run main.py to start uvicorn server