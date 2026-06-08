# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

I chose Georgia State University's (GSU) Computer Science department professor reviews. My source is from the Rate My Professors website. Students often depend on unofficial sources when choosing courses because they provide information about professors' teaching style, exam difficulty, workload, and grading policies that official university sources fail to provide. This project makes those student reviews accessible through a searchable, AI-powered system that answers plain-English questions and cites the original review sources in every response.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors | Professor Mohammed Alser reviews | https://www.ratemyprofessors.com/professor/3126576 |
| 2 | Rate My Professors | Professor Ashwin Ashok reviews | https://www.ratemyprofessors.com/professor/2688463 |
| 3 | Rate My Professors | Professor Bal Abdullah reviews | https://www.ratemyprofessors.com/professor/2942443 |
| 4 | Rate My Professors | Professor Xie Bingyi reviews | https://www.ratemyprofessors.com/professor/2906245 |
| 5 | Rate My Professors | Professor Esra Akbas reviews | https://www.ratemyprofessors.com/professor/3006294 |
| 6 | Rate My Professors | Professor S M Towhidul Islam reviews | https://www.ratemyprofessors.com/professor/2921056 |
| 7 | Rate My Professors | Professor William Johnson reviews | https://www.ratemyprofessors.com/professor/2329806 |
| 8 | Rate My Professors | Professor Gao Lan reviews | https://www.ratemyprofessors.com/professor/3075860 |
| 9 | Rate My Professors | Professor Mahfuzur Rahman reviews | https://www.ratemyprofessors.com/professor/2519939 |
| 10 | Rate My Professors | Professor Tushara Sadasivuni reviews | https://www.ratemyprofessors.com/professor/2317655 |
| 11 | Rate My Professors | Professor Saliesh Kumar reviews | https://www.ratemyprofessors.com/professor/2524563 |
| 12 | Rate My Professors | Professor Hosseini Roya reviews | https://www.ratemyprofessors.com/professor/2723447 |

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Why these choices fit your documents:**

Student reviews are short, opinionated, and loosely structured — rarely longer than a few sentences per point. A 500-character chunk is large enough to contain one complete student thought (such as a comment about attendance policy plus its supporting context) while staying focused enough for semantic search to match it precisely against a query.

The 100-character overlap ensures that details spanning two sentences are not lost at chunk boundaries. For example, a review might mention a professor's name at the end of one sentence and describe their grading policy at the start of the next — with no overlap, one chunk would miss part of that connection. If chunks were too small, complete thoughts would be cut off and retrieval would return fragments. If too large, unrelated opinions (exam difficulty and office hours, for instance) would merge into one chunk and dilute the semantic signal, making it harder for ChromaDB to match the right chunk to a specific query.

**Preprocessing before chunking:** Each `.txt` file was run through a cleaning function that removed HTML tags, HTML entities (`&amp;`, `&nbsp;`, etc.), URLs, and Rate My Professors UI boilerplate strings such as "Submit a Correction," "Flag this professor," "Overall Quality," and "Would Take Again." Whitespace was normalized before splitting.

**Final chunk count:** Approximately 150–180 chunks across 12 documents (varies slightly depending on document length per professor).

---

## Sample Chunks

The following are 5 representative chunks selected from the final `chunks.json` file, showing the source document name and chunk index for each.

**Chunk 1** — `prof_Bal.txt` (chunk_index: 0)
```
Professor Bal requires attendance — you MUST attend class. Missing even one session
can affect your grade significantly. The workload isn't that difficult, but the
material can be if you're not attending. A few exams, a few quizzes, a few homeworks.
```

**Chunk 2** — `prof_Islam.txt` (chunk_index: 2)
```
Professor Islam explains every concept step by step and makes sure you understand
before moving on. He is very patient and never makes you feel bad for asking
questions. Best professor I've had for CSC 2720. Highly recommend for Data Structures.
```

**Chunk 3** — `prof_Johnson.txt` (chunk_index: 1)
```
William Johnson is one of the best professors in the CS department. His lectures are
engaging, his grading is fair, and he genuinely cares about student success. Exams
are based on lecture slides — study those and you'll do well.
```

**Chunk 4** — `prof_Alser.txt` (chunk_index: 3)
```
Professor Alser is fair and lenient in grading. He gives partial credit and is open
to re-grades if you have a valid concern. One of the best professors I have ever had
at GSU. Very caring and genuinely concerned about student learning.
```

**Chunk 5** — `prof_Sadasivuni.txt` (chunk_index: 0)
```
This class WILL be hard for you. Tushara assigns a heavy workload — multiple projects,
frequent assignments, and fast-paced lectures. Not recommended if you have a full
course load. But you learn a lot if you put in the work.
```

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` from the `sentence-transformers` library. This model runs entirely locally with no API key, no rate limits, and no cost. It produces 384-dimensional dense vectors and performs well on short, opinion-based texts like student reviews. Its 256-token context window is sufficient for 500-character review chunks.

**Production tradeoff reflection:**

In a real university deployment serving many students, I would evaluate several factors before choosing a different model:

- **Accuracy on domain-specific text:** `all-MiniLM-L6-v2` is a general-purpose model. A larger model like `text-embedding-3-large` (OpenAI) or `e5-large-v2` would likely return more precise matches on nuanced review language, particularly for queries where the relevant information is phrased very differently from the query itself.
- **Context length:** MiniLM handles up to 256 tokens, which is fine for short review chunks but would be a hard limit if the corpus expanded to include longer documents like syllabi, course descriptions, or advising handbooks.
- **Cost and latency:** API-hosted models add per-token cost and network latency on every query. For a high-traffic student-facing tool, local embedding keeps costs near zero and avoids rate limits, making MiniLM the right choice for this scale.
- **Multilingual support:** If the user base includes international students who write or search in other languages, a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would be necessary. The current model is English-only.
- **Local vs. API:** For a university deployment with privacy requirements (student queries should not leave campus), a local model is strongly preferred over an API-hosted one.

---

## Retrieval Test Results

**Query 1:** "Which professor requires attendance?"

| Rank | Source file | Distance | Chunk preview |
|------|-------------|----------|---------------|
| 1 | prof_Bal.txt | 0.21 | "you MUST attend class. Missing even one session can affect your grade…" |
| 2 | prof_Roya.txt | 0.44 | "attendance is tracked and participation matters…" |
| 3 | prof_Alser.txt | 0.58 | "Professor Alser is fair and lenient in grading…" |

**Why relevant:** The top chunk directly answers the query with explicit attendance language. The embedding model correctly ranked `prof_Bal.txt` first because it contains the strongest and most direct attendance signal ("you MUST attend class"). The second result is partially relevant — Roya's reviews also mention attendance. The third result is less relevant but was retrieved because it shares positive-review language with Bal's file.

---

**Query 2:** "Who is lenient in grading?"

| Rank | Source file | Distance | Chunk preview |
|------|-------------|----------|---------------|
| 1 | prof_Alser.txt | 0.19 | "fair and lenient in grading… gives partial credit…" |
| 2 | prof_Kumar.txt | 0.38 | "Best professor I have ever had… gives you the answers in class…" |
| 3 | prof_Islam.txt | 0.47 | "very patient… never makes you feel bad for asking questions…" |

**Why relevant:** The word "lenient" appears nearly verbatim in `prof_Alser.txt`, giving it the lowest cosine distance and the top rank. The other results are semantically related — both Kumar and Islam have strongly positive reviews — even though they do not contain the exact word. This shows the embedding model finding semantic meaning rather than just keyword matches.

---

**Query 3:** "Which professor's exams are based on lecture slides?"

| Rank | Source file | Distance | Chunk preview |
|------|-------------|----------|---------------|
| 1 | prof_Lan.txt | 0.28 | "quizzes are based on the exact same questions on the PowerPoint…" |
| 2 | prof_Johnson.txt | 0.33 | "Exams are based on lecture slides — study those and you'll do well…" |
| 3 | prof_Rahman.txt | 0.51 | "final is kinda predictable with 1 question for a topic…" |

**Why relevant:** Both `prof_Lan.txt` and `prof_Johnson.txt` contain direct mentions of PowerPoint slides and lecture-based assessments, ranking them in positions 1 and 2 with low distance scores. The third result is weaker — Rahman's "predictable final" is semantically adjacent to the concept of slide-based exams but does not confirm it directly.

---

## Grounded Generation

**System prompt grounding instruction:**

The following system prompt is passed to Groq's `llama-3.3-70b-versatile` model on every request:

```
You are a helpful assistant for Georgia State University students.
You answer questions about CS professors using ONLY the student reviews provided to you.

Rules you must follow:
1. Answer ONLY using information found in the provided review excerpts.
2. Do NOT use any outside knowledge about professors, courses, or universities.
3. If the provided excerpts do not contain enough information to answer the question,
   respond with exactly: "I don't have enough information in the available reviews to answer that."
4. Always mention which professor(s) the information came from.
5. Keep your answer concise and directly relevant to the question.
```

The retrieved chunks are injected into the user message as labeled excerpts in the format `[Excerpt N — source: prof_X.txt]`, followed by the question. The model is explicitly told to cite which source each claim comes from.

**How source attribution is surfaced in the response:**

Source attribution is surfaced in two ways. First, the system prompt instructs the LLM to name the professor and source file in its answer. Second, the `ask()` function programmatically extracts the `source` metadata field from every retrieved chunk and returns a `sources` list alongside the answer. The Gradio interface displays this as a separate "Sources retrieved" field, and the Flask AI Chat page appends it below each bot bubble in the format `SOURCES: BAL, ROYA, ALSER`.

**Example responses with source attribution:**

*Example 1 — Accurate, grounded answer:*

> Query: "Which professor requires attendance according to student reviews?"
>
> Response: "According to the student reviews, Professor Bal (from prof_Bal.txt) requires attendance. This is mentioned in Excerpt 1 and Review 2 from prof_Bal.txt, which states 'you MUST attend class.'"
>
> **Sources: BAL, ROYA, ALSER**

*Example 2 — Accurate, grounded answer:*

> Query: "Which professor is lenient in grading?"
>
> Response: "Professor Alser is described as having 'fair and lenient' grading, according to the review excerpts from prof_Alser.txt."
>
> **Sources: ISLAM, KUMAR, SADASIVUNI, ALSER**

*Example 3 — Out-of-scope refusal:*

> Query: "Which professor for CSC 2720 is most frequently described as explaining concepts clearly?"
>
> Response: "I don't have enough information in the available reviews to answer that."
>
> **Sources: ALSER, JOHNSON, RAHMAN, LAN**

*Note:* This is an honest failure — the relevant `prof_Islam.txt` chunks were not retrieved in the top-5 for this phrasing, so the model correctly refused rather than hallucinating. See Failure Case Analysis below.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which professor for CSC 2720 is most frequently described as explaining concepts clearly? | S M Towhidul Islam | "I don't have enough information in the available reviews to answer that." (Sources: Alser, Johnson, Rahman, Lan) | Off-target — Islam's chunks not in top-5 | Inaccurate |
| 2 | Which professor requires attendance according to student reviews? | Bal Abdullah | "Professor Bal requires attendance. Students mention 'you MUST attend class.'" (Sources: Bal, Roya, Alser) | Relevant | Accurate |
| 3 | Which professor is described as having a heavy workload? | Tushara Sadasivuni | "Professor Bal is described as having a class that 'WILL be hard for you'" (Sources: Johnson, Bal, Islam, Roya) | Partially relevant — Bal retrieved instead of Sadasivuni | Partially accurate |
| 4 | Which professor is lenient in grading? | Mohammed Alser | "Professor Alser is described as having 'fair and lenient' grading." (Sources: Islam, Kumar, Sadasivuni, Alser) | Relevant | Accurate |
| 5 | Which professor has the best reviews irrespective of the course? | William Johnson | "Professor Alser and Professor Kumar have very positive reviews… Professor Kumar has reviews stating 'Best professor I have ever had.'" (Sources: Alser, Kumar, Islam, Roya) | Partially relevant — returns positive professors but misses Johnson | Partially accurate |
| 6 | Which professor's exams are primarily based on lecture slides? | William Johnson | "Professor Lan's quizzes are based on the exact same questions on the PowerPoint… Professor Rahman's final is also kinda predictable." (Sources: Islam, Lan, Johnson, Rahman, Bal) | Partially relevant — retrieves Lan and Johnson but does not identify Johnson as the primary answer | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** Question 1 — "Which professor for CSC 2720 is most frequently described as explaining concepts clearly?"

**What the system returned:** "I don't have enough information in the available reviews to answer that." Sources retrieved: Alser, Johnson, Rahman, Lan — no chunks from `prof_Islam.txt` appeared in the top-5.

**Root cause (tied to a specific pipeline stage):**

This is a **Stage 4 (Retrieval) failure**. The ChromaDB cosine similarity search returned chunks from Alser, Johnson, Rahman, and Lan instead of Islam. The relevant `prof_Islam.txt` chunks ranked 6th or lower and never entered the context window passed to the LLM.

The deeper cause is at **Stage 3 (Embedding)**. The query phrase "explaining concepts clearly" is generic praise language that appears in positive reviews for many professors, not just Islam. When `all-MiniLM-L6-v2` encoded the query into a 384-dimensional vector, the result was nearly equidistant from chunks in multiple professor files. The cosine similarity scores spread across several professors instead of concentrating on Islam's file.

A secondary contributing factor is **Stage 2 (Chunking)**. At 500 characters, a single chunk from `prof_Islam.txt` may contain the "explains clearly" sentence alongside unrelated content such as course difficulty or attendance policy. This dilutes the semantic signal of that specific sentence, making the chunk rank lower against a query that is specifically about explanation clarity.

The generation stage (Stage 5) behaved correctly — Groq's Llama 3.3 received no relevant context and correctly refused to answer rather than hallucinating a professor's name.

**What you would change to fix it:**

1. **Stage 2 fix:** Reduce chunk size to ~150–200 characters so each chunk carries a single focused claim. A chunk containing only "explains every concept step by step" would produce a much more distinctive embedding against a query about explanation clarity.
2. **Stage 4 fix:** Add metadata filtering to restrict retrieval to CSC 2720 professors (Islam and Kumar) when the query mentions CSC 2720. This eliminates off-topic results from Alser, Johnson, and Lan entirely. *(This fix was implemented as a stretch feature — see the professor dropdown in the Gradio interface.)*
3. **Stage 3 fix:** Prepend the professor's name and course number to each chunk before embedding (e.g. `"S M Islam — CSC 2720: [review text]"`), so the professor identity becomes part of the embedding's semantic signal.

---

## Stretch Feature: Metadata Filtering

Metadata filtering was implemented to directly address the failure identified above, and is available in the Gradio interface (`localhost:7860`) as a professor dropdown labeled **"Filter by professor."**

**How it works:** ChromaDB stores a `source` metadata field (e.g. `"prof_Islam.txt"`) with every chunk. When a professor is selected from the dropdown, the `retrieve()` function passes a `where` clause to ChromaDB's `.query()` call before cosine similarity ranking:

```python
where = {"source": {"$eq": "prof_Islam.txt"}}
```

Only chunks from that professor's file are considered. All 5 retrieved chunks come from the selected professor regardless of how generic the query phrasing is.

**Comparison on 3 queries — with vs. without filter:**

| Query | Without filter (full corpus) | With filter: prof_Islam only |
|-------|------------------------------|------------------------------|
| "Which professor explains concepts most clearly?" | Returns Alser, Johnson, Rahman, Lan — **misses Islam** | Returns only Islam chunks — **correct, targeted answer** |
| "Is this professor good at explaining?" | Spreads across multiple positive-review professors | Stays within Islam's file — specific and accurate |
| "What is the workload like?" | Returns workload-heavy professors (Bal, Sadasivuni) | Returns only Islam's workload comments — professor-specific |

The filter has a visible effect on which results are returned: selecting "S M Islam" and re-running Question 1 produces a correct answer, whereas running the same query without the filter produces the refusal shown in the evaluation report.

---

## Spec Reflection

### One way the spec helped you during implementation

The `planning.md` chunking strategy section (500 chars, 100 char overlap) was written before any code was written, and those exact numbers were passed directly to Claude as a prompt to implement `ingest.py`. The spec acted as a contract — the generated code matched the spec without needing revision, and the chunk sizes proved appropriate for review-length text. Having the architecture diagram in `planning.md` also meant each milestone had a clear target: I could point Claude at a specific pipeline stage (for example, "implement the Embedding + Vector Store stage using ChromaDB and all-MiniLM-L6-v2") and receive code that fit the rest of the pipeline without conflicts.

### One way your implementation diverged from the spec, and why

The `planning.md` architecture section described a single Gradio interface as the query layer. During implementation, a Flask dashboard was added alongside Gradio to support interactive features — Battle Mode with live radar charts, a professor leaderboard, tag-based filtering, an Explore page with per-professor radar charts and difficulty sliders, and a rating modal — that Gradio's component model cannot support. This divergence was driven by user experience needs that only became clear once the Gradio interface was running: it handles evaluation well but cannot host a multi-page interactive experience. Both interfaces share the same `query.py` RAG backend and `ask()` function, so the core pipeline architecture from the spec remained unchanged — only the presentation layer expanded beyond what was originally planned.

---

## AI Usage

**Instance 1 — Generating `ingest.py`**

I gave Claude my `planning.md` Chunking Strategy section (500 characters, 100 character overlap, `.txt` file type) and the Documents table listing all 12 professor files. I asked it to implement `load_documents()`, `clean_text()`, and `chunk_text()` matching those exact parameters. Claude generated the full script including HTML entity cleaning and boilerplate removal. I reviewed the cleaning regex patterns and added Rate My Professors-specific boilerplate strings that Claude's generic version had missed — for example, "Submit a Correction," "Flag this professor," "Overall Quality," and "Would Take Again." These were necessary because Claude had no knowledge of the specific UI elements on Rate My Professors pages.

**Instance 2 — Generating the Gradio + Flask interface**

I gave Claude my Retrieval Approach section, the grounding requirement (answers from retrieved context only, with source attribution in every response), and the 6 evaluation questions. Claude produced both a Gradio UI and a Flask dashboard. I then directed Claude through a series of specific revisions that I decided on after reviewing the output: I asked it to change the color scheme from dark purple and neon to an editorial warm cream and gold palette; remove the animated scrolling ticker and professor name marquee; add professor name and course number input fields to the rating modal; correct the course numbers for all 12 professors (Claude had generated plausible but incorrect course numbers); and restructure the AI Chat page to display the 6 evaluation questions as clickable FAQ cards with category tags rather than plain chip buttons. Each revision was a judgment call I made after seeing Claude's output and comparing it against the project requirements and my design intent.