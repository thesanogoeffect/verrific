import pytest
from verrific.pdf2grobid import pdf_to_grobid
from lxml import etree
import os

def test_pdf2grobid_returns_valid_xml(grobid_url, tmp_path):
    # Test the pdf2grobid function with a sample PDF file
    pdf_path = "tests/assets/kelders-et-al-2024.pdf"
    save_file = tmp_path / "grobid_test_result.xml"
    result_path = pdf_to_grobid(pdf_path, grobid_url=grobid_url, consolidate_citations=True, save_path=str(save_file))

    # assert the result is not None
    assert result_path is not None, "The result should not be None"

    # assert the result is a string and the file exists
    assert isinstance(result_path, str), "The result should be a string"
    assert os.path.exists(result_path)

    # parse the result as XML
    try:
        # Use a parser that can recover from errors
        parser = etree.XMLParser(recover=True)
        etree.parse(result_path, parser)
    except etree.XMLSyntaxError as e:
        pytest.fail(f"Result is not valid XML: {e}")


# def test_pdf2grobid_content(grobid_url, tmp_path):
#     # Test the content of the XML returned by pdf2grobid
#     pdf_path = "tests/assets/kelders-et-al-2024.pdf"
#     save_file = tmp_path / "grobid_test_result.xml"
#     result_path = pdf_to_grobid(pdf_path, grobid_url=grobid_url, consolidate_citations=True, save_path=str(save_file))

#     # Load the XML content
#     with open(result_path, 'r', encoding='utf-8') as file:
#         xml_content = file.read()

#     # Check if the XML contains expected elements
#     assert "<teiCorpus" in xml_content, "The XML should contain a <teiCorpus> element"
#     assert "<text>" in xml_content, "The XML should contain a <text> element"
#     assert "<title>" in xml_content, "The XML should contain a <title> element"