# Legal knowledge base

`sources/sample_india.json` contains **short paraphrased SAMPLE entries so the pipeline runs end-to-end.
They are not authoritative.** Before relying on any output, replace them with verified text from
official sources (India Code, MeitY, court websites) and set `"verified": true` plus the correct `version`
and `effective_date`.

Load with (from `backend/`):

    python -m app.scripts.ingest_legal ../knowledge_base/sources/*.json
