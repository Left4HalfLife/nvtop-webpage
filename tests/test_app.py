import os
from unittest.mock import patch

os.environ["AUTH_PASSWORD"] = "test-password"
os.environ["SECRET_KEY"] = "test-secret"

import app


def test_healthcheck_is_public():
    response = app.app.test_client().get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_status_requires_authentication():
    response = app.app.test_client().get("/api/status")

    assert response.status_code == 401


def test_login_rejects_invalid_and_malformed_credentials():
    client = app.app.test_client()

    assert client.post("/api/login", json={"user": [], "password": {}}).status_code == 401
    assert client.post(
        "/api/login",
        json={"user": "nvtop-admin", "password": "wrong"},
    ).status_code == 401


def test_authenticated_status_and_action_are_executed_without_shell(tmp_path):
    client = app.app.test_client()
    app.LOG_PATH = tmp_path / "action.log"
    login = client.post(
        "/api/login",
        json={"user": "nvtop-admin", "password": "test-password"},
    )
    assert login.status_code == 200

    with patch("app.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = "GPU 0"
        run.return_value.stderr = ""

        assert client.get("/api/status").get_json()["output"] == "GPU 0"
        assert client.post("/api/action/list_gpus").status_code == 200

    assert run.call_args.kwargs["shell"] is False
    assert "action=list_gpus result=exit-0" in app.LOG_PATH.read_text()


def test_logout_clears_session():
    client = app.app.test_client()
    client.post(
        "/api/login",
        json={"user": "nvtop-admin", "password": "test-password"},
    )

    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/status").status_code == 401