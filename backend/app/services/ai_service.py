"""AI services: resume analysis, cover letters, skill gap, interview prep.

AI features accept an optional user-supplied API key (OpenAI or Gemini). When a
key + provider are provided, requests are forwarded to that LLM. When omitted,
a deterministic heuristic engine is used so the platform works without keys.
"""
from __future__ import annotations

import json
import re
from typing import Any, Literal

import httpx

Provider = Literal["openai", "gemini"]

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_MODEL = "gemini-1.5-flash"

SKILL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "Dart", "Flutter",
    "Swift", "Kotlin", "Java", "C++", "C#", "Go", "Rust", "SQL", "PostgreSQL", "MongoDB",
    "Redis", "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Django", "FastAPI", "Flask",
    "Spring", "GraphQL", "REST", "CI/CD", "Git", "Linux", "Machine Learning", "Deep Learning",
    "PyTorch", "TensorFlow", "LLM", "RAG", "NLP", "Data Science", "Pandas", "NumPy",
    "Figma", "UI/UX", "Design Systems", "Prototyping", "Tailwind", "CSS", "HTML",
    "Agile", "Scrum", "Leadership", "Communication", "Project Management", "SEO", "Marketing",
]


def _extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort parse of a JSON object from an LLM response."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


class AIService:
    """Thin wrapper over OpenAI/Gemini chat completions with a heuristic fallback."""

    async def _chat(
        self,
        *,
        system: str,
        user: str,
        api_key: str,
        provider: Provider,
        max_tokens: int = 1200,
    ) -> str | None:
        if provider == "gemini":
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}
                ],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens},
            }
            url = GEMINI_URL
            headers = {}
            params = {"key": api_key}
        else:
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }
            url = OPENAI_URL
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {}

        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(url, headers=headers, params=params, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json()

        if provider == "gemini":
            parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
        return data["choices"][0]["message"]["content"]

    async def _chat_json(
        self,
        *,
        system: str,
        user: str,
        api_key: str,
        provider: Provider,
    ) -> dict[str, Any] | None:
        text = await self._chat(system=system, user=user, api_key=api_key, provider=provider)
        if not text:
            return None
        return _extract_json(text)

    # ------------------------------------------------------------
    # Heuristic fallback engine
    # ------------------------------------------------------------
    def _extract_skills(self, text: str) -> list[str]:
        found = [s for s in SKILL_KEYWORDS if re.search(rf"\b{re.escape(s)}\b", text, re.IGNORECASE)]
        return found

    def _length_score(self, text: str) -> int:
        words = len(text.split())
        if 300 <= words <= 900:
            return 30
        if 200 <= words < 300 or 900 < words <= 1200:
            return 20
        return 10

    def _keyword_density_score(self, text: str) -> int:
        skills = self._extract_skills(text)
        if len(skills) >= 10:
            return 30
        if len(skills) >= 6:
            return 22
        if len(skills) >= 3:
            return 14
        return 6

    def _action_verb_score(self, text: str) -> int:
        verbs = ["built", "led", "designed", "developed", "launched", "improved", "shipped", "managed", "created", "optimized"]
        hits = sum(1 for v in verbs if re.search(rf"\b{v}\b", text, re.IGNORECASE))
        return min(hits * 4, 20)

    def _metrics_score(self, text: str) -> int:
        has_percent = bool(re.search(r"\d+\s?%", text))
        has_numbers = bool(re.search(r"\d+[KkMm]|\$\d|\d{3,}", text))
        if has_percent and has_numbers:
            return 20
        if has_numbers:
            return 10
        return 4

    async def analyze_resume(
        self,
        resume_text: str,
        target_role: str | None = None,
        job_description: str | None = None,
        api_key: str | None = None,
        provider: Provider = "openai",
    ) -> dict[str, Any]:
        if api_key:
            prompt = (
                f"Resume:\n{resume_text}\n\n"
                f"Target role: {target_role or 'unspecified'}\n"
                f"Job description: {job_description or 'none provided'}"
            )
            data = await self._chat_json(
                system=(
                    "You are an expert ATS resume reviewer. Analyze the resume for ATS "
                    "compatibility and return ONLY a JSON object with exactly these keys: "
                    '"ats_score" (integer 0-99), "missing_keywords" (array of strings), '
                    '"suggestions" (array of concrete improvement strings), "summary" (one '
                    'sentence). Do not include markdown.'
                ),
                user=prompt,
                api_key=api_key,
                provider=provider,
            )
            if data and isinstance(data.get("ats_score"), int):
                score = max(20, min(int(data["ats_score"]), 99))
                return {
                    "ats_score": score,
                    "missing_keywords": [str(k) for k in (data.get("missing_keywords") or [])],
                    "suggestions": [str(s) for s in (data.get("suggestions") or [])],
                    "summary": str(data.get("summary") or ""),
                }

        skills = self._extract_skills(resume_text)
        ats_score = (
            self._length_score(resume_text)
            + self._keyword_density_score(resume_text)
            + self._action_verb_score(resume_text)
            + self._metrics_score(resume_text)
        )
        ats_score = max(20, min(ats_score, 99))

        missing: list[str] = []
        if target_role:
            role_terms = {"developer": ["TypeScript", "Git", "REST", "CI/CD"], "designer": ["Figma", "Design Systems"], "data": ["Pandas", "SQL", "NumPy"]}
            for term in role_terms.get(target_role.lower(), []):
                if term not in skills:
                    missing.append(term)

        suggestions = [
            "Add quantified achievements with percentages or metrics.",
            "Include a dedicated skills section for ATS keyword matching.",
            "Use strong action verbs (built, shipped, led) to open bullet points.",
            "Tailor keywords to each job description before applying.",
            "Keep resume length between 300 and 900 words.",
        ]
        if len(skills) < 6:
            suggestions.append("List more relevant technical skills to pass keyword screening.")

        return {
            "ats_score": ats_score,
            "missing_keywords": missing or [s for s in ["TypeScript", "Docker", "CI/CD"] if s not in skills][:3],
            "suggestions": suggestions,
            "summary": f"Your resume scored {ats_score}/99. Strengthen keyword coverage and quantify impact to reach the top band.",
        }

    async def cover_letter(
        self,
        resume_text: str,
        job_title: str,
        company_name: str,
        job_description: str | None,
        api_key: str | None = None,
        provider: Provider = "openai",
    ) -> str:
        if api_key:
            prompt = (
                f"Job title: {job_title}\nCompany: {company_name}\n"
                f"Job description: {job_description or 'none provided'}\n\nResume:\n{resume_text}"
            )
            text = await self._chat(
                system=(
                    "You are a professional career coach. Write a compelling, human, 3-4 "
                    "paragraph cover letter for the role based on the candidate's resume. "
                    "Tailor it to the company and job description. Return only the letter body, "
                    "no subject line or signature placeholders."
                ),
                user=prompt,
                api_key=api_key,
                provider=provider,
            )
            if text:
                return text.strip()

        skills = self._extract_skills(resume_text)
        skill_line = ", ".join(skills[:6]) if skills else "relevant experience"
        return (
            f"Dear Hiring Manager at {company_name},\n\n"
            f"I am writing to express my strong interest in the {job_title} role. "
            f"With demonstrated experience across {skill_line}, I am confident I can deliver measurable impact from day one.\n\n"
            f"In my previous roles I focused on shipping reliable, user-centric solutions, collaborating closely with "
            f"cross-functional teams, and continuously improving quality and performance. I take ownership of outcomes "
            f"and enjoy turning ambiguous problems into shipped products.\n\n"
            f"I would welcome the opportunity to discuss how my background aligns with {company_name}'s goals. "
            f"Thank you for your time and consideration.\n\nSincerely,\n[Your Name]"
        )

    async def skill_gap(
        self,
        resume_text: str,
        target_role: str,
        api_key: str | None = None,
        provider: Provider = "openai",
    ) -> dict[str, Any]:
        if api_key:
            data = await self._chat_json(
                system=(
                    "You are a career development expert. Analyze the gap between the candidate's "
                    "current skills and the target role. Return ONLY a JSON object with exactly "
                    'these keys: "current_skills" (array), "missing_skills" (array), '
                    '"recommended_learning" (array of actionable strings). No markdown.'
                ),
                user=f"Target role: {target_role}\n\nResume:\n{resume_text}",
                api_key=api_key,
                provider=provider,
            )
            if data and isinstance(data.get("current_skills"), list):
                return {
                    "current_skills": [str(s) for s in data["current_skills"]],
                    "missing_skills": [str(s) for s in (data.get("missing_skills") or [])],
                    "recommended_learning": [str(s) for s in (data.get("recommended_learning") or [])],
                }

        current = self._extract_skills(resume_text)
        role_map = {
            "flutter": ["Flutter", "Dart", "Firebase", "Riverpod", "CI/CD"],
            "react": ["React", "TypeScript", "Next.js", "Tailwind", "GraphQL"],
            "backend": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
            "data": ["Pandas", "SQL", "PyTorch", "MLOps", "Cloud"],
            "designer": ["Figma", "Design Systems", "Prototyping", "Usability Testing"],
        }
        needed = role_map.get(target_role.lower().split()[0], ["TypeScript", "SQL", "Docker", "CI/CD", "Communication"])
        missing = [s for s in needed if s not in current]
        return {
            "current_skills": current[:12],
            "missing_skills": missing,
            "recommended_learning": [
                f"Complete a guided project using {m} and add it to your resume." for m in missing
            ],
        }

    async def interview_questions(
        self,
        job_title: str,
        job_description: str | None,
        resume_text: str | None,
        api_key: str | None = None,
        provider: Provider = "openai",
    ) -> list[str]:
        if api_key:
            prompt = (
                f"Job title: {job_title}\nJob description: {job_description or 'none provided'}\n"
                f"Candidate resume: {resume_text or 'not provided'}"
            )
            data = await self._chat_json(
                system=(
                    "You are a senior hiring interviewer. Generate 8 insightful interview "
                    "questions for the role, mixing technical and behavioral. Return ONLY a JSON "
                    'object with a single key "questions" (array of strings). No markdown.'
                ),
                user=prompt,
                api_key=api_key,
                provider=provider,
            )
            if data and isinstance(data.get("questions"), list):
                return [str(q) for q in data["questions"]]

        questions = [
            f"Walk me through your experience relevant to this {job_title} role.",
            "Describe a challenging project you shipped. What was your role and the outcome?",
            "How do you prioritize tasks when facing competing deadlines?",
            "Tell me about a time you disagreed with a teammate. How did you resolve it?",
            "Where do you see yourself growing in the next 12 months?",
        ]
        if job_description and "system design" in job_description.lower():
            questions.insert(2, "Design a scalable system for [a described feature]. Walk me through your approach.")
        if job_description and "leadership" in job_description.lower():
            questions.insert(2, "How do you mentor junior engineers and build team culture?")
        return questions


ai_service = AIService()