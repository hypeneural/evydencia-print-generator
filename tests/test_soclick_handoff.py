"""Unit tests for the SoClic handoff client and discovery in Print Generator."""
from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from evydencia_print_generator.domain.job import (
    JobSnapshot,
    JobSource,
    SlotEdit,
    SlotTransform,
)
from evydencia_print_generator.soclick.client import (
    PanelUnavailableError,
    SoclicHandoffError,
    prepare_soclic_draft,
)
from evydencia_print_generator.soclick.discovery import _is_port_healthy, discover_panel_port
from PIL import Image


def _make_dummy_image(path: Path) -> None:
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(path, "JPEG")


def test_discover_panel_port_returns_none_when_no_server_running():
    with patch("evydencia_print_generator.soclick.discovery._is_port_healthy", return_value=False):
        port = discover_panel_port()
        assert port is None


def test_discover_panel_port_finds_active_port():
    def fake_healthy(port: int, timeout_sec: float = 0.8) -> bool:
        return port == 8095

    with patch(
        "evydencia_print_generator.soclick.discovery._is_port_healthy",
        side_effect=fake_healthy,
    ):
        port = discover_panel_port()
        assert port == 8095


def test_discover_panel_port_respects_env_var(monkeypatch):
    monkeypatch.setenv("EVYDFLOW_PANEL_PORT", "8120")

    def fake_healthy(port: int, timeout_sec: float = 0.8) -> bool:
        return port == 8120

    with patch(
        "evydencia_print_generator.soclick.discovery._is_port_healthy",
        side_effect=fake_healthy,
    ):
        port = discover_panel_port()
        assert port == 8120


def test_prepare_soclic_draft_fails_closed_when_file_not_found(tmp_path):
    dummy_snapshot = JobSnapshot(
        template_id="chaveiro-3x4",
        template_version="1.0.0",
        sources={},
        slot_edits={},
    )
    non_existent = tmp_path / "does_not_exist.jpg"
    with pytest.raises(SoclicHandoffError, match="não existe no disco"):
        prepare_soclic_draft(str(non_existent), dummy_snapshot)


def test_prepare_soclic_draft_fails_when_panel_unavailable(tmp_path):
    img_path = tmp_path / "render.jpg"
    _make_dummy_image(img_path)

    dummy_snapshot = JobSnapshot(
        template_id="chaveiro-3x4",
        template_version="1.0.0",
        sources={},
        slot_edits={},
    )

    with patch("evydencia_print_generator.soclick.client.discover_panel_port", return_value=None):
        with pytest.raises(PanelUnavailableError, match="não está em execução"):
            prepare_soclic_draft(str(img_path), dummy_snapshot)


def test_prepare_soclic_draft_successful_dispatch(tmp_path):
    rendered = tmp_path / "output.jpg"
    _make_dummy_image(rendered)

    orig_photo = tmp_path / "Ana #4101" / "foto.jpg"
    orig_photo.parent.mkdir()
    _make_dummy_image(orig_photo)

    source = JobSource(
        source_id="src_1",
        path=orig_photo,
        size_bytes=orig_photo.stat().st_size,
        mtime_ns=orig_photo.stat().st_mtime_ns,
    )
    edit = SlotEdit(
        source_id="src_1",
        transform=SlotTransform(pan_x_norm=0, pan_y_norm=0, scale=1, rotation_deg=0),
    )
    snapshot = JobSnapshot(
        template_id="chaveiro-3x4",
        template_version="1.0.0",
        sources={"src_1": source},
        slot_edits={"slot_01": edit},
    )

    fake_response_data = {
        "ok": True,
        "job_id": "job_print_9988",
        "observation": "Chaveiro | Ana #4101 | 1 folha",
        "panel_url": "http://127.0.0.1:8095/panel/soclick?focus=job_print_9988#review",
        "is_existing": False,
        "total_orders": 1,
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port", return_value=8095),
        patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen,
        patch("webbrowser.open") as mock_browser,
    ):
        res = prepare_soclic_draft(str(rendered), snapshot, open_browser=True)

        assert res["ok"] is True
        assert res["job_id"] == "job_print_9988"
        assert res["observation"] == "Chaveiro | Ana #4101 | 1 folha"
        mock_browser.assert_called_once_with(
            "http://127.0.0.1:8095/panel/soclick?focus=job_print_9988#review"
        )

        # Inspect request payload
        call_args = mock_urlopen.call_args[0]
        req = call_args[0]
        assert req.full_url == "http://127.0.0.1:8095/api/soclick/intake/print-generator"
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["contract_version"] == "1.0"
        assert payload["template_id"] == "chaveiro-3x4"
        assert "slot_01" in payload["slots"]
        assert payload["slots"]["slot_01"]["original_path"] == str(orig_photo)


def test_bridge_prepare_soclic_missing_output_path():
    from evydencia_print_generator.app.bridge import DesktopBridge

    b = DesktopBridge(
        registry=MagicMock(),
        ingest_service=MagicMock(),
        preview_service=MagicMock(),
        server_base_url="http://127.0.0.1:5000",
    )
    res = b.prepare_soclic({}, {})
    assert res["ok"] is False
    assert "ausente" in res["error"]


def test_bridge_prepare_soclic_handles_panel_offline_gracefully(tmp_path):
    from evydencia_print_generator.app.bridge import DesktopBridge
    from evydencia_print_generator.ingest.models import ImageProbe, SourceAsset, SourceIdentity

    rendered = tmp_path / "Chaveiro_test.jpg"
    _make_dummy_image(rendered)

    orig_photo = tmp_path / "foto.jpg"
    _make_dummy_image(orig_photo)

    probe = ImageProbe(
        format="JPEG",
        mode="RGB",
        width_px=100,
        height_px=100,
        stored_width_px=100,
        stored_height_px=100,
        exif_orientation=1,
        has_icc=False,
        icc_description=None,
    )
    registry = MagicMock()
    registry.get.return_value = SourceAsset(
        id="src_1",
        path=orig_photo,
        identity=SourceIdentity(norm_path=str(orig_photo), size_bytes=100, mtime_ns=1000),
        display_name="foto.jpg",
        probe=probe,
    )

    from evydencia_print_generator.paths import templates_dir

    b = DesktopBridge(
        registry=registry,
        ingest_service=MagicMock(),
        preview_service=MagicMock(),
        server_base_url="http://127.0.0.1:5000",
        templates_root=templates_dir(),
    )

    edit_state_dict = {
        "template_id": "chaveiro-3x4",
        "template_version": "1.0.0",
        "slot_edits": {
            "slot_01": {
                "source_id": "src_1",
                "pan_x_norm": 0,
                "pan_y_norm": 0,
                "scale": 1,
                "rotation_deg": 0,
            },
            "slot_02": {
                "source_id": "src_1",
                "pan_x_norm": 0,
                "pan_y_norm": 0,
                "scale": 1,
                "rotation_deg": 0,
            },
        },
    }

    # Production bridge now requires an actual receipt from render_job.
    from evydencia_print_generator.domain.job import EditState, build_job_snapshot
    from evydencia_print_generator.domain.template import load_template
    from evydencia_print_generator.soclick.render_receipt import RenderReceipt

    state = EditState.from_ui(edit_state_dict)
    template = load_template(templates_dir() / "chaveiro-3x4" / "template.json")
    snapshot = build_job_snapshot(template, state, registry.get)
    b._last_render_receipt = RenderReceipt.capture(rendered, state, snapshot)

    with patch("evydencia_print_generator.soclick.client.discover_panel_port", return_value=None):
        res = b.prepare_soclic({"output_path": str(rendered)}, edit_state_dict)
        assert res["ok"] is False
        assert "não está em execução" in res["error"]


def test_discovery_rejects_health_only_foreign_server():

    def response(payload):
        obj = MagicMock()
        obj.status = 200
        obj.read.side_effect = [payload]
        obj.__enter__.return_value = obj
        return obj

    with patch("urllib.request.urlopen", side_effect=[
        response(b'{"ok": true}'),
        response(b'{"detail":"Not Found"}'),
    ]):
        assert _is_port_healthy(8095) is False


def test_discovery_accepts_evydflow_environment_contract():

    def response(payload):
        obj = MagicMock()
        obj.status = 200
        obj.read.side_effect = [payload]
        obj.__enter__.return_value = obj
        return obj

    with patch("urllib.request.urlopen", side_effect=[
        response(b'{"ok":true}'),
        response(
            b'{"environment":"OPERACIONAL","enviar_blocked":true,'
            b'"real_production_allowed":false}'
        ),
    ]) as urlopen:
        assert _is_port_healthy(8095)
        assert "/api/soclick/environment" in urlopen.call_args_list[1].args[0].full_url


def test_discovery_rejects_invalid_port_without_network():
    with patch("urllib.request.urlopen") as urlopen:
        assert not _is_port_healthy(0)
        assert not _is_port_healthy(99999)
        urlopen.assert_not_called()


def test_discovery_rejects_wrong_environment_shape():
    def response(payload):
        obj = MagicMock()
        obj.status = 200
        obj.read.side_effect = [payload]
        obj.__enter__.return_value = obj
        return obj
    with patch("urllib.request.urlopen", side_effect=[
        response(b'{"ok":true}'),
        response(b'{"environment":"OPERACIONAL"}'),
    ]):
        assert not _is_port_healthy(8095)


def test_bridge_rejects_handoff_without_original_render_receipt(tmp_path):
    from evydencia_print_generator.app.bridge import DesktopBridge
    generated = tmp_path / "file.jpg"
    _make_dummy_image(generated)
    bridge = DesktopBridge(
        registry=MagicMock(), ingest_service=MagicMock(),
        preview_service=MagicMock(), server_base_url="http://127.0.0.1:5000",
    )
    with patch("evydencia_print_generator.soclick.client.prepare_soclic_draft") as post:
        result = bridge.prepare_soclic(
            {"output_path": str(generated)},
            {"template_id": "chaveiro-3x4", "template_version": "1.0.0", "slot_edits": {}},
        )
    assert result["ok"] is False
    assert "Sem comprovante" in result["error"]
    post.assert_not_called()


def test_soclic_client_rejects_mutated_jpeg_before_network(tmp_path):
    image = tmp_path / "render.jpg"
    _make_dummy_image(image)
    snapshot = JobSnapshot(
        template_id="chaveiro-3x4", template_version="1.0.0",
        sources={}, slot_edits={},
    )
    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port", return_value=8095),
        patch("urllib.request.urlopen") as post,
    ):
        with pytest.raises(SoclicHandoffError, match="JPEG foi alterado"):
            prepare_soclic_draft(str(image), snapshot, expected_sha256="0" * 64)
    post.assert_not_called()


def test_soclic_client_rejects_cross_origin_panel_link(tmp_path):
    rendered = tmp_path / "output.jpg"
    _make_dummy_image(rendered)
    snapshot = JobSnapshot(
        template_id="chaveiro-3x4", template_version="1.0.0",
        sources={}, slot_edits={},
    )
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "ok": True, "job_id": "job_print_abcd",
        "panel_url": "https://example.invalid/panel/soclick?focus=job_print_abcd#review",
    }).encode()
    mock_response.__enter__.return_value = mock_response
    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port", return_value=8095),
        patch("urllib.request.urlopen", return_value=mock_response),
        patch("webbrowser.open") as browser,
    ):
        with pytest.raises(SoclicHandoffError, match="não corresponde ao rascunho"):
            prepare_soclic_draft(str(rendered), snapshot)
        browser.assert_not_called()


def test_soclic_client_reports_browser_failure_without_losing_draft(tmp_path):
    rendered = tmp_path / "output.jpg"
    _make_dummy_image(rendered)
    snapshot = JobSnapshot(
        template_id="chaveiro-3x4", template_version="1.0.0",
        sources={}, slot_edits={},
    )
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "ok": True, "job_id": "job_print_abcd",
        "panel_url": "http://127.0.0.1:8095/panel/soclick?focus=job_print_abcd#review",
    }).encode()
    mock_response.__enter__.return_value = mock_response
    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port", return_value=8095),
        patch("urllib.request.urlopen", return_value=mock_response),
        patch("webbrowser.open", return_value=False),
    ):
        result = prepare_soclic_draft(str(rendered), snapshot)
    assert result["ok"] is True
    assert result["browser_opened"] is False
    assert result["job_id"] == "job_print_abcd"


@pytest.mark.parametrize(
    ("http_status", "detail", "expected_code"),
    [
        (503, "Configure EVYDFLOW_ALLOWED_ROOTS", "ROOTS_NOT_CONFIGURED"),
        (403, "Access denied for local operator", "OPERATOR_NOT_AUTHORIZED"),
        (503, "Worker not ready", "HANDOFF_UNCERTAIN"),
        (500, "Internal error: C:\\private\\customer.jpg", "HANDOFF_UNCERTAIN"),
        (400, "Corrupt JPEG file", "HANDOFF_REJECTED"),
    ],
)
def test_soclick_http_errors_are_typed_and_do_not_leak_server_details(
    tmp_path, http_status, detail, expected_code
):
    jpeg = tmp_path / "test.jpg"
    _make_dummy_image(jpeg)
    snap = JobSnapshot(template_id="chaveiro-3x4", template_version="1.0.0",
                       sources={}, slot_edits={})
    err = urllib.error.HTTPError(
        "http://127.0.0.1:8095/api/soclick/intake/print-generator",
        http_status, "Server failure", {},
        io.BytesIO(json.dumps({"detail": detail}).encode("utf-8")),
    )
    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port",
              return_value=8095),
        patch("urllib.request.urlopen", side_effect=err),
    ):
        with pytest.raises(SoclicHandoffError) as exc:
            prepare_soclic_draft(str(jpeg), snap, open_browser=False)
    assert exc.value.error_code == expected_code
    assert "C:\\private" not in str(exc.value)
    assert "customer.jpg" not in str(exc.value)


def test_soclick_timeout_is_uncertain_not_offline(tmp_path):
    jpeg = tmp_path / "test.jpg"
    _make_dummy_image(jpeg)
    snap = JobSnapshot(template_id="chaveiro-3x4", template_version="1.0.0",
                       sources={}, slot_edits={})
    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port",
              return_value=8095),
        patch("urllib.request.urlopen",
              side_effect=urllib.error.URLError(TimeoutError("socket timed out"))),
    ):
        with pytest.raises(SoclicHandoffError) as exc:
            prepare_soclic_draft(str(jpeg), snap, open_browser=False)
    assert exc.value.error_code == "HANDOFF_UNCERTAIN"


def test_soclick_malformed_json_shape_is_uncertain_not_a_crash(tmp_path):
    jpeg = tmp_path / "test.jpg"
    _make_dummy_image(jpeg)
    snap = JobSnapshot(template_id="chaveiro-3x4", template_version="1.0.0",
                       sources={}, slot_edits={})
    response = MagicMock()
    response.read.return_value = b'["unexpected", "json"]'
    response.__enter__.return_value = response
    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port",
              return_value=8095),
        patch("urllib.request.urlopen", return_value=response),
    ):
        with pytest.raises(SoclicHandoffError) as exc:
            prepare_soclic_draft(str(jpeg), snap, open_browser=False)
    assert exc.value.error_code == "HANDOFF_UNCERTAIN"

@pytest.mark.parametrize(
    ("reason", "expected_code"),
    [
        (ConnectionRefusedError("actively refused"), "PANEL_OFFLINE"),
        (ConnectionResetError("connection reset after request body"), "HANDOFF_UNCERTAIN"),
        (BrokenPipeError("socket closed during send"), "HANDOFF_UNCERTAIN"),
        (TimeoutError("no response from API"), "HANDOFF_UNCERTAIN"),
        (OSError("unexpected transport error"), "HANDOFF_UNCERTAIN"),
    ],
)
def test_soclick_post_transport_errors_do_not_ask_for_blind_retry(
    tmp_path, reason, expected_code
):
    image = tmp_path / "safe-render.jpg"
    _make_dummy_image(image)
    snapshot = JobSnapshot(
        template_id="chaveiro-3x4", template_version="1.0.0",
        sources={}, slot_edits={},
    )
    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port",
              return_value=8095),
        patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError(reason),
        ) as post,
    ):
        with pytest.raises(SoclicHandoffError) as exc:
            prepare_soclic_draft(str(image), snapshot, open_browser=False)
    assert exc.value.error_code == expected_code
    assert image.exists(), "A network error must not delete the generated JPEG."
    post.assert_called_once()


def test_bridge_unexpected_exception_does_not_leak_private_paths_or_tokens():
    from evydencia_print_generator.app.bridge import DesktopBridge

    bridge = DesktopBridge(
        registry=MagicMock(),
        ingest_service=MagicMock(),
        preview_service=MagicMock(),
        server_base_url="http://127.0.0.1:5000",
    )
    bridge._last_render_receipt = MagicMock()
    with patch(
        "evydencia_print_generator.soclick.prepare_soclic_draft",
        side_effect=RuntimeError(r"C:\\Private\\customer.jpg access token ABC"),
    ):
        result = bridge.prepare_soclic(
            {"output_path": "C:/safe/sample.jpg"},
            {"template_id": "chaveiro-3x4", "template_version": "1.0.0",
             "slot_edits": {}},
        )
    assert result["ok"] is False
    assert result["error_code"] == "HANDOFF_UNCERTAIN"
    assert "customer.jpg" not in result["error"]
    assert "token" not in result["error"].lower()


def test_real_handoff_payload_references_approved_copy_not_arbitrary_original(
    tmp_path, monkeypatch
):
    import hashlib

    source = tmp_path / "external-drive" / "Calendario_FOTO_01.jpg"
    source.parent.mkdir()
    _make_dummy_image(source)
    original_bytes = source.read_bytes()
    approved_root = tmp_path / "evydflow-authorized"
    monkeypatch.setenv("EVYDENCIA_SOCLICK_HANDOFF_DIR", str(approved_root))

    snapshot = JobSnapshot(
        template_id="calendario-2027",
        template_version="1.0.0",
        sources={},
        slot_edits={},
    )
    data = {
        "ok": True,
        "job_id": "job_print_safe123",
        "panel_url": "http://127.0.0.1:8095/panel/soclick"
                     "?focus=job_print_safe123#review",
    }
    response = MagicMock()
    response.read.return_value = json.dumps(data).encode("utf-8")
    response.__enter__.return_value = response

    with (
        patch("evydencia_print_generator.soclick.client.discover_panel_port",
              return_value=8095),
        patch("urllib.request.urlopen", return_value=response) as opened,
    ):
        result = prepare_soclic_draft(str(source), snapshot, open_browser=False)

    assert result["ok"] is True
    payload = json.loads(opened.call_args[0][0].data)
    transmitted = Path(payload["output_path"])
    assert transmitted != source
    assert approved_root.resolve() in transmitted.parents
    assert transmitted.name == source.name
    assert transmitted.read_bytes() == original_bytes
    assert source.read_bytes() == original_bytes
    assert payload["file_sha256"] == hashlib.sha256(original_bytes).hexdigest()
