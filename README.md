# OpenFDA Drug Recall Assistant 💊

A specialized AI assistant that helps users query the FDA Drug Enforcement (Recalls) database efficiently. Built with the **OpenAI Responses API** for stateful conversations and **Streamlit** for the UI.

## Features

- 🔍 **Smart Search**: Find recalls by product name, reason, or year.
- 📊 **Statistics**: Get summaries of recalls by classification, status, and top recalling firms.
- 🧠 **Context Aware**: Remembers conversation history (e.g., "Tell me more about the first one").
- 🛡️ **Guardrails**: Strictly dedicated to FDA data; refuses off-topic queries.
- 🔗 **Citations**: Always links to the OpenFDA source.

## Tech Stack

- **OpenAI Responses API**: Leveraging the latest API for implicit state management (`previous_response_id`) and tool orchestration.
- **Streamlit**: Single-page application logic and UI.
- **Pydantic**: Robust data validation and schema generation.
- **OpenFDA API**: Real-time recall data.

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd curium-assignment
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=sk-...
   ```
   *(Optional)* Define `OPENFDA_API_URL` if you need to override the default endpoint.

## Usage

Run the application:
```bash
streamlit run main.py
```

## Tools Implemented

The assistant has access to two core tools:

1.  **`search_recalls`**
    *   Finds recalls matching a query string, specific classification (Class I, II, III), or year.
    *   Returns normalized, clean data objects.

2.  **`get_recall_stats`**
    *   Aggregates data to show total counts, breakdowns by classification, and top 5 recalling firms.

## Project Structure

```
.
├── main.py              # Application entry point (Streamlit UI + Agent logic)
├── tools.py             # Tool execution and API orchestration
├── function_schemas.py  # Pydantic models for data validation
├── openfda/
│   ├── client.py        # HTTP client for OpenFDA API
│   └── transforms.py    # Data cleaning and normalization
└── requirements.txt
```

## Example Queries

*   "Show me recent Class I drug recalls."
*   "What are the top firms with the most recalls?"
*   "Find recalls for ibuprofen."
*   "How many recalls happened in 2023?"
