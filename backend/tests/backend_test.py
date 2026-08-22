import os
import uuid
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://nsec-community.preview.emergentagent.com").rstrip("/")


def test_admin_auth_cookie_me_logout():
    session = requests.Session()
    login = session.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@nsec.edu", "password": "nsec-admin-2026"})
    assert login.status_code == 200
    assert login.json()["role"] == "founder"
    assert "access_token" in session.cookies
    me = session.get(f"{BASE_URL}/api/auth/me")
    assert me.status_code == 200 and "password" not in me.text
    logout = session.post(f"{BASE_URL}/api/auth/logout")
    assert logout.status_code == 200
    assert session.get(f"{BASE_URL}/api/auth/me").status_code == 401


def test_register_post_feed_persistence_and_student_teacher_block():
    session = requests.Session()
    email = f"test_{uuid.uuid4().hex}@example.com"
    register = session.post(f"{BASE_URL}/api/auth/register", json={"name": "TEST Student", "email": email, "password": "nsec123456", "role": "student"})
    assert register.status_code == 200 and register.json()["role"] == "student"
    post = session.post(f"{BASE_URL}/api/feed", json={"body": "TEST academic update"})
    assert post.status_code == 200 and post.json()["body"] == "TEST academic update"
    assert any(item["id"] == post.json()["id"] for item in session.get(f"{BASE_URL}/api/feed").json())
    blocked = session.post(f"{BASE_URL}/api/teacher-updates", json={"topic": "TEST", "details": "TEST"})
    assert blocked.status_code == 403


def test_public_sections_and_invalid_login():
    rooms = requests.get(f"{BASE_URL}/api/rooms")
    updates = requests.get(f"{BASE_URL}/api/teacher-updates")
    assert rooms.status_code == 200 and len(rooms.json()) >= 1
    assert updates.status_code == 200 and isinstance(updates.json(), list)
    invalid = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "nobody@example.com", "password": "wrongpass"})
    assert invalid.status_code == 401