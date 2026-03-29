from database import engine

def test_db_connection():
    with engine.connect() as connection:
        assert connection is not None