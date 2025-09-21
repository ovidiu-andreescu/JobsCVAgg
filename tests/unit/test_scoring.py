import pytest
from job-matcher.scoring import calculate_jaccard_score, score_and_rank_jobs
from job-matcher.models import JobForScoring

def test_jaccard_score_perfect_match():
    cv_keywords = {"python", "api", "aws"}
    job_keywords = {"python", "api", "aws"}
    assert calculate_jaccard_score(cv_keywords, job_keywords) == 1.0


def test_jaccard_score_partial_match():
    cv_keywords = {"python", "api", "aws", "fastapi"}
    job_keywords = {"python", "aws", "docker", "terraform"}
    assert calculate_jaccard_score(cv_keywords, job_keywords) == pytest.approx(0.333, 0.001)


def test_jaccard_score_no_match():
    cv_keywords = {"python", "api"}
    job_keywords = {"java", "spring"}
    assert calculate_jaccard_score(cv_keywords, job_keywords) == 0.0


def test_jaccard_score_empty_sets():
    cv_keywords = {"python", "api"}
    assert calculate_jaccard_score(cv_keywords, set()) == 0.0
    assert calculate_jaccard_score(set(), cv_keywords) == 0.0
    assert calculate_jaccard_score(set(), set()) == 0.0



@pytest.fixture
def sample_jobs():
    return [
        JobForScoring(source="test", source_job_id="1", title="Perfect Match", url="http://test.com/1",
                      keywords={"python", "api", "aws"}),
        JobForScoring(source="test", source_job_id="2", title="Partial Match", url="http://test.com/2",
                      keywords={"python", "docker"}),
        JobForScoring(source="test", source_job_id="3", title="No Match", url="http://test.com/3",
                      keywords={"java", "spring"}),
        JobForScoring(source="test", source_job_id="4", title="Another Partial", url="http://test.com/4",
                      keywords={"aws", "terraform"}),
    ]


def test_score_and_rank_jobs(sample_jobs):
    cv_keywords = {"python", "api", "aws"}

    ranked_jobs = score_and_rank_jobs(cv_keywords, sample_jobs)

    assert len(ranked_jobs) == 3

    assert ranked_jobs[0].title == "Perfect Match"
    assert ranked_jobs[0].score == 1.0

    assert ranked_jobs[1].score == pytest.approx(0.25)
    assert ranked_jobs[2].score == pytest.approx(0.25)


def test_score_and_rank_no_matching_jobs(sample_jobs):
    cv_keywords = {"golang", "kubernetes"}

    ranked_jobs = score_and_rank_jobs(cv_keywords, sample_jobs)

    assert len(ranked_jobs) == 0
