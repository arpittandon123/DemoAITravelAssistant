# AI Travel Planning Assistant (Singapore)



An intelligent, context-aware travel assistant combining \*\*Document-based Retrieval-Augmented Generation (RAG)** with real-time **Model Context Protocol (MCP)** tool execution.



Developed using **LangChain**, **ChromaDB**, **HuggingFace Embeddings**, and **Streamlit**.



---



## 🏗️ System Architecture



1\. **Vector Knowledge Base (RAG)**:

&#x20;  - **Ingestion**: Parses `.txt` and `.pdf` travel guides using `DirectoryLoader` and `PyPDFLoader`.

&#x20;  - **Chunking**: Uses `RecursiveCharacterTextSplitter` (chunk size: 500, overlap: 80).

&#x20;  - **Embeddings**: Employs open-source `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace.

&#x20;  - **Vector Store**: Persisted locally in `ChromaDB` (`./chroma\_db`).



2\. **Real-Time MCP Tools**:

&#x20;  - **Weather MCP Server**: Queries live forecast API (`Open-Meteo`) for temperature, rainfall probabilities, and weather conditions.

&#x20;  - **Currency MCP Server**: Queries live exchange rate API (`ExchangeRate-API`) for international currency conversion.



3\. **LLM Orchestration & Reasoning**:

&#x20;  - **Default Model**: Built on LangChain adapters using **Ollama** (`llama3.1` / `ChatOllama`) for local processing and reasoning.
&#x20;  - **OpenAI Fallback/Alternative**: Code for OpenAI `gpt-4o` integration (`ChatOpenAI`) is provided in `agent.py` as commented lines. It can be instantly enabled whenever an `OPENAI_API_KEY` is available.



=---



## 🛠️ Installation \& Setup Instructions



### 1. Prerequisites

Ensure you have Python 3.10+ installed.

Clone or download the repo from https://github.com/arpittandon123/DemoAITravelAssistant

### 2. Setup Ollama

- Download and Install Ollama
- Pull the model
```
ollama pull llama3.1
```
- Run the model
```
ollama run llama3.1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Build Vector Store (Ingest Data)

```
python ingest.py
```

### 4. Launch Application UI

```
streamlit run app.py
```
