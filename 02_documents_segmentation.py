import os
import re
import json
from typing import List, Dict
from pydantic import BaseModel, Field
from rich.pretty import pprint

# Define the Section model using Pydantic
class Section(BaseModel):
    title: str = Field(description="Title of the section")
    content: str = Field(description="Complete text of the section")
    start_index: int = Field(description="Start index of the section in the document")
    end_index: int = Field(description="End index of the section in the document")

# Define the Layout model using Pydantic
class Layout(BaseModel):
    Title: str = Field(description="Title of the paper or document")
    Authors: List[str] = Field(description="List of authors as they are mentioned")
    Abstract: str = Field(description="Extract the Abstract of the paper as is or create a brief summary")
    Keywords: List[str] = Field(description="List of keywords as they are mentioned")
    OriginalSections: List[str] = Field(description="List of original section titles as they are mentioned, exclude main title")
    Sections: List[Section] = Field(description="List of sections titles, content, and boundaries")

# Function to structure a paper based on LLM output
def structured_paper(paper: str, llm_output: Dict) -> Dict:
    # Extract sections from LLM output
    sections = llm_output["Sections"]

    # Extract original sections from the paper text
    original_sections = []
    for line in paper.split('\n'):
        if line.strip().isupper():
            original_sections.append(line.strip())

    # Find the header by searching for the first line that starts with the section text
    header_content = ""
    for line in paper.split('\n'):
        if line.strip().startswith(original_sections[0]):
            break
        header_content += line + "\n"

    # Create regex patterns for each section
    section_patterns = {section: re.compile(re.escape(section), re.IGNORECASE) for section in original_sections}

    # Find indices of each section in the paper
    section_indices = []
    for section in original_sections:
        pattern = section_patterns[section]
        match = pattern.search(paper)
        if match:
            section_indices.append((section, match.start(), match.end()))

    # Sort section indices by start index
    section_indices.sort(key=lambda x: x[1])

    # Segment the document based on section indices
    segmented_sections = []
    if section_indices:
        # Add the header section
        segmented_sections.append(Section(
            title="Header",
            content=header_content.strip(),
            start_index=0,
            end_index=section_indices[0][1]
        ))

        # Add the rest of the sections in the correct order
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
    else:
        # If no sections are found, the entire document is the header
        segmented_sections.append(Section(
            title="Header",
            content=paper,
            start_index=0,
            end_index=len(paper)
        ))

    # Create the structured layout
    layout = Layout(
        Title=llm_output["Title"],
        Authors=llm_output["Authors"],
        Abstract=llm_output["Abstract"],
        Keywords=llm_output["Keywords"],
        OriginalSections=original_sections,
        Sections=segmented_sections
    )

    return layout.dict()

# Function to process documents in the output directory and export structured data
def process_documents(output_dir: str, export_dir: str):
    # Create export directory if it doesn't exist
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    # Process each markdown file in the output directory
    for filename in os.listdir(output_dir):
        if filename.endswith(".md"):
            md_file = os.path.join(output_dir, filename)
            json_file = os.path.join(output_dir, filename.replace(".md", ".json"))
            export_file = os.path.join(export_dir, filename.replace(".md", "_processed.json"))

            # Check if corresponding JSON file exists
            if os.path.exists(json_file):
                # Read the markdown file
                with open(md_file, "r") as f:
                    paper_text = f.read()

                # Read the JSON file
                with open(json_file, "r") as f:
                    llm_output = json.load(f)

                # Structure the paper
                structured_layout = structured_paper(paper_text, llm_output)

                # Write the structured layout to the export file
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
