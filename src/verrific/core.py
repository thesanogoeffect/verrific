from grobid_client.grobid_client import GrobidClient
import httpx
import asyncio
from pathlib import Path
from typing import List, Optional
from lxml import etree
import pandas as pd

# Support both package execution (python -m verrific.core) and direct script run
try:  # pragma: no cover - import fallback logic
    from .schemas import Reference  # type: ignore
except ImportError:  # Direct script execution
    import sys as _sys, pathlib as _pathlib
    pkg_root = _pathlib.Path(__file__).resolve().parent.parent
    if str(pkg_root) not in _sys.path:
        _sys.path.insert(0, str(pkg_root))
    from schemas import Reference  # type: ignore

class Verrific:
    """Primary class for reference verification. It is constructed either from a Grobid TEI XML,
    or a PDF file (needing to run Grobid first)."""
    def __init__(self, references: Optional[List[Reference]] = None):
        self.references: List[Reference] = references or []
    
    @classmethod
    def process_pdf_dir(cls, pdf_folder_path):
        # Logic to extract data from PDF
        client = GrobidClient(config_path="/Users/jakub/dev/verrific/.config.json")
        client.process("processFulltextDocument", pdf_folder_path, output="/Users/jakub/dev/verrific/tei", consolidate_citations=True, include_raw_citations=True, include_raw_affiliations=True, consolidate_header=True, n=12)
        return cls()
        
    @classmethod
    def from_grobid_tei(cls, tei_path):
        """Parse a Grobid TEI XML file into a `Verrific` instance with References.

        Extraction strategy:
        - Use lxml to parse the TEI.
        - Navigate to //biblStruct or listBibl//biblStruct (depending on Grobid version)
          capturing: DOI, title (analytic/title or monogr/title), first author surname
          fallback to raw <note type="raw_reference"> or concatenated text.
        - Return instance with collected Reference models.
        """
        path = Path(tei_path)
        if not path.exists():
            raise FileNotFoundError(f"TEI path not found: {tei_path}")

        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(path), parser)
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}

        refs: List[Reference] = []

        # Grobid typically stores structured references under listBibl/biblStruct
        bibl_structs = tree.xpath('//tei:listBibl/tei:biblStruct', namespaces=ns)
        if not bibl_structs:
            # Fallback: search any biblStruct
            bibl_structs = tree.xpath('//tei:biblStruct', namespaces=ns)

        for bs in bibl_structs:
            doi_node = bs.xpath('.//tei:idno[@type="DOI"]/text()', namespaces=ns)
            doi = doi_node[0].strip() if doi_node else None

            # Title preference: analytic (article) then monographic
            title_node = bs.xpath('.//tei:analytic/tei:title/text()', namespaces=ns)
            if not title_node:
                title_node = bs.xpath('.//tei:monogr/tei:title/text()', namespaces=ns)
            title = title_node[0].strip() if title_node else None

            # First author surname
            surname_node = bs.xpath('(.//tei:analytic//tei:author | .//tei:monogr//tei:author)[1]//tei:surname/text()', namespaces=ns)
            first_author_surname = surname_node[0].strip() if surname_node else None

            # Raw fallback: sometimes available as note type="raw_reference"
            raw_node = bs.xpath('.//tei:note[@type="raw_reference"]/text()', namespaces=ns)
            raw = raw_node[0].strip() if raw_node else None
            if not raw:
                # Compose a rough raw string from text content (limited length)
                raw_text = ' '.join(t.strip() for t in bs.xpath('.//text()', namespaces=ns) if t.strip())
                raw = raw_text[:500] if raw_text else None

            refs.append(Reference(doi=doi, title=title, first_author_surname=first_author_surname, raw=raw))

        return cls(references=refs)

    @classmethod
    def from_reference_strings(cls, reference_strings):
        # Logic to process raw reference strings
        return cls()

    # --------------------------- Enrichment via biblio-glutton ---------------------------
    async def enrich_with_biblio_glutton(self, base_url: str = "http://devserver:8080", timeout: float = 10.0, semaphore: int = 5):
        """Enrich references using a biblio-glutton instance.

        Query priority:
        1. If DOI present: GET /service/metadata?doi=...
        2. Else: GET /service/metadata?title=...&firstAuthor=...

        Biblio-glutton expects UTF-8; we send minimal params to avoid mismatches.
        Population: store raw JSON in `reference.glutton` if status 200 and contains data.
        """
        sem = asyncio.Semaphore(semaphore)

        async def fetch(client: httpx.AsyncClient, ref: Reference):
            params = {}
            if ref.doi:
                params['doi'] = ref.doi
            else:
                if ref.title:
                    params['atitle'] = ref.title
                if ref.first_author_surname:
                    params['firstAuthor'] = ref.first_author_surname
            if not params:
                return  # Not enough data to query
            url = f"{base_url.rstrip('/')}/service/lookup"
            try:
                async with sem:
                    resp = await client.get(url, params=params, timeout=timeout)
                if resp.status_code == 200:
                    # Expect JSON response
                    try:
                        ref.glutton = resp.json()
                    except ValueError:
                        ref.glutton = {"_error": "Invalid JSON from biblio-glutton"}
                else:
                    ref.glutton = {"_error": f"HTTP {resp.status_code}"}
            except httpx.HTTPError as e:
                ref.glutton = {"_error": str(e)}

        async with httpx.AsyncClient() as client:
            await asyncio.gather(*(fetch(client, r) for r in self.references))

        return self
    

    def summary(self):
        """Return a summary table of the references - what was extracted, and what was matched. Give feedback - checkmarks for matched references."""
        data = []
        for ref in self.references:
            matched = ref.glutton != None and not (isinstance(ref.glutton, dict) and '_error' in ref.glutton)
            # if not matched:
            #     print("No match for reference:", ref)
            # print("Glutton data:\n", ref.glutton)
            # print("-----")
            data.append({
                "DOI": ref.doi or "",
                "Title": (ref.title[:50] + '...') if ref.title and len(ref.title) > 50 else (ref.title or ""),
                "First Author Surname": ref.first_author_surname or "",
                "Raw": (ref.raw[:50] + '...') if ref.raw and len(ref.raw) > 50 else (ref.raw or ""),
                "Matched": "✅" if matched else "⚠️"
            })
        df = pd.DataFrame(data)
        return df





if __name__ == "__main__":
    async def main():
        verrific = Verrific()
        # verrific.process_pdf_dir("pdf")
        v = verrific.from_grobid_tei("tei/2012-an-open-large-scale-collaborative-effort-to-estimate-the-reproducibility-of-psychological-science.grobid.tei.xml")
        print(f"Extracted {len(v.references)} references.")
        await v.enrich_with_biblio_glutton()

        print("\nSummary:")
        print(v.summary())


    asyncio.run(main())