#!/usr/bin/env python
import json
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field
from typing import List


class FileType(Enum):
    JSON = "json"


class Hierarchy(BaseModel):
    level: int = Field(..., ge=0, description="indent level")
    text: str = Field(..., description="text in one paragraph")
    indent: int = Field(..., description="indent of the text")
    style: str = Field(default="", description="text in one paragraph")


class Section(BaseModel):
    title: str = ""
    content: str = ""


class DocParser:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def section_parse(self) -> List[Section]:
        raise NotImplementedError

    def parse_and_dump(self, output_path: Path, file_type=FileType.JSON):
        output_path = Path(output_path)
        output_path_parent = output_path.parent.absolute()
        output_path_parent.mkdir(parents=True, exist_ok=True)
        result = self.section_parse()
        if file_type == FileType.JSON:
            result = [item.model_dump() for item in result]
            with open(output_path, 'w') as fp:
                json.dump(result, fp, indent=4)
