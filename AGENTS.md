## Cursor Cloud specific instructions

**Product**: ElectroStore FAQ Chatbot — a Streamlit-based Vietnamese FAQ chatbot using custom TF-IDF vectorization and ChromaDB for semantic search over 8 hardcoded FAQ entries.

**Architecture**: Single-process Python app (4 source files). No external services, databases, or APIs required. ChromaDB runs in-process as an embedded persistent client.

### Running the app

```bash
streamlit run app.py --server.headless true --server.port 8501
```

The app serves on `http://localhost:8501`. See `README.md` for standard setup/run instructions.

### Notes

- No automated tests or linter configuration exist in this repo.
- `~/.local/bin` must be on `PATH` for `streamlit` CLI (pip installs scripts there).
- ChromaDB telemetry warnings in the console (e.g. `Failed to send telemetry event`) are harmless — telemetry is disabled via `Settings(anonymized_telemetry=False)`.
- The `chroma_storage/` directory is created at runtime next to `app.py`; it is ephemeral and rebuilt on each app start.
