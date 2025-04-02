## Dependencies

You can install the dependencies using the `requirements_segmentation.txt` file:

`pip install -r requirements_segmentation.txt`

## Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

`OPENAI_API_KEY="xxx"`

`OPENAI_BASE_URL="http://xxx.com/v1"`

> [!IMPORTANT]
> Make sure your LLM have a context big enogh for the input and output of the query

## Usage

1. Place your PDF files in the `input` folder.
2. Run the script:
   
`python 00_segmentation.py`

3. The processed markdown and JSON files will be saved in the `output` folder. This is an intermediate step before the final segmentation based on the llm output.

   <img width="1233" alt="Screenshot 2025-03-26 at 16 00 55" src="https://github.com/user-attachments/assets/5f90d565-b507-4370-a38c-c4753bab6ea3" />


4. Execute `01_index_creation_Lance.py` to generate the index, Langchain documents, and an Excel file containing chunks and metadata. This script processes markdown files in the input folder, using the LLM to create a JSON representation of the document structure. The script then employs this JSON, combined with fuzzy search, to reliably and consistently segment the document based on header locations. This approach contrasts with directly segmenting the contract using the LLM; instead, the LLM provides the document's structure, which a regex and fuzzy logic engine then use for segmentation.

5. The metadata structure is hard coded but it can be modified. The field that works for papers is Title, Abstract, keywords and Sections. If you work with constracts you can request Document type, parties and sections.

Happy programing!

