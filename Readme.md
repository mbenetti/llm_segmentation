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
   
`python 03_segmentation.py`

3. The processed markdown and JSON files will be saved in the `output` folder. This is an intermediate step before the final segmentation based on the llm output

4. Run the script `01_index_creation_Lance.py` to create the index, and two output files, the langchain documents and an excel file with the chuncks and metadata.

The metadata is hard coded but it can be modified.

