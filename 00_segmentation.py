#%%
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
import json
import instructor
import time
from tqdm import tqdm
import os
from datetime import datetime
import pymupdf4llm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define input and output folders
input_folder = "input"
output_folder = "output"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Define log file
log_file = os.path.join(output_folder, "processing_log.txt")

# Function to structure the paper content
def structured_paper(paper):
    class Layout(BaseModel):
        Title: str = Field(description="Title of the paper or document")
        Authors: List[str] = Field(description="List of authors as they are mentioned")
        Abstract: str = Field(description="Extract the Abstract of the paper as is or create a brief summary")
        Keywords: List[str] = Field(description="List of keywords as they are mentioned")
        Sections: List[str] = Field(description="Title of every section of the paper. Decide what a section is based on the amount of text and if it makes sense to break the document there")

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
                Return the extracted information from this document:
                {paper}.
                """
            }
        ],
        response_model=Layout,
        max_retries=1
    )
    return resp

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

# %%
