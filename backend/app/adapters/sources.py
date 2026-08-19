"""Adapters for each job source. These are contract stubs showing how to
implement source-specific ingestion. Real deployments wire them to official
RSS/API/partner feeds (or opt-in listings) rather than scraping copyrighted
job descriptions.
"""
from __future__ import annotations

import asyncio

from app.adapters.base import BaseAdapter, NormalizedJob


class LinkedinAdapter(BaseAdapter):
    source_name = "linkedin"

    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        # Real implementation: LinkedIn RSS feed (www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search)
        # or partner API. Normalize into NormalizedJob with apply_url pointing at the canonical listing.
        return await asyncio.gather(*(self._demo(i) for i in range(limit)))

    async def _demo(self, i: int) -> NormalizedJob:
        return NormalizedJob(
            source=self.source_name,
            external_id=f"li-demo-{i}",
            title=f"Software Engineer (LinkedIn Demo {i})",
            company_name="Nova Labs",
            location="Bengaluru, India",
            remote=(i % 3 == 0),
            salary_min=1_200_000,
            salary_max=2_400_000,
            salary_currency="INR",
            salary_text="₹12L – ₹24L/yr",
            job_type="full_time",
            level="mid",
            skills=["TypeScript", "React", "SQL"],
            description="Demo listing placeholder for LinkedIn adapter.",
            apply_url=f"https://www.linkedin.com/jobs/view/demo-{i}",
            apply_on="LinkedIn",
            experience_min=2,
            experience_max=6,
        )


class IndeedAdapter(BaseAdapter):
    source_name = "indeed"

    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        return [NormalizedJob(
            source=self.source_name,
            external_id=f"in-demo-{i}",
            title=f"Full-Stack Engineer (Indeed Demo {i})",
            company_name="FinEdge",
            location="Mumbai, India",
            remote=False,
            salary_min=1_000_000,
            salary_max=2_000_000,
            salary_currency="INR",
            job_type="full_time",
            level="mid",
            skills=["Node.js", "React", "PostgreSQL"],
            description="Demo listing placeholder for Indeed adapter.",
            apply_url=f"https://in.indeed.com/viewjob/demo-{i}",
            apply_on="Indeed",
            experience_min=2,
            experience_max=5,
        ) for i in range(limit)]


class NaukriAdapter(BaseAdapter):
    source_name = "naukri"

    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        return [NormalizedJob(
            source=self.source_name,
            external_id=f"nk-demo-{i}",
            title=f"Frontend Developer (Naukri Demo {i})",
            company_name="PixelCraft",
            location="Gurugram, India",
            remote=False,
            salary_min=700_000,
            salary_max=1_500_000,
            salary_currency="INR",
            job_type="full_time",
            level="mid",
            skills=["React", "TypeScript", "CSS"],
            description="Demo listing placeholder for Naukri adapter.",
            apply_url=f"https://www.naukri.com/job/demo-{i}",
            apply_on="Naukri",
            experience_min=1,
            experience_max=4,
        ) for i in range(limit)]


class InternshalaAdapter(BaseAdapter):
    source_name = "internshala"

    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        return [NormalizedJob(
            source=self.source_name,
            external_id=f"is-demo-{i}",
            title=f"Software Engineering Intern (Internshala Demo {i})",
            company_name="Nova Labs",
            location="Remote",
            remote=True,
            salary_min=15_000,
            salary_max=30_000,
            salary_currency="INR",
            salary_text="₹15K – ₹30K/mo",
            job_type="internship",
            level="entry",
            skills=["Python", "SQL", "Communication"],
            description="Demo listing placeholder for Internshala adapter.",
            apply_url=f"https://internshala.com/internship/demo-{i}",
            apply_on="Internshala",
            experience_min=0,
            experience_max=0,
        ) for i in range(limit)]


class WellfoundAdapter(BaseAdapter):
    source_name = "wellfound"

    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        return [NormalizedJob(
            source=self.source_name,
            external_id=f"wf-demo-{i}",
            title=f"Founding Engineer (Wellfound Demo {i})",
            company_name="VertexAI",
            location="Remote",
            remote=True,
            salary_min=2_000_000,
            salary_max=4_500_000,
            salary_currency="INR",
            salary_text="₹20L – ₹45L/yr + equity",
            job_type="full_time",
            level="lead",
            skills=["Flutter", "Firebase", "GraphQL"],
            description="Demo listing placeholder for Wellfound adapter.",
            apply_url=f"https://wellfound.com/jobs/demo-{i}",
            apply_on="Wellfound",
            experience_min=4,
            experience_max=9,
        ) for i in range(limit)]


class CompanyAdapter(BaseAdapter):
    source_name = "company"

    async def fetch_latest(self, limit: int = 50) -> list[NormalizedJob]:
        # Real implementation: pull from each company's careers RSS/Greenhouse/Lever API.
        return [NormalizedJob(
            source=self.source_name,
            external_id=f"co-demo-{i}",
            title=f"Staff Engineer (Company Demo {i})",
            company_name="QuantumLabs",
            location="Pune, India",
            remote=False,
            salary_min=3_000_000,
            salary_max=5_000_000,
            salary_currency="INR",
            job_type="full_time",
            level="lead",
            skills=["Go", "Kubernetes", "Distributed Systems"],
            description="Demo listing placeholder for company career page adapter.",
            apply_url=f"https://careers.example.com/jobs/demo-{i}",
            apply_on="Company Website",
            experience_min=7,
            experience_max=12,
        ) for i in range(limit)]