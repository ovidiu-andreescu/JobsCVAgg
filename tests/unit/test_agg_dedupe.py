import pytest
from job_aggregator.models import Job, Query
from job_aggregator.dedupe import dedupe, signature

def make(url, title="Eng", company="Acme"):
    return Job(source="x", source_job_id=url, title=title, company=company, location=None,
               remote=None, url=url, description=None)

def test_dedupe_by_url():
    a = make("https://x.com/job/1?ref=a")
    b = make("https://x.com/job/1")
    c = make("https://x.com/job/2")
    out = dedupe([a,b,c])
    assert len(out) == 2

def test_signature_stable():
    j = make("https://a/b", title="Engineer", company="ACME")
    assert signature(j) == ("https://a/b", "engineer", "acme")

@pytest.mark.asyncio
async def test_aggregate_uses_all_sources(monkeypatch):
    from job_aggregator import aggregate
    from job_aggregator.models import Job, Query

    def make(url, title="Eng", company="Acme"):
        return Job(source="x", source_job_id=url, title=title, company=company,
                   location=None, remote=None, url=url, description=None)

    class P1:
        name = "p1"
        async def search(self, q): return [make("https://a/1")]
        def enabled(self): return True

    class P2:
        name = "p2"
        async def search(self, q): return [make("https://a/1"), make("https://a/2")]
        def enabled(self): return True

    monkeypatch.setattr(aggregate, "available_providers", lambda: [P1(), P2()])

    out = await aggregate.run(Query(q="python"))
    assert {str(j.url) for j in out} == {"https://a/1", "https://a/2"}
