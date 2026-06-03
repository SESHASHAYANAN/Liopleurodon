"""
Liopleurodon — Greenhouse Apply Provider
Submits applications via the Greenhouse Job Board API.

API Reference: https://developers.greenhouse.io/job-board.html
Endpoint: POST https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{id}
Auth: HTTP Basic Auth with Job Board API key
Format: multipart/form-data
"""

import httpx
import base64
from typing import Optional
from config import get_settings
from services.direct_apply.base import (
    BaseApplyProvider, CandidateProfile, ApplyResult, FormField,
    extract_greenhouse_ids, resolve_apply_url,
)


class GreenhouseProvider(BaseApplyProvider):
    """Greenhouse Job Board API integration for direct apply."""

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def get_provider_name(self) -> str:
        return "Greenhouse"

    async def _resolve_ids(self, apply_url: str) -> tuple:
        """Extract Greenhouse IDs, resolving redirect URLs if needed."""
        ids = extract_greenhouse_ids(apply_url or "")
        if ids:
            return ids
        if apply_url:
            resolved = await resolve_apply_url(apply_url)
            ids = extract_greenhouse_ids(resolved)
            if ids:
                return ids
        return None

    async def get_application_form(self, job: dict) -> list[FormField]:
        """
        Fetch the application form fields for a Greenhouse job.
        The Job Board API returns questions/fields for each job posting.
        """
        ids = await self._resolve_ids(job.get("apply_url", ""))
        if not ids:
            return self._default_fields()

        board_token, job_id = ids
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/{board_token}/jobs/{job_id}",
                    params={"questions": "true"},
                )
                if resp.status_code != 200:
                    return self._default_fields()

                data = resp.json()
                fields = self._default_fields()

                # Parse Greenhouse custom questions
                for q in data.get("questions", []):
                    field_type = "text"
                    options = []
                    if q.get("fields"):
                        f = q["fields"][0]
                        ftype = f.get("type", "input_text")
                        if ftype in ("input_text", "input_hidden"):
                            field_type = "text"
                        elif ftype == "textarea":
                            field_type = "textarea"
                        elif ftype == "multi_value_single_select":
                            field_type = "select"
                            options = [v.get("label", "") for v in f.get("values", [])]
                        elif ftype == "multi_value_multi_select":
                            field_type = "checkbox"
                            options = [v.get("label", "") for v in f.get("values", [])]
                        elif ftype == "input_file":
                            field_type = "file"

                    fields.append(FormField(
                        name=f"question_{q.get('id', '')}",
                        label=q.get("label", "Question"),
                        field_type=field_type,
                        required=q.get("required", False),
                        options=options,
                        description=q.get("description", ""),
                    ))

                return fields
        except Exception as e:
            print(f"[Greenhouse] Form fetch error: {e}")
            return self._default_fields()

    async def submit_application(
        self,
        candidate: CandidateProfile,
        job: dict,
        resume_bytes: Optional[bytes] = None,
    ) -> ApplyResult:
        """
        Submit a candidate application to Greenhouse via Job Board API.
        Uses multipart/form-data with Basic Auth.
        """
        settings = get_settings()
        api_key = settings.GREENHOUSE_JOB_BOARD_API_KEY
        steps = []

        # Step 1: Parse ATS identifiers from URL (resolve redirects if needed)
        ids = await self._resolve_ids(job.get("apply_url", ""))

        steps.append({
            "step": "url_parsed",
            "label": "Job URL Analyzed",
            "detail": f"Board: {ids[0]}, Job ID: {ids[1]}" if ids else "ATS: Greenhouse (redirect URL detected)",
            "status": "completed",
        })

        # Step 2: Map candidate profile to Greenhouse schema
        form_data = {
            "first_name": candidate.full_name.split(" ")[0] if candidate.full_name else "",
            "last_name": " ".join(candidate.full_name.split(" ")[1:]) if " " in candidate.full_name else candidate.full_name,
            "email": candidate.email,
        }
        if candidate.phone:
            form_data["phone"] = candidate.phone
        if candidate.linkedin_url:
            form_data["social_url_0"] = candidate.linkedin_url
        if candidate.portfolio_url:
            form_data["social_url_1"] = candidate.portfolio_url
        if candidate.location:
            form_data["location"] = candidate.location

        steps.append({
            "step": "profile_mapped",
            "label": "Profile Mapped to ATS Schema",
            "detail": f"Name: {candidate.full_name}, Email: {candidate.email}",
            "status": "completed",
        })

        # Step 3: Prepare resume attachment
        files = {}
        if resume_bytes and candidate.resume_filename:
            files["resume"] = (candidate.resume_filename, resume_bytes, "application/pdf")
            steps.append({
                "step": "resume_attached",
                "label": "Resume Uploaded",
                "detail": candidate.resume_filename,
                "status": "completed",
            })

        # Step 4: Add cover letter if provided
        if candidate.cover_letter:
            form_data["cover_letter"] = candidate.cover_letter
            steps.append({
                "step": "cover_letter_attached",
                "label": "Cover Letter Attached",
                "status": "completed",
            })

        # Step 5: Add custom question answers
        for key, value in candidate.custom_answers.items():
            form_data[key] = value
        if candidate.custom_answers:
            steps.append({
                "step": "questions_answered",
                "label": "Custom Questions Mapped",
                "detail": f"{len(candidate.custom_answers)} answers",
                "status": "completed",
            })

        # Step 6: Submit to Greenhouse
        steps.append({
            "step": "submitting",
            "label": "Submitting Application",
            "detail": "Sending to Greenhouse Job Board API..." if ids else "Recording application...",
            "status": "in_progress",
        })

        # If we couldn't extract IDs, fail instead of recording locally
        if not ids:
            steps[-1]["status"] = "error"
            steps[-1]["detail"] = "Could not extract Greenhouse board token and job ID from URL"
            return ApplyResult(
                success=False,
                provider="Greenhouse",
                message="Cannot submit: Missing job identifiers.",
                error_code="INVALID_URL",
                steps_completed=steps,
            )

        board_token, job_id = ids
        url = f"{self.BASE_URL}/{board_token}/jobs/{job_id}"

        # Auth: Basic auth with API key as username, empty password
        auth_header = ""
        if api_key:
            encoded = base64.b64encode(f"{api_key}:".encode()).decode()
            auth_header = f"Basic {encoded}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {}
                if auth_header:
                    headers["Authorization"] = auth_header

                # Retry logic with exponential backoff + jitter + Retry-After
                last_error = None
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        resp = await client.post(
                            url,
                            data=form_data,
                            files=files if files else None,
                            headers=headers,
                        )

                        if resp.status_code in (200, 201):
                            response_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                            steps[-1]["status"] = "completed"
                            steps[-1]["detail"] = "Application submitted successfully!"

                            steps.append({
                                "step": "confirmed",
                                "label": "Application Confirmed",
                                "detail": f"Candidate ID: {response_data.get('id', 'N/A')}",
                                "status": "completed",
                            })

                            return ApplyResult(
                                success=True,
                                provider="Greenhouse",
                                message="Application submitted successfully to Greenhouse!",
                                candidate_id=str(response_data.get("id", "")),
                                application_id=str(response_data.get("application_id", "")),
                                ats_response=response_data,
                                steps_completed=steps,
                            )

                        elif resp.status_code == 422:
                            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                            steps[-1]["status"] = "error"
                            steps[-1]["detail"] = f"Validation error: {error_data}"

                            return ApplyResult(
                                success=False,
                                provider="Greenhouse",
                                message=f"Application validation failed: {error_data}",
                                error_code="VALIDATION_ERROR",
                                ats_response=error_data,
                                steps_completed=steps,
                            )

                        elif resp.status_code == 429:
                            import asyncio, random
                            if attempt < max_retries - 1:
                                retry_after = resp.headers.get("Retry-After")
                                if retry_after:
                                    try:
                                        wait = float(retry_after) + random.uniform(0.5, 1.5)
                                    except ValueError:
                                        wait = (2 ** attempt) + random.uniform(1.0, 3.0)
                                else:
                                    wait = (2 ** attempt) + random.uniform(0.5, 2.0)
                                print(f"[Greenhouse] 429 rate limited, attempt {attempt+1}/{max_retries}, waiting {wait:.1f}s")
                                steps[-1]["detail"] = f"Rate limited — retrying in {wait:.0f}s (attempt {attempt+1})"
                                await asyncio.sleep(wait)
                                continue
                            steps[-1]["status"] = "error"
                            steps[-1]["detail"] = f"Rate limited by Greenhouse after {max_retries} attempts"
                            return ApplyResult(
                                success=False,
                                provider="Greenhouse",
                                message="Rate limited by Greenhouse. Please try again later.",
                                error_code="RATE_LIMITED",
                                steps_completed=steps,
                            )

                        else:
                            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                            if attempt < max_retries - 1:
                                import asyncio, random
                                wait = (2 ** attempt) + random.uniform(0.5, 2.0)
                                print(f"[Greenhouse] HTTP {resp.status_code}, retrying in {wait:.1f}s (attempt {attempt+1})")
                                await asyncio.sleep(wait)
                                continue

                    except httpx.TimeoutException:
                        last_error = "Request timed out"
                        if attempt < max_retries - 1:
                            import asyncio, random
                            wait = (2 ** attempt) + random.uniform(0.5, 2.0)
                            await asyncio.sleep(wait)
                            continue

                steps[-1]["status"] = "error"
                steps[-1]["detail"] = last_error or "Unknown error"

                return ApplyResult(
                    success=False,
                    provider="Greenhouse",
                    message=f"Failed to submit: {last_error}",
                    error_code="SUBMISSION_FAILED",
                    steps_completed=steps,
                )

        except Exception as e:
            steps[-1]["status"] = "error"
            steps[-1]["detail"] = str(e)
            return ApplyResult(
                success=False,
                provider="Greenhouse",
                message=f"Submission error: {str(e)}",
                error_code="NETWORK_ERROR",
                steps_completed=steps,
            )

    def _default_fields(self) -> list[FormField]:
        """Default fields common to all Greenhouse applications."""
        return [
            FormField(
                name="first_name", label="First Name", field_type="text",
                required=True, auto_fillable=True,
            ),
            FormField(
                name="last_name", label="Last Name", field_type="text",
                required=True, auto_fillable=True,
            ),
            FormField(
                name="email", label="Email", field_type="email",
                required=True, auto_fillable=True,
            ),
            FormField(
                name="phone", label="Phone", field_type="phone",
                required=False, auto_fillable=True,
            ),
            FormField(
                name="resume", label="Resume / CV", field_type="file",
                required=True, auto_fillable=True,
                description="PDF or DOCX, max 5MB",
            ),
            FormField(
                name="cover_letter", label="Cover Letter", field_type="textarea",
                required=False, auto_fillable=True,
            ),
            FormField(
                name="linkedin_url", label="LinkedIn Profile", field_type="text",
                required=False, auto_fillable=True,
            ),
            FormField(
                name="portfolio_url", label="Portfolio / GitHub", field_type="text",
                required=False, auto_fillable=True,
            ),
        ]
