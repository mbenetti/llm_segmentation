#%% # Dependencies
import json
import os
from fuzzywuzzy import fuzz
from langchain.docstore.document import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain.vectorstores import LanceDB
import lancedb
import pandas as pd

#%% # Ollama Configuration
# OLLAMA_BASE_URL = "http://mtm-llm-uk.uksouth.cloudapp.azure.com:11435/"
# OLLAMA_MODEL = "bge-m3:567m-fp16"

OLLAMA_BASE_URL = "http://localhost:11434/"
OLLAMA_MODEL = "bge-m3"

embeddings = OllamaEmbeddings(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

#%% # Function to find the best match for a section title
def find_best_match(title, lines, start_line):
    if title is None:
        return None
    best_match = None
    best_score = 0
    for i in range(start_line, len(lines)):
        line = lines[i].strip()
        score = fuzz.ratio(title, line)
        if score > best_score and score >= 90:
            best_score = score
            best_match = i
    return best_match

#%% Simple metadata
def simplify_json_metadata(json_data):
    metadata = {}

    # Simplify Title
    metadata['Title'] = json_data.get('Title', '')

    # Simplify Authors
    authors = json_data.get('Authors', [])
    metadata['Authors'] = ', '.join(authors)

    # Simplify Abstract
    metadata['Abstract'] = json_data.get('Abstract', '')

    # Simplify Keywords
    keywords = json_data.get('Keywords', [])
    metadata['Keywords'] = ', '.join(keywords)

    # Simplify Sections
    sections = json_data.get('Sections', [])
    metadata['Sections'] = ', '.join(sections)

    return metadata

#%% # Function to process a single document
def process_document(document_title, markdown_lines, sections, metadata):  # Add metadata parameter
    documents = []
    previous_match_line = 0

    # Check for text before the first section
    if sections:
        first_section_title = sections[0]
        first_section_match_line = find_best_match(first_section_title, markdown_lines, previous_match_line)
        if first_section_match_line is not None:
            section_text = ''.join(markdown_lines[previous_match_line:first_section_match_line])
            if section_text.strip():  # Ensure there is text before the first section
                chunk_metadata = {
                    "section_title": "Document_header",
                    "document_title": document_title,
                    "Authors": metadata.get('Authors', '')  # Add authors
                }
                documents.append(Document(page_content=section_text, metadata=chunk_metadata))
                previous_match_line = first_section_match_line


    # Process the rest of the sections
    for i, section_title in enumerate(sections):
        next_section_title = sections[i + 1] if i + 1 < len(sections) else None
        current_section_match_line = find_best_match(section_title, markdown_lines, previous_match_line)
        if current_section_match_line is not None:
            next_section_match_line = find_best_match(next_section_title, markdown_lines, current_section_match_line) if next_section_title else None
            if next_section_match_line is not None:
                section_text = ''.join(markdown_lines[current_section_match_line:next_section_match_line])
            else:
                section_text = ''.join(markdown_lines[current_section_match_line:])

            if section_text.strip():  # Ensure there is text in the section
                chunk_metadata = {
                    "section_title": section_title,
                    "document_title": document_title,
                    "Authors": metadata.get('Authors', '')  # Add authors
                }
                documents.append(Document(page_content=section_text, metadata=chunk_metadata))
                previous_match_line = next_section_match_line if next_section_match_line else current_section_match_line

    return documents

#%% # Function to process all documents in the output folder
def process_all_sections(output_folder):
    all_sections = []

    # Iterate over all JSON files in the output folder
    for filename in os.listdir(output_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(output_folder, filename)
            markdown_path = os.path.join(output_folder, filename.replace('.json', '.md'))

            # Skip if markdown file doesn't exist
            if not os.path.exists(markdown_path):
                print(f"Warning: Markdown file not found for {filename}, skipping...")
                continue

            # Load JSON file
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Load markdown file
            with open(markdown_path, 'r') as f:
                markdown_lines = f.readlines()

            # Initialize variables
            document_title = data['Title']
            sections = data['Sections']
            metadata = simplify_json_metadata(data)

            # Process the document
            documents = process_document(document_title, markdown_lines, sections, metadata)  # Pass metadata
            all_sections.extend(documents)

    return all_sections

#%% # Function to process all documents and abstract and create vector store
def process_all_abstract(output_folder):
    all_abstract = []

    # Iterate over all JSON files in the output folder
    for filename in os.listdir(output_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(output_folder, filename)

            # Load JSON file
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Extract abstract and metadata
            abstract = data.get('Abstract', '')
            metadata = simplify_json_metadata({k: v for k, v in data.items() if k != 'Abstract'})
            # Create document
            if abstract.strip():  # Ensure there is text in the abstract
                all_abstract.append(Document(page_content=abstract, metadata=metadata))

    return all_abstract




#%% # Process all_sections in the output folder
all_sections = process_all_sections('output')
all_abstract = process_all_abstract('output')

# from rich.pretty import pprint
# all_sections = process_all_sections('test')
# all_abstract = process_all_abstract('test')
# print("All Sections")
# pprint (all_sections)
# print("All Abstracts")
# pprint(all_abstract)

# Process all_sections and all_abstract
all_sections = process_all_sections('output')
all_abstract = process_all_abstract('output')


# Save all_sections to a JSON file
with open('all_sections.json', 'w') as f:
    json.dump([doc.dict() for doc in all_sections], f, indent=4)

# Save all_abstract to a JSON file
with open('all_abstract.json', 'w') as f:
    json.dump([doc.dict() for doc in all_abstract], f, indent=4)



# Convert sections to DataFrame and save to Excel
sections_data = [
    {
        'document_title': doc.metadata['document_title'],
        'section_title': doc.metadata['section_title'],
        'Authors': doc.metadata['Authors'],
        'content': doc.page_content
    } for doc in all_sections
]
sections_df = pd.DataFrame(sections_data)
sections_df.to_excel('sections_output.xlsx', index=False)

# Convert abstracts to DataFrame and save to Excel
abstracts_data = [
    {
        'Title': doc.metadata['Title'],
        'Authors': doc.metadata['Authors'],
        'Keywords': doc.metadata['Keywords'],
        'Abstract': doc.page_content
    } for doc in all_abstract
]
abstracts_df = pd.DataFrame(abstracts_data)
abstracts_df.to_excel('abstracts_output.xlsx', index=False)


#%%
# Initialize LanceDB
db = lancedb.connect('lance_db')

# Create embeddings and Lance collections for sections
try:
    print("Embeddings initialized successfully for sections")
    section_collection = LanceDB.from_documents(
        documents=all_sections,
        embedding=embeddings,
        connection=db,
        table_name="sections"
    )
    print("Lance collection created successfully for sections")
    
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    print(f"Error details: {str(e)}")

# Create embeddings and Lance collections for abstracts
try:
    print("Embeddings initialized successfully for abstracts")
    abstract_collection = LanceDB.from_documents(
        documents=all_abstract,
        embedding=embeddings,
        connection=db,
        table_name="abstracts"
    )
    print("Lance collection created successfully for abstracts")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
    print(f"Error details: {str(e)}")


# Process all_abstract in the output folder
all_abstract = process_all_abstract('output')


# %%
