"""Tests for NEW features: story emoji reactions, trending directory,
plus regression for feed likes/comments, stories, discover."""
import os
import re
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

TINY_PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="


@pytest.fixture(scope="session")
def test_credentials():
    p = Path("/app/memory/test_credentials.md")
    content = p.read_text(encoding="utf-8")
    email = re.search(r'`([^`]+@[^`]+)`', content).group(1)
    pwd = re.search(r'/\s*`([^`]+)`', content).group(1)
    return {"email": email, "password": pwd}


@pytest.fixture(scope="session")
def admin_client(test_credentials):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json=test_credentials)
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    return s


@pytest.fixture(scope="session")
def second_client():
    """Register a fresh student user (second reactor)."""
    s = requests.Session()
    email = f"TEST_student_{uuid.uuid4().hex[:8]}@nsec.edu"
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "name": "TEST Student", "email": email, "password": "test-pass-2026", "role": "student"})
    if r.status_code != 200:
        pytest.fail(f"Register failed {r.status_code}: {r.text[:300]}")
    s.user = r.json()
    return s


@pytest.fixture(scope="session")
def story(admin_client):
    r = admin_client.post(f"{BASE_URL}/api/stories", json={"image": TINY_PNG, "caption": "TEST story"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "_id" not in data
    assert data["caption"] == "TEST story"
    assert data["reactions"] == {}
    return data


# --- NEW: story reactions ---
class TestStoryReactions:
    def test_create_story_appears_in_grouped_feed(self, admin_client, story):
        r = admin_client.get(f"{BASE_URL}/api/stories")
        assert r.status_code == 200
        groups = r.json()
        me = admin_client.get(f"{BASE_URL}/api/auth/me").json()
        grp = next((g for g in groups if g["author_id"] == me["id"]), None)
        assert grp is not None, "own story group missing from GET /api/stories"
        assert any(s["id"] == story["id"] for s in grp["stories"])

    def test_react_add_toggle_and_switch(self, admin_client, story):
        sid = story["id"]
        me = admin_client.get(f"{BASE_URL}/api/auth/me").json()
        # add heart
        r = admin_client.post(f"{BASE_URL}/api/stories/{sid}/react", json={"emoji": "❤️"})
        assert r.status_code == 200, r.text
        assert r.json()["reactions"].get("❤️") == [me["id"]]
        # same emoji again -> removed
        r = admin_client.post(f"{BASE_URL}/api/stories/{sid}/react", json={"emoji": "❤️"})
        assert r.status_code == 200
        assert "❤️" not in r.json()["reactions"]
        # add fire then switch to clap
        admin_client.post(f"{BASE_URL}/api/stories/{sid}/react", json={"emoji": "🔥"})
        r = admin_client.post(f"{BASE_URL}/api/stories/{sid}/react", json={"emoji": "👏"})
        reactions = r.json()["reactions"]
        assert "🔥" not in reactions
        assert reactions.get("👏") == [me["id"]]
        # persistence via GET /api/stories
        groups = admin_client.get(f"{BASE_URL}/api/stories").json()
        found = None
        for g in groups:
            for s in g["stories"]:
                if s["id"] == sid:
                    found = s
        assert found is not None
        assert found["reactions"].get("👏") == [me["id"]]

    def test_two_users_same_emoji_accumulate(self, admin_client, second_client, story):
        sid = story["id"]
        r = second_client.post(f"{BASE_URL}/api/stories/{sid}/react", json={"emoji": "👏"})
        assert r.status_code == 200
        assert len(r.json()["reactions"]["👏"]) == 2

    def test_invalid_emoji_400(self, admin_client, story):
        r = admin_client.post(f"{BASE_URL}/api/stories/{story['id']}/react", json={"emoji": "🍕"})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_unauthenticated_401(self, story):
        r = requests.post(f"{BASE_URL}/api/stories/{story['id']}/react", json={"emoji": "❤️"})
        assert r.status_code == 401

    def test_unknown_story_404(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/stories/{uuid.uuid4()}/react", json={"emoji": "❤️"})
        assert r.status_code == 404

    def test_missing_emoji_field_422(self, admin_client, story):
        r = admin_client.post(f"{BASE_URL}/api/stories/{story['id']}/react", json={})
        assert r.status_code == 422

    def test_create_story_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/stories", json={"image": TINY_PNG})
        assert r.status_code == 401


# --- NEW: trending directory ---
class TestTrendingDirectory:
    def test_trending_returns_ranked_users_with_activity(self, admin_client, second_client):
        # generate activity for the second (fresh) user
        p = second_client.post(f"{BASE_URL}/api/feed", json={"body": "TEST trending post"})
        assert p.status_code == 200
        pid = p.json()["id"]
        for i in range(3):
            c = second_client.post(f"{BASE_URL}/api/feed/{pid}/comments", json={"body": f"TEST c{i}"})
            assert c.status_code == 200

        r = admin_client.get(f"{BASE_URL}/api/directory/trending")
        assert r.status_code == 200, r.text
        items = r.json()
        assert isinstance(items, list) and len(items) > 0
        assert len(items) <= 8
        for it in items:
            assert "activity" in it and isinstance(it["activity"], int)
            assert "id" in it and "name" in it
            assert "password_hash" not in it and "_id" not in it
        scores = [it["activity"] for it in items]
        assert scores == sorted(scores, reverse=True), f"not sorted desc: {scores}"
        uid = second_client.user["id"]
        entry = next((i for i in items if i["id"] == uid), None)
        assert entry is not None, "recently active user missing from trending"
        assert entry["activity"] >= 4

    def test_trending_public_access(self):
        r = requests.get(f"{BASE_URL}/api/directory/trending")
        assert r.status_code == 200


# --- REGRESSION: feed likes & comments ---
class TestFeedLikesComments:
    def test_like_toggle(self, admin_client, second_client):
        pid = admin_client.post(f"{BASE_URL}/api/feed", json={"body": "TEST like post"}).json()["id"]
        r = admin_client.post(f"{BASE_URL}/api/feed/{pid}/like")
        assert r.status_code == 200
        assert r.json()["like_count"] == 1
        assert "_id" not in r.json()
        r = second_client.post(f"{BASE_URL}/api/feed/{pid}/like")
        assert r.json()["like_count"] == 2
        r = admin_client.post(f"{BASE_URL}/api/feed/{pid}/like")
        assert r.json()["like_count"] == 1
        feed = admin_client.get(f"{BASE_URL}/api/feed").json()
        post = next(p for p in feed if p["id"] == pid)
        assert post["like_count"] == 1

    def test_like_unauth_and_404(self, admin_client):
        r = requests.post(f"{BASE_URL}/api/feed/{uuid.uuid4()}/like")
        assert r.status_code == 401
        r = admin_client.post(f"{BASE_URL}/api/feed/{uuid.uuid4()}/like")
        assert r.status_code == 404

    def test_comments_create_list_and_count(self, admin_client):
        pid = admin_client.post(f"{BASE_URL}/api/feed", json={"body": "TEST comment post"}).json()["id"]
        c = admin_client.post(f"{BASE_URL}/api/feed/{pid}/comments", json={"body": "TEST first comment"})
        assert c.status_code == 200, c.text
        cd = c.json()
        assert cd["body"] == "TEST first comment"
        assert cd["post_id"] == pid
        assert "_id" not in cd
        lst = admin_client.get(f"{BASE_URL}/api/feed/{pid}/comments")
        assert lst.status_code == 200
        assert any(x["id"] == cd["id"] for x in lst.json())
        feed = admin_client.get(f"{BASE_URL}/api/feed").json()
        post = next(p for p in feed if p["id"] == pid)
        assert post["comment_count"] == 1

    def test_comment_validation(self, admin_client):
        pid = admin_client.post(f"{BASE_URL}/api/feed", json={"body": "TEST validation post"}).json()["id"]
        assert admin_client.post(f"{BASE_URL}/api/feed/{pid}/comments", json={"body": ""}).status_code == 422
        assert requests.post(f"{BASE_URL}/api/feed/{pid}/comments", json={"body": "x"}).status_code == 401
        assert admin_client.post(f"{BASE_URL}/api/feed/{uuid.uuid4()}/comments", json={"body": "x"}).status_code == 404


# --- REGRESSION: discover ---
class TestDiscover:
    def test_discover_shape(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/discover")
        assert r.status_code == 200
        d = r.json()
        for key in ("people", "rooms", "updates"):
            assert key in d and isinstance(d[key], list)
        assert all("password_hash" not in p for p in d["people"])

    def test_discover_search_filters(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/discover", params={"q": "NSEC Admin"})
        assert r.status_code == 200
        assert any(p["name"] == "NSEC Admin" for p in r.json()["people"])
        r2 = admin_client.get(f"{BASE_URL}/api/discover", params={"q": "zzz-no-match-zzz"})
        assert r2.json()["people"] == []
