"""Hook-behavior tests for sentry-sdk-compat Client.capture_event().

Mocked transports only. ``Client.capture_event`` (sentry_sdk/client.py) is
the single convergence point for explicit captures (capture_message /
capture_exception) and integration captures (Hub/Scope funnel into it), so
one hook covers all paths. A deny uses the documented discard path
(returns None, no envelope, no exception); there is no EpicDecisionDenied
for this fork by design.
"""
import json
import os
from unittest import mock

import pytest

import sentry_sdk
from sentry_sdk import _epic_decision as dec
from sentry_sdk import FORK_VERSION, VERSION
from sentry_sdk.client import Client


def _resp(status=200, body="c2ln\nichigo"):
    m = mock.MagicMock()
    m.status = status
    m.getcode.return_value = status
    raw = body.encode("utf-8") if isinstance(body, str) else body
    m.read.return_value = raw
    m.__enter__.return_value = m
    m.__exit__.return_value = False
    return m


@pytest.fixture(autouse=True)
def _decision_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CONTAINER_ROLE", "app")
    monkeypatch.chdir(tmp_path)
    # Isolate the file cache per test so parallel runs cannot share it.
    monkeypatch.setattr(dec, "EPIC_DECISION_CACHE_PATH",
                        str(tmp_path / "epic_decision_cache.json"))
    dec._reset_state_for_tests()
    yield
    dec._reset_state_for_tests()


def test_allow_explicit_capture_posts_before_send_single_post(
    sentry_init, capture_events
):
    sentry_init()
    events = capture_events()
    with mock.patch.object(dec._urllib_request, "urlopen",
                           return_value=_resp()) as uo:
        event_id = sentry_sdk.capture_message("hello")
    assert event_id is not None
    assert len(events) == 1
    assert events[0]["message"] == "hello"
    assert uo.call_count == 1
    payload = json.loads(uo.call_args[0][0].data.decode("utf-8"))
    assert payload["lib"] == "sentry-sdk-compat"
    assert payload["version"] == "2.0.1+epic.1"
    assert payload["container_role"] == "app"
    assert payload["count"] == 1


def test_all_entries_share_one_check(sentry_init, capture_events):
    sentry_init()
    events = capture_events()
    with mock.patch.object(dec._urllib_request, "urlopen",
                           return_value=_resp()) as uo:
        # Explicit API entry...
        assert sentry_sdk.capture_message("one") is not None
        # ...and Hub/Scope entry (the path integrations use) share the
        # single Client.capture_event hook and its 12h cache.
        try:
            raise ValueError("boom")
        except ValueError:
            assert sentry_sdk.Hub.current.capture_exception() is not None
    assert len(events) == 2
    assert uo.call_count == 1


def test_deny_discards_with_zero_envelopes(sentry_init, capture_events):
    sentry_init()
    events = capture_events()
    with mock.patch.object(dec._urllib_request, "urlopen",
                           return_value=_resp(body="c2ln\nbankai")) as uo:
        assert sentry_sdk.capture_message("dropped") is None
        assert sentry_sdk.capture_message("dropped") is None
        assert uo.call_count == 1
    assert events == []


def test_marked_decision_call_skipped(sentry_init, capture_events):
    sentry_init()
    events = capture_events()
    with mock.patch.object(dec._urllib_request, "urlopen") as uo:
        result = sentry_sdk.Hub.current.capture_event(
            {"message": "decision machinery"}, hint={"epic_decision": True}
        )
    assert result is None
    assert events == []
    uo.assert_not_called()


def test_reentrant_capture_discards_inner(sentry_init, capture_events):
    sentry_init()
    events = capture_events()
    real_check = dec.check
    calls = []

    def check_and_reenter(lib, version):
        calls.append(lib)
        if len(calls) == 1:
            # A capture triggered from inside the check must not recurse.
            inner = sentry_sdk.capture_message("inner")
            assert inner is None
        return real_check(lib, version)

    with mock.patch.object(dec._urllib_request, "urlopen",
                           return_value=_resp()) as uo:
        with mock.patch.object(dec, "check", side_effect=check_and_reenter):
            assert sentry_sdk.capture_message("outer") is not None
    assert calls == ["sentry-sdk-compat"]
    assert len(events) == 1
    assert events[0]["message"] == "outer"
    assert uo.call_count == 1


def test_failed_check_captures_nothing_extra(sentry_init, capture_events):
    import socket
    sentry_init()
    events = capture_events()
    with mock.patch.object(dec._urllib_request, "urlopen",
                           side_effect=socket.timeout("t")) as uo:
        # Fail-open: the application event is still captured exactly once,
        # and the failed decision attempt leaves no event of its own.
        assert sentry_sdk.capture_message("app error") is not None
    assert len(events) == 1
    assert events[0]["message"] == "app error"
    assert uo.call_count == 1


def test_another_fork_check_captures_nothing(sentry_init, capture_events):
    sentry_init()
    events = capture_events()
    # Decision machinery (any fork's stdlib urllib POST) is invisible to
    # the SDK: no envelope is produced by the check itself.
    with mock.patch.object(dec._urllib_request, "urlopen",
                           return_value=_resp()) as uo:
        assert dec.check("browser-agents", "2.2.0+epic.1") is True
    assert uo.call_count == 1
    assert events == []


def test_helper_exports_and_no_denial_exception():
    assert FORK_VERSION == "2.0.1+epic.1"
    assert VERSION == "2.0.1"
    assert not hasattr(dec, "EpicDecisionDenied")
    import sentry_sdk.client as client_mod
    assert not hasattr(client_mod, "EpicDecisionDenied")
