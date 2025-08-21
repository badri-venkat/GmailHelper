# Gmail Service

- Authenticates with Gmail API using OAuth.  
- Fetches and stores emails in a local SQLite database.  
- Applies rule-based processing on stored emails (mark as read, move message, etc.).  
- Provides a FastAPI-based OpenAPI interface to query and test email fetching & rule execution.

To execute the service locally,
(Make sure latest changes are pulled from "main" branch)
1. Create a Poetry virtual environment and setup poetry
2. Install dependencies with **poetry install** command
3. Open tests/manual/test_orchestrate.py
4. Run test #1 in main.py, which redirects to oauth and fetches latest mails into in-memory store
5. Setup rules in rules.json
6. Run test #2 in main.py, to run rules in rules.json

To test the APIs,
1. Run main.py to start uvicorn server
2. Open http://0.0.0.0:8000/docs to view the OpenAPI interface

# Issues with current design
1. Rules should be managed with CRUD API and should be applied by passing rule_id
2. Credentials shouldn't be stored in-memory, instead should be stored & fetched from AWS Systems Manager or any credentials store