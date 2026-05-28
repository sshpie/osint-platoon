"""Weapons Squad — Document & Metadata Intel. PDFs, DOCX, metadata extraction."""
from __future__ import annotations
import io
import json
import re
from datetime import datetime, timezone
import httpx
from platoon.models.spot_report import SPOTReport, Finding
from platoon.models.tasking import SquadTasking
from platoon.utils.claude_runner import run_claude
from platoon.utils.logger import get_logger
from platoon.squads.alpha import _parse_spot

_SYSTEM = """\
You are the Weapons Squad — Document Intelligence — of an OSINT research platoon (ATP 3-21.8).

Mission: Find and analyze publicly accessible documents associated with the target.
PDFs, DOCX, XLSX, presentations — extract author info, org names, timestamps, software versions,
GPS coordinates (if present), and any other metadata.

Rules of Engagement:
- Only fetch documents that are publicly indexed (appear in search results).
- Use web_search to locate documents, then we will fetch and analyze them.
- Note metadata fields: Author, Creator, Producer, Company, LastModifiedBy, GPS.

Output: Conclude with SPOT JSON:

```json
{
  "squad": "weapons",
  "finds": [
    {
      "type": "document_metadata|author|company|gps_coordinates|software_version|creation_date",
      "value": "the finding",
      "source_url": "https://...",
      "timestamp": "2026-01-01T00:00:00Z",
      "confidence": 0.85,
      "metadata": {
        "filename": "report.pdf",
        "author": "John Doe",
        "company": "ACME Corp",
        "created": "2025-01-15",
        "software": "Microsoft Word 16.0"
      }
    }
  ],
  "pivots": ["author name", "company name", "email from metadata"],
  "confidence": 0.7
}
```
"""

_PDF_HEADERS = {"User-Agent": "osint-platoon/1.0 (security research)"}
_MAX_DOC_SIZE = 5 * 1024 * 1024  # 5MB


async def _fetch_pdf_metadata(url: str) -> dict:
    """Fetch a publicly accessible PDF and extract metadata."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.head(url, headers=_PDF_HEADERS)
            content_type = resp.headers.get("content-type", "")
            content_length = int(resp.headers.get("content-length", 0))
            if content_length > _MAX_DOC_SIZE:
                return {"error": "document too large"}
            if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
                return {"error": "not a PDF"}

            resp = await client.get(url, headers=_PDF_HEADERS)
            if resp.status_code != 200:
                return {"error": f"http_{resp.status_code}"}

            try:
                import PyPDF2  # type: ignore
                reader = PyPDF2.PdfReader(io.BytesIO(resp.content))
                meta = reader.metadata or {}
                return {k.lstrip("/"): str(v) for k, v in meta.items()}
            except ImportError:
                return {"error": "PyPDF2 not installed", "content_type": content_type}
            except Exception as e:
                return {"error": str(e)[:100]}
    except Exception as e:
        return {"error": str(e)[:100]}


def _metadata_to_findings(metadata: dict, url: str) -> list[Finding]:
    finds: list[Finding] = []
    now = datetime.now(timezone.utc)
    field_type_map = {
        "Author": "author",
        "Creator": "author",
        "Company": "company",
        "LastModifiedBy": "author",
        "Producer": "software_version",
        "CreationDate": "creation_date",
        "ModDate": "creation_date",
        "Subject": "document_metadata",
        "Title": "document_metadata",
        "Keywords": "document_metadata",
    }
    for field, value in metadata.items():
        if "error" in field.lower() or not value or len(str(value)) < 2:
            continue
        ftype = field_type_map.get(field, "document_metadata")
        finds.append(Finding(
            type=ftype,
            value=str(value)[:300],
            source_url=url,
            timestamp=now,
            confidence=0.9,
            metadata={"field": field, "filename": url.split("/")[-1][:100]},
        ))
    return finds


class WeaponsSquad:
    async def run(self, target: str, tasking: SquadTasking) -> SPOTReport:
        log = get_logger()
        log.log("squad_dispatched", squad="weapons", objective=tasking.objective[:80])

        brief = (
            f"MISSION — WEAPONS SQUAD — DOCUMENT INTELLIGENCE\n\n"
            f"Primary target: {target}\n"
            f"Objective: {tasking.objective}\n"
            f"Mode: {tasking.mode.upper()}\n\n"
            f"Execute document reconnaissance:\n"
            f"1. Search for publicly accessible PDFs, presentations, and reports associated with {target}\n"
            f"   (Use: site:example.com filetype:pdf, OR '{target}' filetype:pdf, etc.)\n"
            f"2. Find job postings that reveal technology stack\n"
            f"3. Look for annual reports, press releases, technical documentation\n"
            f"4. Note any direct document URLs you find (they will be analyzed for metadata)\n\n"
            f"For each document found, extract: author, organization, creation date, software used.\n\n"
            f"Conclude with the SPOT JSON block."
        )

        text = await run_claude(
            brief,
            system=_SYSTEM,
            model="claude-sonnet-4-6",
            allow_web_search=True,
        )

        # Extract any PDF URLs found in the text and fetch metadata
        pdf_urls = re.findall(r'https?://[^\s<>"\']+\.pdf(?:\?[^\s<>"\']*)?', text, re.IGNORECASE)[:5]
        raw_meta_finds: list[Finding] = []
        for url in pdf_urls:
            meta = await _fetch_pdf_metadata(url)
            raw_meta_finds.extend(_metadata_to_findings(meta, url))

        report = _parse_spot(text, "weapons")
        # Merge raw metadata finds
        existing_vals = {f.value for f in report.finds}
        for f in raw_meta_finds:
            if f.value not in existing_vals:
                report.finds.append(f)

        log.log("spot_report", squad="weapons", findings=len(report.finds),
                pivots=len(report.pivots), pdf_urls_analyzed=len(pdf_urls))
        return report
