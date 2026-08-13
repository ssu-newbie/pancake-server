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
