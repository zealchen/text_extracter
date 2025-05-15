import unittest
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from doc_parser.docx_parser import DocxParser
from pathlib import Path


class TestDocxParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_test_docx_files()

    def test_section_parse_test1(self):
        parser = DocxParser(Path("test1.docx"))
        sections = parser.section_parse()

        self.assertGreaterEqual(len(sections), 2)
        # Check that Level 1 titles appear
        level1_titles = [s.title for s in sections if "Level 1" in s.title]
        self.assertGreaterEqual(len(level1_titles), 2)

        for section in sections:
            print(f"\n[test1] Title: {section.title}")
            print(f"[test1] Content: {section.content}")
            self.assertTrue(section.title.strip() or section.content.strip())

    def test_section_parse_test2(self):
        parser = DocxParser(Path("test2.docx"))
        sections = parser.section_parse()

        self.assertGreaterEqual(len(sections), 3)
        for section in sections:
            print(f"\n[test2] Title: {section.title}")
            print(f"[test2] Content: {section.content}")
            self.assertTrue(section.title.strip() or section.content.strip())

        # Optional: Check if centered bold text appears in titles (requires parser support)
        center_titles = [s.title for s in sections if "Centered Title" in s.title]
        self.assertGreaterEqual(len(center_titles), 3, "Expected at least 3 center-aligned titles to be recognized.")


if __name__ == '__main__':
    unittest.main()