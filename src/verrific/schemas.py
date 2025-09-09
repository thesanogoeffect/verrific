from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class Reference(BaseModel):
    """Schema for a bibliographic reference extracted from a Grobid TEI file.

    Fields are intentionally optional because Grobid output (or fallback
    heuristics) might not always yield complete metadata.
    """
    doi: Optional[str] = Field(default=None, description="Digital Object Identifier if detected")
    title: Optional[str] = Field(default=None, description="Title of the work")
    first_author_surname: Optional[str] = Field(default=None, description="Surname of the first author")
    raw: Optional[str] = Field(default=None, description="Raw string captured (fallback when structured data missing)")
    glutton: Optional[Dict[str, Any]] = Field(default=None, description="Enriched metadata returned by biblio-glutton")

    def key(self) -> str:
        """Return a stable key to help with de-duplication."""
        if self.doi:
            return f"doi:{self.doi.lower()}"
        parts = [self.first_author_surname or "", self.title or "", self.raw or ""]
        return "|".join(p.strip().lower() for p in parts if p)

