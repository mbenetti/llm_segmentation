import os
import re
import json
from typing import List, Dict
from pydantic import BaseModel, Field
from rich.pretty import pprint

class Section(BaseModel):
    title: str = Field(description="Title of the section")
    content: str = Field(description="Complete text of the section")
    start_index: int = Field(description="Start index of the section in the document")
    end_index: int = Field(description="End index of the section in the document")

class Layout(BaseModel):
    Title: str = Field(description="Title of the paper or document")
    Authors: List[str] = Field(description="List of authors as they are mentioned")
    Abstract: str = Field(description="Extract the Abstract of the paper as is or create a brief summary")
    Keywords: List[str] = Field(description="List of keywords as they are mentioned")
    OriginalSections: List[str] = Field(description="List of original section titles as they are mentioned")
    Sections: List[Section] = Field(description="List of sections with their titles, content, and boundaries")

def structured_paper(paper: str, llm_output: Dict) -> Dict:
    sections = llm_output["Sections"]
    section_patterns = {section: re.compile(re.escape(section), re.IGNORECASE) for section in sections}

    section_indices = []
    for section in sections:
        pattern = section_patterns[section]
        match = pattern.search(paper)
        if match:
            section_indices.append((section, match.start(), match.end()))

    # Sort section indices by start index
    section_indices.sort(key=lambda x: x[1])

    # Segment the document based on section indices
    segmented_sections = []
    for i, (section, start_index, end_index) in enumerate(section_indices):
        if i < len(section_indices) - 1:
            next_section_start_index = section_indices[i + 1][1]
        else:
            next_section_start_index = len(paper)

        content = paper[start_index:next_section_start_index].strip()
        segmented_sections.append(Section(
            title=section,
            content=content,
            start_index=start_index,
            end_index=next_section_start_index
        ))

    # Create the structured layout
    layout = Layout(
        Title=llm_output["Title"],
        Authors=llm_output["Authors"],
        Abstract=llm_output["Abstract"],
        Keywords=llm_output["Keywords"],
        OriginalSections=sections,
        Sections=segmented_sections
    )

    return layout.dict()

def process_documents(output_dir: str, export_dir: str):
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    for filename in os.listdir(output_dir):
        if filename.endswith(".md"):
            md_file = os.path.join(output_dir, filename)
            json_file = os.path.join(output_dir, filename.replace(".md", ".json"))
            export_file = os.path.join(export_dir, filename.replace(".md", "_processed.json"))

            if os.path.exists(json_file):
                with open(md_file, "r") as f:
                    paper_text = f.read()

                with open(json_file, "r") as f:
                    llm_output = json.load(f)

                structured_layout = structured_paper(paper_text, llm_output)

                with open(export_file, "w") as f:
                    json.dump(structured_layout, f, indent=4)

                print(f"Processed and saved: {export_file}")
            else:
                print(f"JSON file not found for: {md_file}")

# Define the output directory and export directory
output_dir = "output"
export_dir = "exports"

# Process all documents in the output directory and export to the export directory
process_documents(output_dir, export_dir)