import os
import sys

# Check if we are running in an IDE/development environment
# We are in development if we are not frozen (compiled)
# Can be overridden by the MY_APP_ENV environment variable
IS_DEVELOPMENT: bool = not getattr(sys, "frozen", False)

if "MY_APP_ENV" in os.environ:
    IS_DEVELOPMENT = os.environ["MY_APP_ENV"] == "development"
