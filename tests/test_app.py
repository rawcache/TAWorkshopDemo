import pytest

import app as task_app
from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory task store before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])
    task_app.next_id = 3


def test_index(client):
    """Verify that the task tracker page renders."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Verify that listing tasks adds a default priority."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


def test_add_task_success(client):
    """Verify that a task can be created without a priority."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    created_task = response.get_json()
    assert created_task['title'] == "Test new task"
    assert created_task['priority'] == "Medium"

    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_priorities(client):
    """Verify that Low, Medium, and High priorities are preserved."""
    for priority in ('Low', 'Medium', 'High'):
        response = client.post(
            '/api/tasks',
            json={"title": f"{priority} task", "priority": priority}
        )
        assert response.status_code == 201
        assert response.get_json()['priority'] == priority

    priorities = [
        task['priority'] for task in client.get('/api/tasks').get_json()
    ]
    assert priorities[-3:] == ['Low', 'Medium', 'High']


def test_empty_priority_defaults_to_medium(client):
    """Verify that an empty priority defaults to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Empty priority task", "priority": ""}
    )
    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_invalid_priority(client):
    """Verify that unsupported priorities are rejected."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority task", "priority": "Urgent"}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_add_task_missing_title(client):
    """Verify that a task title is required."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response = client.post('/api/tasks', json={})
    assert response.status_code == 400


def test_delete_task(client):
    """Verify that deleting an existing task still works."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200

    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
    assert data[0]['priority'] == 'Medium'
