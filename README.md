\# edu\_diff\_engine



A research-grade engine for \*\*relative difficulty–controlled question generation\*\* from PDFs using LLMs.



This library reads a PDF chapter or document, dynamically builds a \*\*local difficulty rubric\*\* (levels 1–5 based on context), and generates MCQs targeted to a desired difficulty and cognitive skill profile.



\## Key Features

\- Dynamic rubric generation using Groq API

\- External question generation using user-selected LLMs (OpenAI, Groq, Gemini, etc.)

\- Relative difficulty scale based on PDF content

\- Cognitive skill scoring (memory, reasoning, numerical, language)

\- PDF extraction using pdfplumber

\- Command-line interactive usage

\- No API keys stored — provided at runtime for safety

\- Future: Streamlit UI for LogiQ integration



\## Quickstart (Development)



```bash

git clone https://github.com/nilparadox/edu\_diff\_engine.git

cd edu\_diff\_engine

python -m venv .venv

.\\.venv\\Scripts\\activate

pip install -r requirements.txt



