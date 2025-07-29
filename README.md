# FastAPI Project

## Project Structure

```
chauffeur/
├── app/
│   ├── __init__.py
│   └── routes.py
├── main.py
├── requirements.txt
└── README.md
```

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the FastAPI app:
   ```bash
   uvicorn main:app --reload
   ```
3. Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

- Root endpoint: `/`
- Example endpoint: `/hello` 