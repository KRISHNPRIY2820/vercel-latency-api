from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data.json"
)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

def process_request(body: RequestBody):

    results = []

    for region in body.regions:

        rows = [row for row in DATA if row["region"] == region]

        if not rows:
            continue

        latencies = [row["latency_ms"] for row in rows]
        uptimes = [row["uptime_pct"] for row in rows]

        results.append({
            "region": region,
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": sum(
                1 for latency in latencies
                if latency > body.threshold_ms
            )
        })

    return {"regions": results}

@app.post("/analytics")
async def analytics(body: RequestBody):
    return process_request(body)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Latency analytics service is running"
    }