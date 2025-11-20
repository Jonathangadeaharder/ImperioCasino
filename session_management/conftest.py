"""
Pytest configuration and fixtures for ImperioCasino testing.

This module provides comprehensive test fixtures for unit and integration testing.
"""

import pytest
import os
import tempfile
from faker import Faker

# Set test environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['RATELIMIT_STORAGE_URL'] = 'memory://'

from imperioApp import app as flask_app, db
from imperioApp.utils.models import User, BlackjackGameState
from imperioApp.utils.auth import generate_token
from imperioApp.utils.services import create_user

fake = Faker()


@pytest.fixture(scope='session')
def app():
    """
    Create application for testing with test configuration.

    This fixture is session-scoped, meaning it's created once per test session.
    """
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': False,  # Disable rate limiting in tests
        'SERVER_NAME': 'localhost.localdomain',  # For url_for to work
        'PREFERRED_URL_SCHEME': 'http',
    })

    return flask_app


@pytest.fixture(scope='function')
def client(app):
    """
    Create test client for making requests.

    This fixture is function-scoped, meaning it's recreated for each test.
    """
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def app_context(app):
    """
    Provide application context for tests that need it.

    Usage:
        def test_something(app_context):
            # Code here runs within app context
            user = User.query.first()
    """
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(app_context):
    """
    Create a test user with default credentials.

    Returns:
        User: Test user with username='testuser', password='testpass123', coins=1000
    """
    user = create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        starting_coins=1000
    )
    db.session.commit()
    return user


@pytest.fixture
def test_user_poor(app_context):
    """
    Create a test user with insufficient coins.

    Returns:
        User: Test user with only 5 coins
    """
    user = create_user(
        username='pooruser',
        email='poor@example.com',
        password='testpass123',
        starting_coins=5
    )
    db.session.commit()
    return user


@pytest.fixture
def test_user_rich(app_context):
    """
    Create a test user with lots of coins.

    Returns:
        User: Test user with 10000 coins
    """
    user = create_user(
        username='richuser',
        email='rich@example.com',
        password='testpass123',
        starting_coins=10000
    )
    db.session.commit()
    return user


@pytest.fixture
def multiple_users(app_context):
    """
    Create multiple test users with varying coin balances.

    Returns:
        list: List of 5 User objects
    """
    users = []
    for i in range(5):
        user = create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='testpass123',
            starting_coins=1000 * (i + 1)
        )
        users.append(user)
    db.session.commit()
    return users


@pytest.fixture
def auth_token(test_user):
    """
    Generate authentication token for test user.

    Returns:
        str: JWT token for test_user
    """
    return generate_token(test_user.username)


@pytest.fixture
def auth_headers(auth_token):
    """
    Create authentication headers for API requests.

    Returns:
        dict: Headers dictionary with Authorization token
    """
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def authenticated_client(client, test_user):
    """
    Create an authenticated test client.

    This client is already logged in with test_user credentials.
    """
    with client:
        with client.session_transaction() as sess:
            sess['user_id'] = test_user.id
            sess['token'] = generate_token(test_user.username)
        yield client


@pytest.fixture
def blackjack_game(test_user, app_context):
    """
    Create a blackjack game state for testing.

    Returns:
        BlackjackGameState: Active game with test_user
    """
    game = BlackjackGameState(
        user_id=test_user.id,
        deck=['2H', '3H', '4H', '5H', '6H'],
        dealer_hand=['KH'],
        player_hand=['AH', '10H'],
        player_coins=test_user.coins,
        current_wager=10,
        game_over=False,
        message='',
        player_stood=False,
        double_down=False,
        split=False,
        current_hand='first'
    )
    db.session.add(game)
    db.session.commit()
    return game


@pytest.fixture
def mock_redis(mocker):
    """
    Mock Redis for tests that interact with rate limiting.

    Returns:
        Mock: Mocked Redis client
    """
    mock = mocker.patch('redis.from_url')
    mock.return_value.ping.return_value = True
    return mock


@pytest.fixture
def disable_rate_limiting(app):
    """
    Temporarily disable rate limiting for specific tests.

    Usage:
        def test_something(client, disable_rate_limiting):
            # Rate limiting is disabled here
            response = client.post('/login', data={...})
    """
    original_enabled = app.config.get('RATELIMIT_ENABLED', True)
    app.config['RATELIMIT_ENABLED'] = False
    yield
    app.config['RATELIMIT_ENABLED'] = original_enabled


@pytest.fixture
def sample_coins_data():
    """
    Provide sample coin amounts for testing.

    Returns:
        dict: Various coin amounts for different scenarios
    """
    return {
        'zero': 0,
        'small': 10,
        'medium': 100,
        'large': 1000,
        'huge': 10000,
        'negative': -100,
    }


@pytest.fixture
def fake_user_data():
    """
    Generate fake user data using Faker.

    Returns:
        dict: Dictionary with fake username, email, password
    """
    return {
        'username': fake.user_name()[:20],  # Limit length
        'email': fake.email(),
        'password': fake.password(length=12)
    }


@pytest.fixture(autouse=True)
def reset_database(app_context):
    """
    Automatically reset database between tests.

    This fixture runs before every test to ensure a clean database state.
    """
    yield
    # Cleanup after test
    db.session.remove()
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@pytest.fixture
def capture_logs(caplog):
    """
    Capture application logs during testing.

    Usage:
        def test_something(capture_logs):
            # ... test code ...
            assert 'Expected log message' in capture_logs.text
    """
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "game: marks tests as game logic tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark unit tests
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        # Mark API tests
        if "test_routes" in item.nodeid or "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        # Mark game tests
        if "test_blackjack" in item.nodeid or "test_roulette" in item.nodeid or "test_cherrycharm" in item.nodeid:
            item.add_marker(pytest.mark.game)
