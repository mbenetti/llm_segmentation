from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Dict, Tuple
import json
import instructor
import time
from tqdm import tqdm
import os
from datetime import datetime
import pymupdf4llm
from dotenv import load_dotenv
from fuzzywuzzy import process
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Define input and output folders
input_folder = "input"
output_folder = "output"
export_folder = "exports"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)
os.makedirs(export_folder, exist_ok=True)

# Define log file
log_file = os.path.join(export_folder, "processing_log.txt")

# Function to structure the paper content
def structured_paper(paper):
    class Layout(BaseModel):
        Title: str = Field(description="Title of the paper or document")
        Authors: List[str] = Field(description="List of authors as they are mentioned")
        Abstract: str = Field(description="Extract the Abstract of the paper as is or create a brief summary")
        Keywords: List[str] = Field(description="List of keywords as they are mentioned")
        Header: str = Field(description="All text content from the beginning of the document up to the start of the first identified section title.")
        Sections: List[Tuple[str, str]] = Field(description="List of sections. Each item is a tuple where the first element is the section title (header) and the second element is the complete text content of that section, excluding the title itself.")

    client = instructor.patch(
        OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY")
        ),
        mode=instructor.Mode.JSON,
    )

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": f"""
                Extract the following information from the document provided below:
                1. Title: The main title of the document.
                2. Authors: A list of author names.
                3. Abstract: The abstract section or a brief summary if no abstract exists.
                4. Keywords: A list of keywords, if mentioned.
                5. Header: All text content starting from the beginning of the document up to (but not including) the title/header of the very first section. This might include introductory paragraphs, affiliations, dates, etc., that appear before formal sections begin. If there's no text before the first section, return an empty string for the Header.
                6. Sections: A list of sections. For each section, provide its title (header) and its complete text content, EXCLUDING the title/header itself from the content. Return the sections as a list of tuples, where each tuple is (section_title, section_content_without_title).

                Document:
                {paper}
                """
            }
        ],
        response_model=Layout,
        max_retries=1
    )

    return Layout(
        Title=resp.Title,
        Authors=resp.Authors,
        Abstract=resp.Abstract,
        Keywords=resp.Keywords,
        Header=resp.Header, # Add this line
        Sections=resp.Sections
    )

# List all PDF files in the input folder
pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]

# List all already converted markdown files in the output folder
converted_files = {os.path.splitext(f)[0] for f in os.listdir(output_folder) if f.endswith('.md')}

# Process each PDF file
for pdf_file in pdf_files:
    base_name = os.path.splitext(pdf_file)[0]
    if base_name not in converted_files:
        pdf_path = os.path.join(input_folder, pdf_file)
        md_text = pymupdf4llm.to_markdown(pdf_path)

        # Define the output markdown file path
        md_file = base_name + '.md'
        md_path = os.path.join(output_folder, md_file)

        # Write the markdown text to the output file
        with open(md_path, 'w', encoding='utf-8') as md_file:
            md_file.write(md_text)

# Filter out already processed files
unprocessed_files = [
    f for f in os.listdir(output_folder) if f.endswith(".md")
    and not os.path.exists(os.path.join(output_folder, f.replace(".md", ".json")))
]
    
# Add progress bar
for file_name in tqdm(unprocessed_files, desc="Processing papers"):
    try:
        print(f"\nProcessing: {file_name}")
        file_path = os.path.join(output_folder, file_name)
        with open(file_path, "r") as file:
            content = file.read()

        response = structured_paper(content)

        json_file_path = os.path.join(output_folder, file_name.replace(".md", ".json"))
        with open(json_file_path, "w") as json_file:
            json_file.write(response.model_dump_json(indent=2))
    
        # --- Generate Excel file for the current document ---
        if response.Sections: # Check if Sections list is not empty
            try:
                current_file_sections = []
                for section_title, section_content in response.Sections:
                    current_file_sections.append({
                        "Title": section_title,
                        "Text": section_content
                    })
    
                if current_file_sections: # Ensure there's data before creating the file
                    df = pd.DataFrame(current_file_sections)
                    base_name = os.path.splitext(file_name)[0]
                    excel_file_name = f"{base_name}_sections.xlsx"
                    excel_file_path = os.path.join(export_folder, excel_file_name)
                    df.to_excel(excel_file_path, index=False, engine='openpyxl')
    
                    # Log successful Excel creation for this file
                    with open(log_file, "a") as log:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log.write(f"[{timestamp}] Successfully generated Excel file for {file_name}: {excel_file_path}\n")
                    print(f"Successfully created Excel file: {excel_file_path}")
                else:
                     # Log if no sections were extracted for this file, though response.Sections was not empty initially (edge case)
                    with open(log_file, "a") as log:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log.write(f"[{timestamp}] No section data extracted for Excel from {file_name}, although Sections list was present.\n")
    
    
            except Exception as e:
                # Log errors if Excel generation fails for this file
                with open(log_file, "a") as log:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log.write(f"[{timestamp}] Error generating Excel file for {file_name}: {str(e)}\n")
                print(f"\nError generating Excel file for {file_name}: {str(e)}")
        else:
            # Log if no sections were found in the response for this file
            with open(log_file, "a") as log:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log.write(f"[{timestamp}] No sections found in response for {file_name} to generate Excel file.\n")
    
        # Log successful processing
        with open(log_file, "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] Successfully processed: {file_name}\n")

        # Add delay between calls
        time.sleep(1)

    except Exception as e:
        # Log errors if they occur
        with open(log_file, "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] Error processing {file_name}: {str(e)}\n")

print("\nProcessing complete.")
