# PancakE 설문 서버
# 실행:  pip install fastapi uvicorn   ->   python -m uvicorn pancake_server:app --host 0.0.0.0 --port 8000
# 게임 종료 후 플레이어의 설문 응답을 저장하고,
# 다음 판 시작 시 최근 응답자들을 '주민 데이터'로 돌려준다. (데이터 순환 구조)

import json
import os
import threading
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses.json")
_lock = threading.Lock()

app = FastAPI(title="PancakE Survey Server", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


class Survey(BaseModel):
    claims: list[str]
    agrees: list[bool]


def _load() -> list:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(rows: list) -> None:
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")

class ScoreIn(BaseModel):
    score: int

def _load_scores():
    if not os.path.exists(SCORE_FILE):
        return []
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_scores(rows):
    tmp = SCORE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    os.replace(tmp, SCORE_FILE)

@app.post("/score")
def post_score(s: ScoreIn):
    """게임 종료 점수 기록 -> 역대 최고 점수 반환"""
    with _lock:
        rows = _load_scores()
        rows.append({"ts": time.time(), "score": int(s.score)})
        _save_scores(rows)
    best = max(r["score"] for r in rows)
    return {"ok": True, "best": best, "count": len(rows)}

@app.get("/best")
def get_best():
    rows = _load_scores()
    return {"best": max([r["score"] for r in rows], default=0), "count": len(rows)}

@app.get("/health")
def health():
    return {"ok": True, "responses": len(_load())}


@app.post("/responses")
def post_responses(survey: Survey):
    # 한 번의 제출 = 응답자(주민) 한 명
    n = min(len(survey.claims), len(survey.agrees))
    if n == 0:
        return {"ok": False, "error": "empty"}
    row = {
        "ts": time.time(),
        "claims": survey.claims[:n],
        "agrees": survey.agrees[:n],
    }
    with _lock:
        rows = _load()
        rows.append(row)
        _save(rows)
    return {"ok": True, "total": len(rows)}


@app.get("/residents")
def residents(n: int = 100):
    # 최근 응답자 n명 (게임의 '주민' 데이터)
    rows = _load()[-max(1, min(n, 1000)):]
    out = [{"claims": r["claims"], "agrees": r["agrees"]} for r in reversed(rows)]
    return {"count": len(out), "residents": out}
