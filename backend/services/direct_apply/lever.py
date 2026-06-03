"""
Liopleurodon — Lever Apply Provider
Submits applications via the Lever Postings API.

API Reference: https://github.com/lever/postings-api/blob/master/README.md
Endpoint: POST https://api.lever.co/v0/postings/{company}/{id}/apply
Auth: API Key
Format: multipart/form-data or application/json
"""

import httpx
from typing import Optional
from config import get_settings
from services.direct_apply.base import (
    BaseApplyProvider, CandidateProfile, ApplyResult, FormField,
    extract_lever_ids, resolve_apply_url,
)


class LeverProvider(BaseApplyProvider):
    """Lever Postings API integration for direct apply."""

    BASE_URL = "https://api.lever.co/v0/postings"

    def get_provider_name(self) -> str:
        return "Lever"

    async def _resolve_ids(self, apply_url: str) -> tuple:
        """Extract Lever IDs, resolving redirect URLs if needed."""
        ids = extract_lever_ids(apply_url or "")
        if ids:
            return ids
        # URL might be an aggregator redirect (Adzuna, etc.) — resolve it
        if apply_url:
            resolved = await resolve_apply_url(apply_url)
            ids = extract_lever_ids(resolved)
            if ids:
                return ids
        return None

    async def get_application_form(self, job: dict) -> list[FormField]:
        """
        Fetch application form for a Lever posting.
        Lever's Postings API is public for reading — no auth needed for GET.
        """
        ids = await self._resolve_ids(job.get("apply_url", ""))
        if not ids:
            return self._default_fields()

        company_slug, posting_id = ids
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/{company_slug}/{posting_id}",
                )
                if resp.status_code != 200:
                    return self._default_fields()

                data = resp.json()
                fields = self._default_fields()

                # Parse Lever custom form fields
                for form_list in data.get("lists", []):
                    fields.append(FormField(
                        name=f"custom_{form_list.get('text', '').lower().replace(' ', '_')}",
                        label=form_list.get("text", ""),
                        field_type="textarea",
                        required=False,
                        description="",
                    ))

                return fields
        except Exception as e:
            print(f"[Lever] Form fetch error: {e}")
            return self._default_fields()

    async def submit_application(
        self,
        candidate: CandidateProfile,
        job: dict,
        resume_bytes: Optional[bytes] = None,
    ) -> ApplyResult:
        """
        Submit a candidate application to Lever via Postings API.
        Uses multipart/form-data for resume uploads.
        """
        settings = get_settings()
        api_key = settings.LEVER_API_KEY
        steps = []

        # Step 1: Parse Lever URL identifiers (resolve redirects if needed)
        ids = await self._resolve_ids(job.get("apply_url", ""))

        steps.append({
            "step": "url_parsed",
            "label": "Job URL Analyzed",
            "detail": f"Company: {ids[0]}, Posting: {ids[1][:12]}..." if ids else "Could not extract Lever posting ID from URL",
            "status": "completed" if ids else "error",
        })

        # Step 2: Map candidate profile to Lever schema
        form_data = {
            "name": candidate.full_name,
            "email": candidate.email,
        }
        if candidate.phone:
            form_data["phone"] = candidate.phone
        if candidate.linkedin_url:
            form_data["urls[LinkedIn]"] = candidate.linkedin_url
        if candidate.portfolio_url:
            form_data["urls[Portfolio]"] = candidate.portfolio_url
        if candidate.current_company:
            form_data["org"] = candidate.current_company

        steps.append({
            "step": "profile_mapped",
            "label": "Profile Mapped to ATS Schema",
            "detail": f"Name: {candidate.full_name}, Email: {candidate.email}",
            "status": "completed",
        })

        # Step 3: Prepare resume
        files = {}
        if resume_bytes and candidate.resume_filename:
            files["resume"] = (candidate.resume_filename, resume_bytes, "application/pdf")
            steps.append({
                "step": "resume_attached",
                "label": "Resume Uploaded",
                "detail": candidate.resume_filename,
                "status": "completed",
            })

        # Step 4: Cover letter
        if candidate.cover_letter:
            form_data["comments"] = candidate.cover_letter
            steps.append({
                "step": "cover_letter_attached",
                "label": "Cover Letter Attached",
                "status": "completed",
            })

        # Step 5: Custom answers
        for key, value in candidate.custom_answers.items():
            form_data[key] = value
        if candidate.custom_answers:
            steps.append({
                "step": "questions_answered",
                "label": "Custom Questions Mapped",
                "detail": f"{len(candidate.custom_answers)} answers",
                "status": "completed",
            })

        # Step 6: Submit to Lever
        steps.append({
            "step": "submitting",
            "label": "Submitting Application",
            "detail": "Sending to Lever Postings API..." if ids else "Recording application...",
            "status": "in_progress",
        })

        # If we couldn't extract IDs, fail instead of recording locally
        if not ids:
            steps[-1]["status"] = "error"
            steps[-1]["detail"] = "Could not extract Lever company slug and posting ID from URL"
            return ApplyResult(
                success=False,
                provider="Lever",
                message="Cannot submit: Missing job identifiers.",
                error_code="INVALID_URL",
                steps_completed=steps,
            )

        company_slug, posting_id = ids
        url = f"{self.BASE_URL}/{company_slug}/{posting_id}"
        params = {}
        if api_key:
            params["key"] = api_key
            
        # If no API key, try submitting without one (Lever public postings allow this)
        if not api_key:
            print("[Lever] No LEVER_API_KEY set — attempting public posting submission")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                last_error = None
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        resp = await client.post(
                            url,
                            data=form_data,
                            files=files if files else None,
                            params=params,
                        )

                        if resp.status_code in (200, 201):
                            response_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                            steps[-1]["status"] = "completed"
                            steps[-1]["detail"] = "Application submitted successfully!"

                            steps.append({
                                "step": "confirmed",
                                "label": "Application Confirmed",
                                "detail": f"Application ID: {response_data.get('applicationId', 'N/A')}",
                                "status": "completed",
                            })

                            return ApplyResult(
                                success=True,
                                provider="Lever",
                                message="Application submitted successfully to Lever!",
                                candidate_id=str(response_data.get("candidateId", "")),
                                application_id=str(response_data.get("applicationId", "")),
                                ats_response=response_data,
                                steps_completed=steps,
                            )

                        elif resp.status_code == 422:
                            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                            steps[-1]["status"] = "error"
                            steps[-1]["detail"] = f"Validation error: {error_data}"
                            return ApplyResult(
                                success=False,
                                provider="Lever",
                                message=f"Application validation failed: {error_data}",
                                error_code="VALIDATION_ERROR",
                                ats_response=error_data,
                                steps_completed=steps,
                            )

                        elif resp.status_code == 429:
                            import asyncio, random
                            if attempt < max_retries - 1:
                                # Respect Retry-After header
                                retry_after = resp.headers.get("Retry-After")
                                if retry_after:
                                    try:
                                        wait = float(retry_after) + random.uniform(0.5, 1.5)
                                    except ValueError:
                                        wait = (2 ** attempt) + random.uniform(1.0, 3.0)
                                else:
                                    wait = (2 ** attempt) + random.uniform(0.5, 2.0)
                                print(f"[Lever] 429 rate limited, attempt {attempt+1}/{max_retries}, waiting {wait:.1f}s")
                                steps[-1]["detail"] = f"Rate limited — retrying in {wait:.0f}s (attempt {attempt+1})"
                                await asyncio.sleep(wait)
                                continue
                            steps[-1]["status"] = "error"
                            steps[-1]["detail"] = f"Rate limited by Lever after {max_retries} attempts"
                            return ApplyResult(
                                success=False,
                                provider="Lever",
                                message="Rate limited by Lever. Please try again later.",
                                error_code="RATE_LIMITED",
                                steps_completed=steps,
                            )

                        else:
                            error_body = resp.text[:300]
                            last_error = f"HTTP {resp.status_code}: {error_body}"
                            if attempt < max_retries - 1:
                                import asyncio, random
                                wait = (2 ** attempt) + random.uniform(0.5, 2.0)
                                print(f"[Lever] HTTP {resp.status_code}, retrying in {wait:.1f}s (attempt {attempt+1})")
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
                    provider="Lever",
                    message=f"Failed to submit: {last_error}",
                    error_code="SUBMISSION_FAILED",
                    steps_completed=steps,
                )

        except Exception as e:
            steps[-1]["status"] = "error"
            steps[-1]["detail"] = str(e)
            return ApplyResult(
                success=False,
                provider="Lever",
                message=f"Submission error: {str(e)}",
                error_code="NETWORK_ERROR",
                steps_completed=steps,
            )

    def _default_fields(self) -> list[FormField]:
        """Default fields for Lever applications."""
        return [
            FormField(
                name="name", label="Full Name", field_type="text",
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
                name="comments", label="Cover Letter / Additional Info",
                field_type="textarea", required=False, auto_fillable=True,
            ),
            FormField(
                name="urls[LinkedIn]", label="LinkedIn Profile",
                field_type="text", required=False, auto_fillable=True,
            ),
            FormField(
                name="urls[Portfolio]", label="Portfolio / GitHub",
                field_type="text", required=False, auto_fillable=True,
            ),
            FormField(
                name="org", label="Current Company",
                field_type="text", required=False, auto_fillable=True,
            ),
        ]
