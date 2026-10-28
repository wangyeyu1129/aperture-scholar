import httpx
import pytest

from aperture_scholar.config import ScholarSettings
from aperture_scholar.domain.errors import ProviderError
from aperture_scholar.infrastructure.semantic_scholar import SemanticScholarSource
from aperture_scholar.infrastructure.sqlite import SQLiteDatabase, SQLiteResponseCache


@pytest.fixture
def cache(tmp_path):
    database = SQLiteDatabase(tmp_path / "cache.sqlite3")
    database.initialize()
    return SQLiteResponseCache(database)


def test_search_maps_nullable_fields_and_caches(cache):
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["x-api-key"] == "test-only-key"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "paperId": "p1",
                        "title": "Paper",
                        "abstract": None,
                        "year": None,
                        "externalIds": None,
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        source = SemanticScholarSource(
            client, cache, ScholarSettings(api_key="test-only-key"), sleep=lambda _: None
        )
        assert source.search("query", 10)[0].abstract == ""
        assert source.search("query", 10)[0].id == "p1"
        assert len(calls) == 1


def test_rate_limit_retries_then_succeeds(cache):
    calls, delays = [], []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "2"})
            if len(calls) == 1
            else httpx.Response(200, json={"data": []})
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        source = SemanticScholarSource(client, cache, ScholarSettings(), sleep=delays.append)
        assert source.search("query", 10) == []
        assert len(calls) == 2
        assert 2 in delays


@pytest.mark.parametrize("status,expected_calls", [(401, 1), (429, 3), (503, 3)])
def test_http_failures_are_bounded(cache, status, expected_calls):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        source = SemanticScholarSource(client, cache, ScholarSettings(), sleep=lambda _: None)
        with pytest.raises(ProviderError):
            source.search("query", 10)
    assert len(calls) == expected_calls


def test_transport_failure_is_bounded(cache):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectError("synthetic outage")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        source = SemanticScholarSource(client, cache, ScholarSettings(), sleep=lambda _: None)
        with pytest.raises(ProviderError):
            source.search("query", 10)
    assert len(calls) == 3


@pytest.mark.parametrize("payload", ["not-json", '{"data": null}', '{"data": [{"title":"no id"}]}'])
def test_malformed_response_not_cached(cache, payload):
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=payload))
    ) as client:
        source = SemanticScholarSource(client, cache, ScholarSettings(), sleep=lambda _: None)
        with pytest.raises(ProviderError):
            source.search("query", 10)


def test_bad_query_rejected_before_network(cache):
    with httpx.Client() as client:
        source = SemanticScholarSource(client, cache, ScholarSettings())
        with pytest.raises(ValueError):
            source.search("", 10)
