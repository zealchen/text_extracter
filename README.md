# Document Parser CLI

A command-line tool to extract structured sections from documents like `.docx` and `.pdf`, and output them as structured JSON files.

---

## Features

- 📄 Supports `.docx` and `.pdf` input files
- 🧠 Automatically detects appropriate parser based on file extension
- 📂 Extracts titles, subtitles, and associated content
- 🧾 Outputs clean, hierarchical JSON

---

## Requirements

- Python 3.7+
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```sh
python cli.py --input_path <path_to_input_file_or_directory> --output_path <path_to_output_json>

```

## Output Format
```json
[
  {
    "title": "Introduction",
    "content": "This is the introduction content."
  },
  {
    "title": "Details",
    "content": "This section contains more detailed explanations."
  }
]
```
