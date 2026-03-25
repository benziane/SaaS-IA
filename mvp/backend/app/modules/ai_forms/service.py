"""
AI Forms service - Create, manage, and analyze AI-powered forms.
"""

import json
import secrets
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.ai_forms import AIForm, FormResponse

logger = structlog.get_logger()

VALID_FIELD_TYPES = {
    "text", "email", "number", "select", "multiselect",
    "rating", "textarea", "date", "file",
}


class AIFormsService:
    """Service for AI forms operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ─── CRUD ──────────────────────────────────────────────────────────────────────

    async def create_form(self, user_id: UUID, data: dict) -> AIForm:
        """Create a new form."""
        fields = data.get("fields", [])
        if isinstance(fields, list):
            fields = [f if isinstance(f, dict) else f.model_dump() if hasattr(f, "model_dump") else f for f in fields]

        form = AIForm(
            user_id=user_id,
            title=data["title"],
            description=data.get("description"),
            fields_json=json.dumps(fields),
            style=data.get("style", "conversational"),
            thank_you_message=data.get("thank_you_message"),
            is_public=data.get("is_public", False),
            responses_count=0,
            status="draft",
        )
        self.session.add(form)
        await self.session.commit()
        await self.session.refresh(form)

        logger.info("form_created", form_id=str(form.id), title=form.title)
        return form

    async def list_forms(self, user_id: UUID) -> list[AIForm]:
        """List all forms for a user."""
        result = await self.session.execute(
            select(AIForm)
            .where(AIForm.user_id == user_id, AIForm.is_deleted == False)
            .order_by(AIForm.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_form(self, user_id: UUID, form_id: UUID) -> Optional[AIForm]:
        """Get form details, verifying ownership."""
        form = await self.session.get(AIForm, form_id)
        if not form or form.user_id != user_id or form.is_deleted:
            return None
        return form

    async def update_form(self, user_id: UUID, form_id: UUID, data: dict) -> Optional[AIForm]:
        """Update form settings."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return None

        for field in ["title", "description", "style", "thank_you_message", "is_public"]:
            if field in data and data[field] is not None:
                setattr(form, field, data[field])

        if "fields" in data and data["fields"] is not None:
            fields = data["fields"]
            if isinstance(fields, list):
                fields = [
                    f if isinstance(f, dict) else f.model_dump() if hasattr(f, "model_dump") else f
                    for f in fields
                ]
            form.fields_json = json.dumps(fields)

        form.updated_at = datetime.now(UTC)
        self.session.add(form)
        await self.session.commit()
        await self.session.refresh(form)

        logger.info("form_updated", form_id=str(form_id))
        return form

    async def delete_form(self, user_id: UUID, form_id: UUID) -> bool:
        """Soft delete a form."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return False

        form.is_deleted = True
        form.status = "closed"
        form.updated_at = datetime.now(UTC)
        self.session.add(form)
        await self.session.commit()

        logger.info("form_deleted", form_id=str(form_id))
        return True

    # ─── Publish / Close ───────────────────────────────────────────────────────────

    async def publish_form(self, user_id: UUID, form_id: UUID) -> Optional[AIForm]:
        """Generate share_token and set form status to published."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return None

        if not form.share_token:
            form.share_token = secrets.token_urlsafe(32)

        form.status = "published"
        form.updated_at = datetime.now(UTC)
        self.session.add(form)
        await self.session.commit()
        await self.session.refresh(form)

        logger.info("form_published", form_id=str(form_id), share_token=form.share_token)
        return form

    async def close_form(self, user_id: UUID, form_id: UUID) -> Optional[AIForm]:
        """Close form to new responses."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return None

        form.status = "closed"
        form.updated_at = datetime.now(UTC)
        self.session.add(form)
        await self.session.commit()
        await self.session.refresh(form)

        logger.info("form_closed", form_id=str(form_id))
        return form

    # ─── Public response submission ────────────────────────────────────────────────

    async def _get_form_by_token(self, share_token: str) -> Optional[AIForm]:
        """Retrieve a published form by its share token."""
        result = await self.session.execute(
            select(AIForm).where(
                AIForm.share_token == share_token,
                AIForm.status == "published",
                AIForm.is_deleted == False,
            )
        )
        return result.scalars().first()

    async def submit_response(
        self, form_id: UUID, share_token: str, answers: dict
    ) -> Optional[FormResponse]:
        """Public submission - validate answers against field types/required, store response."""
        form = await self._get_form_by_token(share_token)
        if not form or form.id != form_id:
            return None

        # Validate answers against fields
        fields = json.loads(form.fields_json) if form.fields_json else []
        validation_errors = self._validate_answers(fields, answers)
        if validation_errors:
            logger.warning(
                "form_response_validation_failed",
                form_id=str(form_id),
                errors=validation_errors,
            )
            raise ValueError(f"Validation failed: {'; '.join(validation_errors)}")

        response = FormResponse(
            form_id=form_id,
            answers_json=json.dumps(answers),
        )
        self.session.add(response)

        # Update responses count
        form.responses_count = (form.responses_count or 0) + 1
        form.updated_at = datetime.now(UTC)
        self.session.add(form)

        await self.session.commit()
        await self.session.refresh(response)

        logger.info(
            "form_response_submitted",
            form_id=str(form_id),
            response_id=str(response.id),
        )
        return response

    def _validate_answers(self, fields: list[dict], answers: dict) -> list[str]:
        """Validate submitted answers against field definitions."""
        errors = []
        field_map = {f["field_id"]: f for f in fields}

        for field in fields:
            fid = field["field_id"]
            ftype = field.get("type", "text")
            required = field.get("required", False)
            value = answers.get(fid)

            if required and (value is None or value == "" or value == []):
                errors.append(f"Field '{field.get('label', fid)}' is required")
                continue

            if value is None or value == "":
                continue

            if ftype == "email" and isinstance(value, str) and "@" not in value:
                errors.append(f"Field '{field.get('label', fid)}' must be a valid email")

            if ftype == "number":
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field.get('label', fid)}' must be a number")

            if ftype == "rating":
                try:
                    rating = float(value)
                    if rating < 0 or rating > 10:
                        errors.append(f"Field '{field.get('label', fid)}' must be between 0 and 10")
                except (ValueError, TypeError):
                    errors.append(f"Field '{field.get('label', fid)}' must be a number")

            if ftype == "select":
                options = field.get("options", [])
                if options and value not in options:
                    errors.append(f"Field '{field.get('label', fid)}' has invalid option")

            if ftype == "multiselect":
                options = field.get("options", [])
                if options and isinstance(value, list):
                    invalid = [v for v in value if v not in options]
                    if invalid:
                        errors.append(
                            f"Field '{field.get('label', fid)}' has invalid options: {invalid}"
                        )

        # Check for answers referencing non-existent fields
        for answer_key in answers:
            if answer_key not in field_map:
                errors.append(f"Unknown field: '{answer_key}'")

        return errors

    # ─── Response management ───────────────────────────────────────────────────────

    async def list_responses(self, user_id: UUID, form_id: UUID) -> Optional[list[FormResponse]]:
        """List all responses for a form, verifying form ownership."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return None

        result = await self.session.execute(
            select(FormResponse)
            .where(FormResponse.form_id == form_id)
            .order_by(FormResponse.submitted_at.desc())
        )
        return list(result.scalars().all())

    async def get_response(
        self, user_id: UUID, form_id: UUID, response_id: UUID
    ) -> Optional[FormResponse]:
        """Get a single response, verifying form ownership."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return None

        response = await self.session.get(FormResponse, response_id)
        if not response or response.form_id != form_id:
            return None
        return response

    # ─── AI features ───────────────────────────────────────────────────────────────

    async def analyze_responses(self, user_id: UUID, form_id: UUID) -> Optional[dict]:
        """AI analysis of all responses - summary, trends, insights."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return None

        result = await self.session.execute(
            select(FormResponse).where(FormResponse.form_id == form_id)
        )
        responses = list(result.scalars().all())

        fields = json.loads(form.fields_json) if form.fields_json else []
        total_responses = len(responses)

        if total_responses == 0:
            return {
                "form_id": str(form_id),
                "total_responses": 0,
                "completion_rate": 0.0,
                "field_stats": {},
                "ai_insights": None,
            }

        # Calculate field stats
        field_stats = {}
        total_fields = len(fields)
        completion_scores = []

        for resp in responses:
            answers = json.loads(resp.answers_json) if resp.answers_json else {}
            answered_count = sum(
                1 for f in fields if f.get("field_id") in answers and answers[f["field_id"]]
            )
            completion_scores.append(
                answered_count / total_fields if total_fields > 0 else 1.0
            )

        for field in fields:
            fid = field["field_id"]
            ftype = field.get("type", "text")
            label = field.get("label", fid)
            values = []

            for resp in responses:
                answers = json.loads(resp.answers_json) if resp.answers_json else {}
                if fid in answers and answers[fid] is not None and answers[fid] != "":
                    values.append(answers[fid])

            stat: dict = {
                "label": label,
                "type": ftype,
                "response_count": len(values),
                "fill_rate": round(len(values) / total_responses, 2) if total_responses else 0,
            }

            if ftype in ("number", "rating") and values:
                nums = []
                for v in values:
                    try:
                        nums.append(float(v))
                    except (ValueError, TypeError):
                        pass
                if nums:
                    stat["average"] = round(sum(nums) / len(nums), 2)
                    stat["min"] = min(nums)
                    stat["max"] = max(nums)

            if ftype in ("select", "multiselect") and values:
                option_counts: dict[str, int] = {}
                for v in values:
                    if isinstance(v, list):
                        for item in v:
                            option_counts[str(item)] = option_counts.get(str(item), 0) + 1
                    else:
                        option_counts[str(v)] = option_counts.get(str(v), 0) + 1
                stat["option_distribution"] = option_counts

            field_stats[fid] = stat

        completion_rate = round(
            sum(completion_scores) / len(completion_scores), 2
        ) if completion_scores else 0.0

        # AI insights via AIAssistantService
        ai_insights = None
        if total_responses >= 2:
            try:
                from app.ai_assistant.service import AIAssistantService

                summary_data = {
                    "form_title": form.title,
                    "total_responses": total_responses,
                    "completion_rate": completion_rate,
                    "field_stats": field_stats,
                    "sample_answers": [],
                }

                for resp in responses[:10]:
                    answers = json.loads(resp.answers_json) if resp.answers_json else {}
                    summary_data["sample_answers"].append(answers)

                prompt = (
                    f"Analyze these form responses and provide insights:\n\n"
                    f"Form: {form.title}\n"
                    f"Total responses: {total_responses}\n"
                    f"Completion rate: {completion_rate * 100:.0f}%\n\n"
                    f"Field statistics:\n{json.dumps(field_stats, indent=2)}\n\n"
                    f"Sample answers:\n{json.dumps(summary_data['sample_answers'], indent=2)}\n\n"
                    f"Provide: 1) Key trends 2) Notable patterns 3) Actionable recommendations"
                )

                result = await AIAssistantService.process_text_with_provider(
                    text=prompt,
                    task="form_response_analysis",
                    provider_name="gemini",
                    user_id=form.user_id,
                    module="ai_forms",
                )
                ai_insights = result.get("processed_text")
            except Exception as e:
                logger.error("form_analysis_ai_failed", error=str(e), form_id=str(form_id))

        return {
            "form_id": str(form_id),
            "total_responses": total_responses,
            "completion_rate": completion_rate,
            "field_stats": field_stats,
            "ai_insights": ai_insights,
        }

    async def generate_form(self, user_id: UUID, prompt: str, num_fields: int = 5) -> AIForm:
        """AI-generated form from natural language description."""
        generated_fields = []

        try:
            from app.ai_assistant.service import AIAssistantService

            generation_prompt = (
                f"Generate a form with exactly {num_fields} fields based on this description:\n\n"
                f'"{prompt}"\n\n'
                f"Return ONLY a valid JSON array where each element has:\n"
                f'- "field_id": lowercase_snake_case unique identifier\n'
                f'- "type": one of text, email, number, select, multiselect, rating, textarea, date, file\n'
                f'- "label": human-readable label\n'
                f'- "required": boolean\n'
                f'- "options": array of strings (only for select/multiselect, null otherwise)\n'
                f'- "validation": null\n'
                f'- "condition": null\n\n'
                f"Return only the JSON array, no markdown, no explanation."
            )

            result = await AIAssistantService.process_text_with_provider(
                text=generation_prompt,
                task="form_generation",
                provider_name="gemini",
                user_id=user_id,
                module="ai_forms",
            )

            raw_text = result.get("processed_text", "[]")
            # Extract JSON from possible markdown code blocks
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)
            if isinstance(parsed, list):
                # Validate and sanitize generated fields
                for f in parsed:
                    ftype = f.get("type", "text")
                    if ftype not in VALID_FIELD_TYPES:
                        ftype = "text"
                    generated_fields.append({
                        "field_id": str(f.get("field_id", f"field_{len(generated_fields)+1}")),
                        "type": ftype,
                        "label": str(f.get("label", f"Field {len(generated_fields)+1}")),
                        "required": bool(f.get("required", False)),
                        "options": f.get("options") if ftype in ("select", "multiselect") else None,
                        "validation": f.get("validation"),
                        "condition": f.get("condition"),
                    })

            logger.info("form_generated_via_ai", num_fields=len(generated_fields))
        except Exception as e:
            logger.error("form_generation_ai_failed", error=str(e))

        # Fallback: generate basic fields if AI failed
        if not generated_fields:
            for i in range(num_fields):
                generated_fields.append({
                    "field_id": f"field_{i+1}",
                    "type": "text",
                    "label": f"Question {i+1}",
                    "required": i == 0,
                    "options": None,
                    "validation": None,
                    "condition": None,
                })

        # Extract a title from the prompt
        title = prompt[:100].strip()
        if len(prompt) > 100:
            title += "..."

        form = AIForm(
            user_id=user_id,
            title=title,
            description=prompt,
            fields_json=json.dumps(generated_fields),
            style="conversational",
            responses_count=0,
            status="draft",
        )
        self.session.add(form)
        await self.session.commit()
        await self.session.refresh(form)

        logger.info("form_generated", form_id=str(form.id), num_fields=len(generated_fields))
        return form

    async def score_response(
        self, user_id: UUID, form_id: UUID, response_id: UUID
    ) -> Optional[FormResponse]:
        """AI scoring of an individual response."""
        form = await self.get_form(user_id, form_id)
        if not form:
            return None

        response = await self.session.get(FormResponse, response_id)
        if not response or response.form_id != form_id:
            return None

        fields = json.loads(form.fields_json) if form.fields_json else []
        answers = json.loads(response.answers_json) if response.answers_json else {}

        try:
            from app.ai_assistant.service import AIAssistantService

            prompt = (
                f"Score this form response on a scale of 0.0 to 1.0 and provide analysis.\n\n"
                f"Form: {form.title}\n"
                f"Fields:\n{json.dumps(fields, indent=2)}\n\n"
                f"Answers:\n{json.dumps(answers, indent=2)}\n\n"
                f"Return a JSON object with:\n"
                f'- "score": float between 0.0 and 1.0 (completeness and quality)\n'
                f'- "analysis": brief analysis string\n\n'
                f"Return only the JSON object, no markdown."
            )

            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="form_response_scoring",
                provider_name="gemini",
                user_id=user_id,
                module="ai_forms",
            )

            raw_text = result.get("processed_text", "{}")
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)
            score = float(parsed.get("score", 0.5))
            score = max(0.0, min(1.0, score))
            analysis = str(parsed.get("analysis", ""))

            response.score = score
            response.analysis = analysis
        except Exception as e:
            logger.error(
                "form_response_scoring_failed",
                error=str(e),
                response_id=str(response_id),
            )
            # Fallback: basic completeness score
            total_fields = len(fields)
            required_fields = [f for f in fields if f.get("required")]
            answered = sum(1 for f in fields if f.get("field_id") in answers and answers[f["field_id"]])
            response.score = round(answered / total_fields, 2) if total_fields else 0.5
            response.analysis = f"Answered {answered}/{total_fields} fields."

        self.session.add(response)
        await self.session.commit()
        await self.session.refresh(response)

        logger.info(
            "form_response_scored",
            response_id=str(response_id),
            score=response.score,
        )
        return response
