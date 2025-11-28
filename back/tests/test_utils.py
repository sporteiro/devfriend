def requires_real_db():
    """Return True if environment variable PYTEST_USE_REAL_DB is NOT set to '1'."""
    import os
    return os.getenv('PYTEST_USE_REAL_DB') != '1'
