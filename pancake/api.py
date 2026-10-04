import time

from fastapi import APIRouter

from pancake.schemas import ScoreIn, Survey
from pancake.storage import JsonStore


def create_router(store: JsonStore) -> APIRouter:
    router = APIRouter()

    @router.post("/score")
    def post_score(s: ScoreIn):
        """게임 종료 점수 기록 -> 역대 최고 점수 반환"""
        rows = store.append_score({"ts": time.time(), "score": int(s.score)})
        best = max(r["score"] for r in rows)
        return {"ok": True, "best": best, "count": len(rows)}

    @router.get("/best")
    def get_best():
        rows = store.load_scores()
        return {"best": max([r["score"] for r in rows], default=0), "count": len(rows)}

    @router.get("/health")
    def health():
        return {"ok": True, "responses": len(store.load_responses())}

    @router.post("/responses")
    def post_responses(survey: Survey):
        # Keep legacy truncation and the HTTP 200 error response for Unity clients.
        n = min(len(survey.claims), len(survey.agrees))
        if n == 0:
            return {"ok": False, "error": "empty"}
        row = {"ts": time.time(), "claims": survey.claims[:n], "agrees": survey.agrees[:n]}
        rows = store.append_response(row)
        return {"ok": True, "total": len(rows)}

    @router.get("/residents")
    def residents(n: int = 100):
        rows = store.load_responses()[-max(1, min(n, 1000)):]
        out = [{"claims": r["claims"], "agrees": r["agrees"]} for r in reversed(rows)]
        return {"count": len(out), "residents": out}

    return router
