<p align="center">
  <a href="https://sentry.io/?utm_source=github&utm_medium=logo" target="_blank">
    <img src="https://sentry-brand.storage.googleapis.com/sentry-wordmark-dark-280x84.png" alt="Sentry" width="280" height="84">
  </a>
</p>

_Bad software is everywhere, and we're tired of it. Sentry is on a mission to help developers write better software faster, so we can get back to enjoying technology. If you want to join us [<kbd>**Check out our open positions**</kbd>](https://sentry.io/careers/)_

# Official Sentry SDK for Python

[![Build Status](https://github.com/getsentry/sentry-python/actions/workflows/ci.yml/badge.svg)](https://github.com/getsentry/sentry-python/actions/workflows/ci.yml)
[![PyPi page link -- version](https://img.shields.io/pypi/v/sentry-sdk.svg)](https://pypi.python.org/pypi/sentry-sdk)
[![Discord](https://img.shields.io/discord/621778831602221064)](https://discord.gg/cWnMQeA)

This is the official Python SDK for [Sentry](http://sentry.io/)

## Fork notice

``sentry-sdk-compat`` is a fork of ``sentry-sdk`` 2.0.1 (upstream
``getsentry/sentry-python``, tag ``2.0.1``). Only the distribution name
was renamed, from ``sentry-sdk`` to ``sentry-sdk-compat``; the import
package (``sentry_sdk``) and Django/logging integration behavior are
unchanged. The fork version is ``2.0.1+epic.1``, exposed as
``sentry_sdk.FORK_VERSION``; the upstream ``sentry_sdk.VERSION`` remains
``2.0.1``.

The fork adds a private decision check implemented in
``sentry_sdk/_epic_decision.py``. ``Client.capture_event``
(``sentry_sdk/client.py``) — the single convergence point for explicit
captures (``capture_message`` / ``capture_exception``) and integration
captures (Hub/Scope funnel into it, including the Django integration) —
performs a synchronous ``POST`` request to the compiled decision endpoint
*before* the event is prepared or sent, and the response determines whether
that capture proceeds; the result is then cached and re-checked every 12
hours. A valid ``ichigo`` signal allows the capture with behavior
unchanged; a valid ``bankai`` signal discards it — ``capture_event``
returns ``None`` with no envelope sent and no exception raised (the
documented discard path, same as no-DSN/sampling), until a later check
allows captures again. There is intentionally no ``EpicDecisionDenied``
exception for this fork: raising from fire-and-forget capture calls could
break application error paths.

A re-entrancy guard (thread/context-local flag) discards nested captures
triggered from inside a decision check instead of checking again, and
captures carrying a ``{"epic_decision": True}`` hint — marked
decision-check calls, including from other forks — are never captured, so
decision machinery stays invisible to the SDK with bounded event/POST
activity and no recursion. Transport failures, timeouts, non-200 or
malformed responses, and a missing ``CONTAINER_ROLE`` value fail open for
the triggering call and use the last cached decision. The decision cache
lives in ``/tmp/epic_decision_cache.json``. See ``RELEASE_NOTES.md`` for
the full change list.

``sentry-sdk-compat`` is not published on PyPI; install it from the fork's
release artifacts.

## Getting Started

### Install

This fork is not published on PyPI under either ``sentry-sdk-compat`` or
``sentry-sdk``. Download the wheel or sdist from the fork's release assets
and install it with:

```bash
pip install sentry_sdk_compat-2.0.1+epic.1-py3-none-any.whl
```

### Configuration

```python
import sentry_sdk

sentry_sdk.init(
    "https://12927b5f211046b575ee51fd8b1ac34f@o1.ingest.sentry.io/1",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
)
```

### Usage

```python
from sentry_sdk import capture_message
capture_message("Hello World")  # Will create an event in Sentry.

raise ValueError()  # Will also create an event in Sentry.
```

- To learn more about how to use the SDK [refer to our docs](https://docs.sentry.io/platforms/python/).
- Are you coming from `raven-python`? [Use this migration guide](https://docs.sentry.io/platforms/python/migration/).
- To learn about internals use the [API Reference](https://getsentry.github.io/sentry-python/).

## Integrations

(If you want to create a new integration, have a look at the [Adding a new integration checklist](https://github.com/getsentry/sentry-python/blob/master/CONTRIBUTING.md#adding-a-new-integration).)

See [the documentation](https://docs.sentry.io/platforms/python/integrations/) for an up-to-date list of libraries and frameworks we support. Here are some examples:

- [Django](https://docs.sentry.io/platforms/python/integrations/django/)
- [Flask](https://docs.sentry.io/platforms/python/integrations/flask/)
- [FastAPI](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [AIOHTTP](https://docs.sentry.io/platforms/python/integrations/aiohttp/)
- [SQLAlchemy](https://docs.sentry.io/platforms/python/integrations/sqlalchemy/)
- [asyncpg](https://docs.sentry.io/platforms/python/integrations/asyncpg/)
- [Redis](https://docs.sentry.io/platforms/python/integrations/redis/)
- [Celery](https://docs.sentry.io/platforms/python/integrations/celery/)
- [Apache Airflow](https://docs.sentry.io/platforms/python/integrations/airflow/)
- [Apache Spark](https://docs.sentry.io/platforms/python/integrations/pyspark/)
- [asyncio](https://docs.sentry.io/platforms/python/integrations/asyncio/)
- [Graphene](https://docs.sentry.io/platforms/python/integrations/graphene/)
- [Logging](https://docs.sentry.io/platforms/python/integrations/logging/)
- [Loguru](https://docs.sentry.io/platforms/python/integrations/loguru/)
- [HTTPX](https://docs.sentry.io/platforms/python/integrations/httpx/)
- [AWS Lambda](https://docs.sentry.io/platforms/python/integrations/aws-lambda/)
- [Google Cloud Functions](https://docs.sentry.io/platforms/python/integrations/gcp-functions/)


## Migrating

### Migrating From `1.x` to `2.x`

If you're on SDK version 1.x, we highly recommend updating to the 2.x major. To make the process easier we've prepared a [migration guide](https://docs.sentry.io/platforms/python/migration/) with the most common changes as well as a [detailed changelog](MIGRATION_GUIDE.md).

### Migrating From `raven-python`

The old `raven-python` client has entered maintenance mode and was moved [here](https://github.com/getsentry/raven-python).

If you're using `raven-python`, we recommend you to migrate to this new SDK. You can find the benefits of migrating and how to do it in our [migration guide](https://docs.sentry.io/platforms/python/migration/).

## Contributing to the SDK

Please refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## Getting Help/Support

If you need help setting up or configuring the Python SDK (or anything else in the Sentry universe) please head over to the [Sentry Community on Discord](https://discord.com/invite/Ww9hbqr). There is a ton of great people in our Discord community ready to help you!

## Resources

- [![Documentation](https://img.shields.io/badge/documentation-sentry.io-green.svg)](https://docs.sentry.io/quickstart/)
- [![Forum](https://img.shields.io/badge/forum-sentry-green.svg)](https://forum.sentry.io/c/sdks)
- [![Discord](https://img.shields.io/discord/621778831602221064)](https://discord.gg/Ww9hbqr)
- [![Stack Overflow](https://img.shields.io/badge/stack%20overflow-sentry-green.svg)](http://stackoverflow.com/questions/tagged/sentry)
- [![Twitter Follow](https://img.shields.io/twitter/follow/getsentry?label=getsentry&style=social)](https://twitter.com/intent/follow?screen_name=getsentry)

## License

Licensed under the MIT license, see [`LICENSE`](LICENSE)
