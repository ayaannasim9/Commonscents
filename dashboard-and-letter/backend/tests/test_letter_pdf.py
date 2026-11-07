from fastapi.testclient import TestClient

from counterpart.app import create_app
from counterpart.llm.client import LLMClient

import pytest

C = "/customers/MRG-4471"


@pytest.fixture
def client():
    return TestClient(create_app(":memory:", LLMClient(mode="stub")))


def test_pdf_needs_an_approved_letter(client):
    assert client.get(f"{C}/letter.pdf").status_code == 409
    client.post(f"{C}/letter")
    assert client.get(f"{C}/letter.pdf").status_code == 409  # a draft is not sendable (P3)
    client.post(f"{C}/letter/approve")
    r = client.get(f"{C}/letter.pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")
    assert b"/URI" not in r.content  # no links in the file (P6)


def test_preview_works_before_approval(client):
    r = client.get(f"{C}/letter.pdf?preview=true")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


def test_pdf_for_every_persona(client):
    for cid in ("JDN-2208", "AMR-3135", "DAN-5502", "SAM-7316", "RAV-6049"):
        client.post(f"/customers/{cid}/letter/approve")
        assert client.get(f"/customers/{cid}/letter.pdf").content.startswith(b"%PDF"), cid
