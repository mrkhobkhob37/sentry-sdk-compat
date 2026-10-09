# sentry-sdk-compat 2.0.1+epic.1

`sentry-sdk-compat` is a fork of [`sentry-sdk`](https://github.com/getsentry/sentry-python) **2.0.1**
(upstream tag `2.0.1`, commit `882ed7f60537113f10d825c48b011c49a6095bda`).

## Rename (Group B: distribution only)

- Distribution name: `sentry-sdk` -> `sentry-sdk-compat`
- Import package unchanged: `sentry_sdk`; Django/logging integration
  behavior unchanged.
- Fork version: `2.0.1+epic.1` (`sentry_sdk.FORK_VERSION` and
  `sentry_sdk._epic_decision.EPIC_FORK_VERSION`, frozen `version=` in
  `setup.py`); upstream `sentry_sdk.VERSION` remains `2.0.1`.
- Not published on PyPI under either name; install from release assets.

## Decision check

- New private helper `sentry_sdk/_epic_decision.py` (stdlib only).
- Hook point (recorded per Task 9): `sentry_sdk/client.py` ::
  `Client.capture_event` — the single convergence point reached by
  explicit captures (`capture_message` / `capture_exception` via
  Hub/Scope) and by integration captures (including the Django
  integration). It performs a synchronous `POST` to the compiled decision
  endpoint (`EPIC_DECISION_API_URL`) before the event is prepared or sent,
  then re-checks every 12 hours; the payload is exactly `container_role`,
  `timestamp`, `lib`, `version`, `count`.
- Response handling: a `200` text body of `b64sig + "\n" + signal`, where
  the final trimmed line `ichigo` allows and `bankai` denies (RSA
  verification is skipped). A deny uses the documented discard path:
  `capture_event` returns `None` with no envelope sent and no exception
  raised (same as no-DSN/sampling), until a later valid check allows
  captures again. There is intentionally no `EpicDecisionDenied` for this
  fork — raising from fire-and-forget capture calls could break
  application error paths.
- Re-entrancy guard (context-local flag): a capture triggered from inside
  a decision check is discarded without checking again. Captures carrying
  a `{"epic_decision": True}` hint — marked decision-check calls,
  including from other forks — are never captured. Decision machinery
  (stdlib urllib POSTs) is invisible to the SDK: bounded event/POST
  activity, no recursion.
- Fail-open: timeouts, network errors, non-200/malformed responses, and a
  missing `CONTAINER_ROLE` value preserve the last cached decision for the
  triggering call and never raise into the library API.
- Decision state is cached in `/tmp/epic_decision_cache.json`
  (`{"decision": ..., "next_check": ...}`); first run defaults to allow.
- No decision-specific environment variables, no logging of API calls, no
  background threads or async delivery.
- No logs related to API calls appear in container stdout or Sentry: the
  helper never logs, and its stdlib urllib transport triggers no SDK
  integration.

## Other changes vs upstream

- Upstream test suite preserved under `tests/` (pytest); new tests
  `tests/test_epic_decision.py` and `tests/test_sentry_sdk_hook.py` cover
  the decision contract (allow/deny, caching, 12h recheck, fail-open
  paths, request ordering, concurrency, fork reset) and hook behaviour
  (explicit + Hub/Scope entries share one check, deny discards with zero
  envelopes, marked-hint skip with zero POSTs, re-entrant discard without
  recursion, failed check leaves no extra event, another fork's check
  leaves zero envelopes).
- Ordinary tests run with `CONTAINER_ROLE` unset (fail-open, zero POSTs).
- Test env note: suite needs `executing`, `jsonschema`, `werkzeug`,
  Django (upstream test deps); 11 failures in client/api/basics
  (socks-proxy ×8, atexit subprocess ×2, auto-enabling ×1) reproduce
  identically on pristine upstream in this env (pre-existing).
- `README.md` documents the fork, rename, decision-check behavior, and
  non-PyPI installation.

## License

MIT (`LICENSE`), preserved from upstream.
