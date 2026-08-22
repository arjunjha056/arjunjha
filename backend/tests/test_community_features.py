import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


def test_profile_room_reply_reaction_and_discovery():
    session = requests.Session()
    login = session.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@nsec.edu", "password": "nsec-admin-2026"})
    assert login.status_code == 200

    profile = session.get(f"{BASE_URL}/api/auth/me").json()
    update = session.put(f"{BASE_URL}/api/profile", json={
        "name": profile["name"], "relationship": "Prefer not to say",
        "department": "TEST Information Technology", "bio": "TEST biography",
        "headline": "TEST academic headline", "interests": ["TEST AI"], "avatar": ""
    })
    assert update.status_code == 200 and update.json()["department"] == "TEST Information Technology"

    rooms = session.get(f"{BASE_URL}/api/rooms").json()
    room_id = rooms[0]["id"]
    marker = f"TEST room {uuid.uuid4().hex}"
    parent = session.post(f"{BASE_URL}/api/rooms/{room_id}/posts", json={"body": marker})
    assert parent.status_code == 200 and parent.json()["parent_id"] is None
    parent_id = parent.json()["id"]
    reply = session.post(f"{BASE_URL}/api/rooms/{room_id}/posts", json={"body": marker + " reply", "parent_id": parent_id})
    assert reply.status_code == 200 and reply.json()["parent_id"] == parent_id
    reacted = session.post(f"{BASE_URL}/api/rooms/{room_id}/posts/{parent_id}/react")
    assert reacted.status_code == 200 and reacted.json()["reactions"]["thoughtful"] == 1
    unreacted = session.post(f"{BASE_URL}/api/rooms/{room_id}/posts/{parent_id}/react")
    assert unreacted.status_code == 200 and unreacted.json()["reactions"]["thoughtful"] == 0

    discovery = session.get(f"{BASE_URL}/api/discover", params={"q": "TEST Information Technology"})
    assert discovery.status_code == 200 and any(p["department"] == "TEST Information Technology" for p in discovery.json()["people"])