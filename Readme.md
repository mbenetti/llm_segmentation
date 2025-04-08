# Document Segmentation Script

<img width="1402" alt="Screenshot 2025-04-08 at 16 16 45" src="https://github.com/user-attachments/assets/fc726b46-6bbd-4780-a35f-0451dbed7f9a" />


This script processes PDF documents, converts them to Markdown, and then uses a Large Language Model (LLM) via the `instructor` library to extract structured information, including metadata and section content.

## Dependencies

Install the required Python packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

```dotenv
OPENAI_API_KEY="YOUR_API_KEY_HERE"
OPENAI_BASE_URL="YOUR_OPENAI_API_BASE_URL_HERE" # e.g., http://localhost:11434/v1 or https://api.openai.com/v1
OPENAI_MODEL="YOUR_MODEL_NAME_HERE" # e.g., llama3, gpt-4-turbo
```

> [!IMPORTANT]
> You can use your preferred OpenAI-compatible LLM endpoint. The code uses the `openai` library's client, which can be configured to point to various compatible APIs. Ensure the chosen LLM has a sufficiently large context window to handle the input document and the structured JSON output.

## Usage

1.  Place your PDF files in the `input` folder.
2.  Ensure your `.env` file is correctly configured with your API key, base URL, and model name.
3.  Run the script:

    ```bash
    python segmentation.py
    ```

4.  **Output:**
    *   For each PDF in `input`, a corresponding Markdown file (`.md`) will be created in the `output` folder (if it doesn't already exist).
    *   For each Markdown file in `output` that hasn't been processed yet, a corresponding JSON file (`.json`) containing the structured data extracted by the LLM will be created in the `output` folder.
    *   A log file (`exports/processing_log.txt`) tracks the processing status and any errors.

## Extracted Data Structure

The script instructs the LLM to extract the following fields, which are saved in the output JSON file:

*   `Title`: The main title of the document.
*   `Authors`: A list of author names.
*   `Abstract`: The abstract section or a brief summary.
*   `Keywords`: A list of keywords, if mentioned.
*   `Header`: All text content from the beginning of the document up to the start of the first identified section title.
*   `Sections`: A list of tuples. Each tuple contains:
    *   The section title (string).
    *   The full text content of that section, excluding the title itself (string).

This structure is defined using Pydantic in the `segmentation.py` script and can be modified to suit different document types (e.g., contracts, reports) by changing the `Layout` model and the LLM prompt.

Happy programming!

