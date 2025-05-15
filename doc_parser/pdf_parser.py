#!/usr/bin/env python
import json
import pymupdf
import sys
import math
from typing import List
from doc_parser.parser import DocParser
from doc_parser.parser import Section
from pydantic import BaseModel, Field
from pymupdf import Document, Page


class PageMargin(BaseModel):
    """
    Represents the left, right, and center margin positions of a PDF page.
    """
    left: float
    right: float
    center: float = Field(default=0, init=False)

    def model_post_init(self, __context):
        self.center = (self.left + self.right) / 2
        
    def __str__(self):
        return f"left: {self.left}, center: {self.center}, right: {self.right}"


class SpanStyle(BaseModel):
    """
    Represents the style of a text span, including size, font, and formatting flags.
    """
    size: int
    flags: int
    font: str

    def __eq__(self, other):
        return self.size == other.size and self.flags == other.flags and self.font == other.font


def is_title(span_pos_x0, span_pos_x1, page_margin: PageMargin, span: SpanStyle, body: SpanStyle):
    """
    Heuristically determine whether a span of text is likely a section title.
    Criteria include:
    - Not full-width (not covering both left and right margins)
    - Center-aligned and has a different font from body text
    - Or is left-aligned and significantly larger than body text
    """
    span_center = math.floor((span_pos_x1 + span_pos_x0) / 2)
    if span_pos_x0 <= page_margin.left * 1.05 and span_pos_x1 >= page_margin.right * 0.95:
        return False  # Skip full-width spans
    if span_pos_x0 > page_margin.left * 1.05 and \
        span_center >= page_margin.center * 0.95 and \
        span_center <= page_margin.center * 1.05 and \
        span.font != body.font:
        return True  # Likely a center-aligned title with different font
    elif span_pos_x0 <= page_margin.left * 1.05 and span.size > body.size + 2:
        return True  # Likely a larger font on the left side
    else:
        return False


def get_page_margin(page: Page):
    """
    Calculate the leftmost and rightmost x-coordinates from all spans on the page.
    Returns a PageMargin object with left, right, and center.
    """
    position_stat = {
        "leftmost_pos_x": sys.maxsize,
        "rightmost_pos_x": 0,
        "center": 0
    }

    text_dict = page.get_text("dict")
    blocks = text_dict["blocks"]
    blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if span["bbox"][0] < position_stat['leftmost_pos_x']:
                    position_stat['leftmost_pos_x'] = span["bbox"][0]
                if span["bbox"][2] > position_stat['rightmost_pos_x']:
                    position_stat['rightmost_pos_x'] = span["bbox"][2]
    return PageMargin(
        left=position_stat['leftmost_pos_x'],
        right=position_stat['rightmost_pos_x']
    )


def get_body_style(doc) -> SpanStyle:
    """
    Estimate the most common span style in the entire document, 
    assumed to be the body text style.
    """
    style_stat = {}

    for page in doc:
        text_dict = page.get_text("dict")
        blocks = text_dict["blocks"]
        blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    key = "{}&{}&{}".format(span["size"], span["flags"], span["font"])
                    if key not in style_stat:
                        style_stat[key] = 0
                    style_stat[key] += len(span["text"])
    style_stat = sorted(style_stat.items(), key=lambda item: item[1], reverse=True)

    size, flags, font = style_stat[0][0].split('&')
    return SpanStyle(
        size=int(float(size)), flags=int(flags), font=font)


def first_non_null_span(line):
    """
    Return the first span in a line that contains non-empty text.
    Used to determine visual positioning.
    """
    for span in line["spans"]:
        if span["text"].strip():
            return span
    return None


class PDFParser(DocParser):
    """
    A custom parser for PDF documents that extracts structured sections
    based on text layout and style heuristics.
    """
    def section_parse(self) -> List[Section]:
        doc: Document = pymupdf.open(self.file_path)
        
        # Determine the most common text style, assumed to be the body text
        body_style: SpanStyle = get_body_style(doc)
        # Initialize a list to store all extracted sections
        sections: List[Section] = []

        for page in doc:
            last_line_pos_y0 = -1  # Tracks vertical position of the previous line
            page_margin = get_page_margin(page)  # Compute left/right/center margins
            text_dict = page.get_text("dict")
            blocks = text_dict["blocks"]
            # Sort blocks top-down, left-right
            blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))

            for b_index, block in enumerate(text_dict["blocks"]):            
                for line in block.get("lines", []):
                    
                    # Find the first span with non-empty text to analyze layout
                    first_span = first_non_null_span(line)
                    if not first_span or first_span["bbox"][0]  > page_margin.center:
                        continue  # Skip empty or far-right aligned lines (e.g., right aligned header)
                    
                    # Extract span horizontal and vertical positions
                    first_span_pos_x0 = int(first_span["bbox"][0])
                    first_span_pos_x1 = int(first_span["bbox"][2])
                    first_span_pos_y0 = int(first_span["bbox"][1])
                    
                    # Determine if this line starts at a new vertical position (new line)
                    if last_line_pos_y0 == -1 or int(last_line_pos_y0) != int(first_span_pos_y0):
                        is_new_line = True
                    else:
                        is_new_line = False
                    last_line_pos_y0 = first_span["bbox"][1]
                    
                    # Construct the current span's style
                    span_style = SpanStyle(size=int(first_span["size"]), flags=int(first_span["flags"]), font=first_span["font"])
                    if span_style == body_style:
                        # If the style matches the body text, treat as content
                        if not sections:
                            continue
                        for span in line["spans"]:
                            if span["text"].strip():
                                sections[-1].content += span["text"]
                    elif is_new_line and is_title(first_span_pos_x0, first_span_pos_x1, page_margin, span_style, body_style):
                        # If the style and position heuristically indicate a title
                        if not sections or sections[-1].content:
                            sections.append(Section())
                        for span in line["spans"]:
                            if span["text"].strip():
                                sections[-1].title += span["text"]
                    else:
                        # Style does not match body or title, still treat as body content
                        if not sections:
                            continue  # Ignore stray text before any section
                        for span in line["spans"]:
                            if span["text"].strip():
                                sections[-1].content += span["text"]
                                
        sections = [item for item in sections if item.content != '']
        return sections
