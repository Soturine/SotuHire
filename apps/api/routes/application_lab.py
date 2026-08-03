"""Guided Application Lab and Resume Studio endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from modules.application_lab.models import (
    ApplicationActionPlan,
    ApplicationSuggestion,
    ResumeVariant,
)

from apps.api.routes.responses import ok
from apps.api.schemas.application_lab import (
    ActionPlanCreateRequest,
    ApplicationKitResponse,
    ApplicationLabAnalyzeResponse,
    ApplicationLabSessionCreateRequest,
    ApplicationLabSessionDetail,
    ApplicationLabSessionPage,
    ApplicationLabSessionUpdateRequest,
    MasterResumeResponse,
    MasterResumeUpsertRequest,
    RequestMetadata,
    ResumeExportRequest,
    ResumeExportResponse,
    ResumeIngestionRequest,
    ResumeIngestionResponse,
    ResumeTemplatesResponse,
    ResumeVariantCreateRequest,
    ResumeVariantPage,
    ResumeVariantResponse,
    ResumeVariantUpdateRequest,
    SuggestionEditRequest,
    TrackerSaveRequest,
    TrackerSaveResponse,
    VariantFromSessionRequest,
)
from apps.api.schemas.common import ApiEnvelope
from apps.api.services.application_lab import (
    ApplicationLabApiService,
    get_application_lab_api_service,
)

application_lab_router = APIRouter(prefix="/api/v1/application-lab", tags=["application-lab"])
resume_studio_router = APIRouter(prefix="/api/v1/resume-studio", tags=["resume-studio"])
LabDependency = Annotated[ApplicationLabApiService, Depends(get_application_lab_api_service)]


@application_lab_router.post("/sessions", response_model=ApiEnvelope[ApplicationLabSessionDetail])
def create_session(
    payload: ApplicationLabSessionCreateRequest, service: LabDependency
) -> ApiEnvelope[ApplicationLabSessionDetail]:
    return ok(service.create_session(payload), request_id=payload.request_id)


@application_lab_router.get("/sessions", response_model=ApiEnvelope[ApplicationLabSessionPage])
def list_sessions(
    service: LabDependency,
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ApiEnvelope[ApplicationLabSessionPage]:
    return ok(service.list_sessions(limit=limit, offset=offset))


@application_lab_router.get(
    "/sessions/{session_id}", response_model=ApiEnvelope[ApplicationLabSessionDetail]
)
def get_session(
    session_id: str, service: LabDependency
) -> ApiEnvelope[ApplicationLabSessionDetail]:
    return ok(service.detail(session_id))


@application_lab_router.patch(
    "/sessions/{session_id}", response_model=ApiEnvelope[ApplicationLabSessionDetail]
)
def update_session(
    session_id: str,
    payload: ApplicationLabSessionUpdateRequest,
    service: LabDependency,
) -> ApiEnvelope[ApplicationLabSessionDetail]:
    changes = payload.model_dump(exclude={"request_id"}, exclude_unset=True)
    return ok(service.update_session(session_id, changes), request_id=payload.request_id)


@application_lab_router.post(
    "/sessions/{session_id}/cancel", response_model=ApiEnvelope[ApplicationLabSessionDetail]
)
def cancel_session(
    session_id: str, payload: RequestMetadata, service: LabDependency
) -> ApiEnvelope[ApplicationLabSessionDetail]:
    return ok(service.cancel_session(session_id), request_id=payload.request_id)


@application_lab_router.post(
    "/sessions/{session_id}/analyze", response_model=ApiEnvelope[ApplicationLabAnalyzeResponse]
)
def analyze_session(
    session_id: str, payload: RequestMetadata, service: LabDependency
) -> ApiEnvelope[ApplicationLabAnalyzeResponse]:
    return ok(service.analyze(session_id), request_id=payload.request_id)


def _review(
    session_id: str,
    suggestion_id: str,
    action: str,
    service: ApplicationLabApiService,
    *,
    edited_value: str = "",
) -> ApplicationSuggestion:
    return service._call(
        service.domain.review_suggestion,
        session_id,
        suggestion_id,
        action,
        edited_value=edited_value,
    )


@application_lab_router.post(
    "/sessions/{session_id}/suggestions/{suggestion_id}/accept",
    response_model=ApiEnvelope[ApplicationSuggestion],
)
def accept_suggestion(
    session_id: str,
    suggestion_id: str,
    payload: RequestMetadata,
    service: LabDependency,
) -> ApiEnvelope[ApplicationSuggestion]:
    return ok(
        _review(session_id, suggestion_id, "accepted", service),
        request_id=payload.request_id,
    )


@application_lab_router.post(
    "/sessions/{session_id}/suggestions/{suggestion_id}/edit",
    response_model=ApiEnvelope[ApplicationSuggestion],
)
def edit_suggestion(
    session_id: str,
    suggestion_id: str,
    payload: SuggestionEditRequest,
    service: LabDependency,
) -> ApiEnvelope[ApplicationSuggestion]:
    return ok(
        _review(
            session_id,
            suggestion_id,
            "edited",
            service,
            edited_value=payload.edited_value,
        ),
        request_id=payload.request_id,
    )


@application_lab_router.post(
    "/sessions/{session_id}/suggestions/{suggestion_id}/reject",
    response_model=ApiEnvelope[ApplicationSuggestion],
)
def reject_suggestion(
    session_id: str,
    suggestion_id: str,
    payload: RequestMetadata,
    service: LabDependency,
) -> ApiEnvelope[ApplicationSuggestion]:
    return ok(
        _review(session_id, suggestion_id, "rejected", service),
        request_id=payload.request_id,
    )


@application_lab_router.post(
    "/sessions/{session_id}/suggestions/{suggestion_id}/undo",
    response_model=ApiEnvelope[ApplicationSuggestion],
)
def undo_suggestion(
    session_id: str,
    suggestion_id: str,
    payload: RequestMetadata,
    service: LabDependency,
) -> ApiEnvelope[ApplicationSuggestion]:
    return ok(
        _review(session_id, suggestion_id, "pending", service),
        request_id=payload.request_id,
    )


@application_lab_router.post(
    "/sessions/{session_id}/variant", response_model=ApiEnvelope[ResumeVariant]
)
def create_session_variant(
    session_id: str, payload: VariantFromSessionRequest, service: LabDependency
) -> ApiEnvelope[ResumeVariant]:
    variant = service._call(service.domain.create_variant, session_id, title=payload.title)
    return ok(variant, request_id=payload.request_id)


@application_lab_router.post(
    "/sessions/{session_id}/kit", response_model=ApiEnvelope[ApplicationKitResponse]
)
def create_session_kit(
    session_id: str, payload: RequestMetadata, service: LabDependency
) -> ApiEnvelope[ApplicationKitResponse]:
    kit, snapshot = service._call(service.domain.create_kit, session_id)
    return ok(
        ApplicationKitResponse(kit=kit, snapshot_id=snapshot.snapshot_id),
        request_id=payload.request_id,
    )


@application_lab_router.post(
    "/sessions/{session_id}/action-plan", response_model=ApiEnvelope[ApplicationActionPlan]
)
def create_session_action_plan(
    session_id: str, payload: ActionPlanCreateRequest, service: LabDependency
) -> ApiEnvelope[ApplicationActionPlan]:
    plan = service._call(
        service.domain.create_action_plan,
        session_id,
        period_days=payload.period_days,
    )
    return ok(plan, request_id=payload.request_id)


@application_lab_router.post(
    "/sessions/{session_id}/tracker", response_model=ApiEnvelope[TrackerSaveResponse]
)
def save_session_tracker(
    session_id: str, payload: TrackerSaveRequest, service: LabDependency
) -> ApiEnvelope[TrackerSaveResponse]:
    tracker_id = service._call(
        service.domain.save_to_tracker,
        session_id,
        privacy_acknowledged=payload.privacy_acknowledged,
        source_capture_id=payload.source_capture_id,
    )
    detail = service.detail(session_id)
    return ok(
        TrackerSaveResponse(
            tracker_application_id=tracker_id,
            session=detail.session,
        ),
        request_id=payload.request_id,
    )


@resume_studio_router.get("/master", response_model=ApiEnvelope[MasterResumeResponse])
def get_master_resume(service: LabDependency) -> ApiEnvelope[MasterResumeResponse]:
    return ok(service.master())


@resume_studio_router.post("/ingest", response_model=ApiEnvelope[ResumeIngestionResponse])
def ingest_resume(
    payload: ResumeIngestionRequest,
    service: LabDependency,
) -> ApiEnvelope[ResumeIngestionResponse]:
    return ok(
        service.ingest_resume(payload.file_name, payload.content_base64),
        request_id=payload.request_id,
    )


@resume_studio_router.put("/master", response_model=ApiEnvelope[MasterResumeResponse])
def put_master_resume(
    payload: MasterResumeUpsertRequest, service: LabDependency
) -> ApiEnvelope[MasterResumeResponse]:
    return ok(service.save_master(payload.resume), request_id=payload.request_id)


@resume_studio_router.get("/variants", response_model=ApiEnvelope[ResumeVariantPage])
def list_resume_variants(
    service: LabDependency,
    master_resume_id: str = "",
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ApiEnvelope[ResumeVariantPage]:
    return ok(
        service.variants(
            master_resume_id=master_resume_id,
            limit=limit,
            offset=offset,
        )
    )


@resume_studio_router.post("/variants", response_model=ApiEnvelope[ResumeVariantResponse])
def create_resume_variant(
    payload: ResumeVariantCreateRequest, service: LabDependency
) -> ApiEnvelope[ResumeVariantResponse]:
    return ok(service.save_variant(payload.variant), request_id=payload.request_id)


@resume_studio_router.get(
    "/variants/{variant_id}", response_model=ApiEnvelope[ResumeVariantResponse]
)
def get_resume_variant(
    variant_id: str, service: LabDependency
) -> ApiEnvelope[ResumeVariantResponse]:
    return ok(service.variant(variant_id))


@resume_studio_router.patch(
    "/variants/{variant_id}", response_model=ApiEnvelope[ResumeVariantResponse]
)
def update_resume_variant(
    variant_id: str,
    payload: ResumeVariantUpdateRequest,
    service: LabDependency,
) -> ApiEnvelope[ResumeVariantResponse]:
    changes = payload.model_dump(exclude={"request_id"}, exclude_unset=True)
    return ok(
        service.update_variant(variant_id, changes),
        request_id=payload.request_id,
    )


@resume_studio_router.get("/templates", response_model=ApiEnvelope[ResumeTemplatesResponse])
def list_resume_templates(service: LabDependency) -> ApiEnvelope[ResumeTemplatesResponse]:
    return ok(service.templates())


@resume_studio_router.post(
    "/variants/{variant_id}/export", response_model=ApiEnvelope[ResumeExportResponse]
)
def export_resume_variant(
    variant_id: str, payload: ResumeExportRequest, service: LabDependency
) -> ApiEnvelope[ResumeExportResponse]:
    return ok(
        service.export_variant(
            variant_id,
            export_format=payload.format,
            template_id=payload.template_id,
            page_size=payload.page_size,
        ),
        request_id=payload.request_id,
    )


__all__ = ["application_lab_router", "resume_studio_router"]
