"""Public exams and edital endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query
from modules.public_exams import ExamNotice

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.public_exams import (
    PublicExamAnalyzeRequest,
    PublicExamAnalyzeResponse,
    PublicExamConfirmRequest,
    PublicExamConfirmResponse,
    PublicExamImportRequest,
    PublicExamImportResponse,
    PublicExamListResponse,
    PublicExamStudyPlanRequest,
    PublicExamStudyPlanResponse,
)
from apps.api.services.public_exams import (
    public_exams_analyze,
    public_exams_confirm,
    public_exams_delete,
    public_exams_get,
    public_exams_import,
    public_exams_list,
    public_exams_study_plan,
)

router = APIRouter(prefix="/api/v1/public-exams", tags=["public-exams"])


@router.post("/import", response_model=ApiEnvelope[PublicExamImportResponse])
def import_public_exam(payload: PublicExamImportRequest) -> ApiEnvelope[PublicExamImportResponse]:
    """Extract a review-only edital draft from pasted text."""
    data, warnings = public_exams_import(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.get("", response_model=ApiEnvelope[PublicExamListResponse])
def list_public_exams(
    query: str = Query(default="", max_length=240),
) -> ApiEnvelope[PublicExamListResponse]:
    """List saved public exam notices."""
    return ok(public_exams_list(query))


@router.get("/{notice_id}", response_model=ApiEnvelope[ExamNotice])
def get_public_exam(notice_id: str) -> ApiEnvelope[ExamNotice]:
    """Return one saved public exam notice."""
    return ok(public_exams_get(notice_id))


@router.delete("/{notice_id}", response_model=ApiEnvelope[PublicExamListResponse])
def delete_public_exam(notice_id: str) -> ApiEnvelope[PublicExamListResponse]:
    """Delete one saved notice."""
    return ok(public_exams_delete(notice_id))


@router.post("/{notice_id}/confirm", response_model=ApiEnvelope[PublicExamConfirmResponse])
def confirm_public_exam(
    notice_id: str,
    payload: PublicExamConfirmRequest,
) -> ApiEnvelope[PublicExamConfirmResponse]:
    """Persist a reviewed notice locally."""
    return ok(public_exams_confirm(notice_id, payload), request_id=payload.request_id)


@router.post("/{notice_id}/analyze", response_model=ApiEnvelope[PublicExamAnalyzeResponse])
def analyze_public_exam(
    notice_id: str,
    payload: PublicExamAnalyzeRequest,
) -> ApiEnvelope[PublicExamAnalyzeResponse]:
    """Compare one saved notice/role with the Universal Career Profile."""
    return ok(public_exams_analyze(notice_id, payload), request_id=payload.request_id)


@router.post("/{notice_id}/study-plan", response_model=ApiEnvelope[PublicExamStudyPlanResponse])
def study_plan_public_exam(
    notice_id: str,
    payload: PublicExamStudyPlanRequest,
) -> ApiEnvelope[PublicExamStudyPlanResponse]:
    """Generate a simple initial study plan."""
    return ok(public_exams_study_plan(notice_id, payload), request_id=payload.request_id)
