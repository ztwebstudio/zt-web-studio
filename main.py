
"""
ZT Web Studio Cloud Build API
Queues build requests only; does not generate APKs.

Production requirements:
- Persistent job queue/database
- Authenticated user identity and authorization
- Distributed rate limiting
- Isolated Android build runner with Android SDK, JDK and Gradle
- Build artifact storage and secure download URLs

Never execute untrusted project code in this API process.
"""

import os
import re
import time
import uuid
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI(
    title="ZT Web Studio Cloud Build API",
    version="0.2.0",
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

PACKAGE_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_]*"
    r"(\.[A-Za-z][A-Za-z0-9_]*)+"
)

ALLOWED_PROJECT_TYPES = {"android-template"}
ALLOWED_TEMPLATES = {"basic-activity"}

MAX_JOBS = 1000

class BuildRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    appName: str = Field(min_length=1, max_length=50)
    packageName: str = Field(min_length=3, max_length=180)
    projectType: str = Field(
        default="android-template",
        min_length=1,
        max_length=40,
    )
    template: str = Field(
        default="basic-activity",
        min_length=1,
        max_length=50,
    )

JOBS = {}
JOBS_LOCK = Lock()


@app.get("/")
def health():
    return {
        "name": "ZT Web Studio Cloud Build API",
        "status": "ok",
        "buildRunner": "not-configured",
        "apkGenerationAvailable": False,
    }


@app.post("/api/build", status_code=202)
def create_build(body: BuildRequest):
    if not body.appName.strip():
        raise HTTPException(
            status_code=400,
            detail="App name cannot be blank",
        )

    if not PACKAGE_PATTERN.fullmatch(body.packageName):
        raise HTTPException(
            status_code=400,
            detail="Invalid Android application ID",
        )

    if body.projectType not in ALLOWED_PROJECT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported project type",
        )

    if body.template not in ALLOWED_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported template",
        )

    job_id = str(uuid.uuid4())

    job = {
        "jobId": job_id,
        "status": "queued",
        "appName": body.appName,
        "packageName": body.packageName,
        "projectType": body.projectType,
        "template": body.template,
        "createdAt": int(time.time()),
        "message": (
            "Queued only. An isolated build runner "
            "must be configured to generate an APK."
        ),
    }

    with JOBS_LOCK:
        if len(JOBS) >= MAX_JOBS:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Job queue capacity reached. "
                    "Try again later."
                ),
            )

        JOBS[job_id] = job

    return {
        "jobId": job_id,
        "status": "queued",
        "message": job["message"],
    }


@app.get("/api/build/{job_id}")
def get_build(job_id: str):
    try:
        parsed_id = uuid.UUID(job_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID",
        )

    canonical_id = str(parsed_id)

    with JOBS_LOCK:
        job = JOBS.get(canonical_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Unknown job ID",
            )

        return dict(job)
