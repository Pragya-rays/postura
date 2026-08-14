import uuid


def _email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@example.com"


async def test_register_login_me_logout_flow(client) -> None:
    email = _email()
    password = "correct-horse-battery-staple"

    register_resp = await client.post("/auth/register", json={"email": email, "password": password})
    assert register_resp.status_code == 201
    assert register_resp.json()["email"] == email
    assert "postura_session" in register_resp.cookies

    me_resp = await client.get("/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 204

    me_after_logout = await client.get("/auth/me")
    assert me_after_logout.status_code == 401


async def test_duplicate_registration_rejected(client) -> None:
    email = _email()
    payload = {"email": email, "password": "correct-horse-battery-staple"}

    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 400


async def test_login_wrong_password_rejected(client) -> None:
    email = _email()
    await client.post("/auth/register", json={"email": email, "password": "correct-horse-battery-staple"})

    resp = await client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert resp.status_code == 401


async def test_login_unknown_email_rejected_with_generic_message(client) -> None:
    resp = await client.post("/auth/login", json={"email": _email(), "password": "whatever"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


async def test_me_without_cookie_is_401(client) -> None:
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
