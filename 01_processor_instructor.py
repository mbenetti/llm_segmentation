#%%
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Dict
import json
import instructor
import time
from tqdm import tqdm

def structured_paper(paper):
    class Layout(BaseModel):
        Title: str = Field(description="Title of the paper or document")
        Authors: List[str] = Field(description="List of authors as they are mentioned")
        Abstract: str = Field(description="Extract the Abstract of the paper as is or create a breaf summary")
        Keywords: List[str] = Field(description="List of keywords as they are mentioned")
        Sections: List[str] = Field(description="List of sections title base on the layout and content")

    client = instructor.patch(
        OpenAI(
            base_url="https://codestral.mistral.ai/v1",
            api_key = "K4WxjJyPfHirNaydm99Cdja8duqVbica"
        ),
        mode=instructor.Mode.JSON,
    )

    resp = client.chat.completions.create(
        model="codestral-latest",
        temperature = 0,
        messages=[
            {
                "role": "user",
                "content": f""" 
                Return the extracted information from this docuemnt: 
                {paper}.
                """
            }
        ],
        response_model=Layout,
        max_retries=1
    )
    return resp

#%%
import os
from datetime import datetime

output_folder = "output"
export_folder = "exports"
log_file = os.path.join(export_folder, "processing_log.txt")

output_files = [f for f in os.listdir(output_folder) if f.endswith(".md")]

# Filter out already processed files
unprocessed_files = [
    f for f in output_files 
    if not os.path.exists(os.path.join(output_folder, f.replace(".md", ".json")))
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
