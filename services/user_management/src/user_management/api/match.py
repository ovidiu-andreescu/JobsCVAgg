from fastapi import APIRouter, Depends, HTTPException, Query

from user_management.auth_deps import CurrentUser, get_current_user
from user_management.matcher.storage import get_cv_keywords_from_s3, get_all_jobs_for_scoring
from user_management.matcher.scoring import score_and_rank_jobs

router = APIRouter(prefix="/match", tags=["match"])

@router.get("/me")
def match_me(
        user: CurrentUser = Depends(get_current_user),
        limit: int = Query(50, ge=1, le=200)
):
    email = str(user.email).strip().lower()
    cv_keywords = get_cv_keywords_from_s3(email)
    if not cv_keywords:
        raise HTTPException(status_code=404, detail="No CV keywords found")

    jobs = get_all_jobs_for_scoring()
    ranked = score_and_rank_jobs(cv_keywords, jobs)
    return [j.model(mode="json") for j in ranked[:limit]]


