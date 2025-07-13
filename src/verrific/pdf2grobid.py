"""Original scienceverse/papercheck pdf2grobid module AI-translated to Python
Use your own Grobid server for production use."""
import os
import requests
import tempfile
from tenacity import retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _check_grobid_server(grobid_url):
    """Check if the grobid server is available."""
    try:
        response = requests.get(grobid_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"The grobid server {grobid_url} is not available, retrying: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _pdf_to_grobid_request(post_url, files, payload):
    """Send a request to the grobid server."""
    try:
        response = requests.post(post_url, files=files, data=payload)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed, retrying: {e}")
        raise

def pdf_to_grobid(filename, save_path=".", 
                  grobid_url="https://kermitt2-grobid.hf.space", # using the public Grobid server provided by Kermit2
                  start=-1, end=-1, 
                  consolidate_citations=0, 
                  consolidate_header=0, 
                  consolidate_funders=0):
    """
    Convert a PDF to Grobid XML.

    This function uses a public grobid server. You can set up your own local 
    grobid server following instructions from https://grobid.readthedocs.io/ 
    and set the argument `grobid_url` to its path (e.g., http://localhost:8070)

    Consolidation of citations, headers, and funders looks up these items in 
    CrossRef or another database to fix or enhance information (see 
    https://grobid.readthedocs.io/en/latest/Consolidation/). This can slow 
    down conversion. Consolidating headers is only useful for published papers, 
    and can be set to 0 for work in prep.

    :param filename: path to the PDF or a list of paths or a directory
    :param save_path: directory or file path to save to; set to None to save to a temp file
    :param grobid_url: the URL to the grobid server
    :param start: the first page of the PDF to read (defaults to -1 to read all pages)
    :param end: the last page of the PDF to read (defaults to -1 to read all pages)
    :param consolidate_citations: whether to fix/enhance citations
    :param consolidate_header: whether to fix/enhance paper info
    :param consolidate_funders: whether to fix/enhance funder info
    :return: path to the XML file or a list of paths
    """

    # Check if the grobid server is available
    try:
        _check_grobid_server(grobid_url)
    except Exception as e:
        print(f"The grobid server {grobid_url} is not available: {e}")
        return None

    # Handle list of files or a directory
    if isinstance(filename, list):
        if save_path and not os.path.isdir(save_path):
            print(f"Warning: {save_path} is not a directory. PDFs will be saved in the current working directory: {os.getcwd()}")
            save_path = "."
        
        xmls = []
        with tqdm(total=len(filename), desc="Processing PDFs") as pbar:
            for pdf in filename:
                try:
                    xml = pdf_to_grobid(pdf, save_path, grobid_url, start, end,
                                      consolidate_citations, consolidate_header,
                                      consolidate_funders)
                    xmls.append(xml)
                except Exception as e:
                    print(f"Error converting {pdf}: {e}")
                    xmls.append(None)
                pbar.update(1)
        
        errors = [f for f, x in zip(filename, xmls) if x is None]
        if errors:
            print(f"Warning: {len(errors)} of {len(xmls)} files did not convert: {', '.join(errors)}")
            
        return xmls

    elif os.path.isdir(filename):
        pdfs = [os.path.join(root, file) 
                for root, _, files in os.walk(filename) 
                for file in files if file.endswith(".pdf")]
        if not pdfs:
            print(f"Warning: There are no PDF files in the directory {filename}")
        return pdf_to_grobid(pdfs, save_path, grobid_url)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"The file {filename} does not exist.")

    with open(filename, 'rb') as f:
        files = {'input': f}
        payload = {
            'start': start,
            'end': end,
            'consolidateCitations': consolidate_citations,
            'consolidateHeader': consolidate_header,
            'consolidateFunders': consolidate_funders,
            'includeRawCitations': 1
        }
        post_url = f"{grobid_url}/api/processFulltextDocument"
        
        try:
            response = _pdf_to_grobid_request(post_url, files=files, payload=payload)
        except Exception as e:
            raise SystemError(f"Request failed after multiple retries: {e}")

    if save_path is None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as temp:
            temp.write(response.content)
            save_file = temp.name
    elif os.path.isdir(save_path):
        base = os.path.basename(filename)
        name, _ = os.path.splitext(base)
        save_file = os.path.join(save_path, f"{name}.xml")
    else:
        name, _ = os.path.splitext(save_path)
        save_file = f"{name}.xml"

    with open(save_file, 'wb') as f:
        f.write(response.content)

    return save_file
