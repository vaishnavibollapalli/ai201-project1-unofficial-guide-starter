# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain
I chose Georgia State University's (GSU) Computer Science department professor reviews. My source is from Rate My Professors website. Students often depend on unofficial sources when they are choosing courses as they provide information about the professors teaching style, exam difficulty, amount of workload or even the grading policies which official sources fail to provide. This project makes student reviews accessible through a searchable database system.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

|#| Source | Description | URL or location |
|-|--------|-------------|-----------------|
|1|Rate My Professor|Professor Mohammed Alser reviews|https://www.ratemyprofessors.com/professor/3126576 |
|2|Rate My Professor|Professor Ashwin Ashok reviews|https://www.ratemyprofessors.com/professor/2688463 |
|3|Rate My Professor|Professor Bal Abdullah reviews|https://www.ratemyprofessors.com/professor/2942443 |
|4|Rate My Professor|Professor Xie Bingyi reviews|https://www.ratemyprofessors.com/professor/2906245 |
|5|Rate My Professor|Professor Esra Akbas reviews|https://www.ratemyprofessors.com/professor/3006294 |
|6|Rate My Professor|Professor S M Islam To reviews |https://www.ratemyprofessors.com/professor/2921056 |
|7|Rate My Professor|Professor William Johnson reviews|https://www.ratemyprofessors.com/professor/2329806 |
|8|Rate My Professor|Professor Gao Lan reviews|https://www.ratemyprofessors.com/professor/3075860 |
|9|Rate My Professor|Professor Mufzur Rahaman reviews|https://www.ratemyprofessors.com/professor/2519939 |
|10|Rate My Professor|Professor Tushara Sadasivuni reviews|https://www.ratemyprofessors.com/professor/2317655 |
|11|Rate My Professor|Professor Saliesh Kumar reviews|https://www.ratemyprofessors.com/professor/2524563|
|12|Rate My Professor|Professor Hosseini Roya reviews|https://www.ratemyprofessors.com/professor/2723447|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 500 charc

**Overlap:** 100 charc

**Reasoning:**
-The .txt documents in this project has short reviews by students about professors teaching styles, grading policies, exam difficulties, amount of workload and their responsiveness. Each chunk size is 500 charcters which is large enough to keep one complete thought but stay on topic.

-To make sure key info isn't missed, there's a 100-character overlap between chunks. This way, details like attendance rules and test difficulty that might stretch across sentences get covered better.

-If the pieces are too small, thoughts could get cut off and mess up finding the right info. But if they're too big, different views could blend, making it tougher for search stuff to pick out what's really relevant.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** all-MiniLM-L6-v2 from the sentence-transformers library.


**Top-k:** 5 retrieved chunks per query

**Production tradeoff reflection:**
-I picked the all-MiniLM-L6-v2 model since it’s free, runs smoothly on local devices, and gives pretty solid results for shorter texts like student reviews. If we wanted to use this in a real-world setting at a university, though, I'd want to look into bigger, more powerful models. Those could handle longer texts and provide even better accuracy. 

-There'd be other things to think about too, such as speed, costs, and whether the model works with multiple languages. Also, for dealing with really large datasets, a more advanced model might be necessary despite the extra computing power and expenses needed.
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 |Which professor for CSC 2720 is most frequently described as explaining concepts clearly? |S M Towhidul Islam|
| 2 |Which professor requires attendance according to student reviews? |Bal Abdullah|
| 3 |Which professor is described as having a heavy workload? |Tushara Sadasivuni|
| 4 |Which Professor is lenient in grading? |Mohammed Alser|
| 5 |Which Professor has the best reviews irrespective of the course? |William Johnson|
| 6 |Which professor's exams are primarily based on lecture slides?|William Johnson|

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.Student reviews can seriously contradict themselves about the same professor. One might call a professor amazing, but someone else could say the exact opposite. So, it’s hard for the system to come up with a fair summary.

2.Sometimes crucial info gets chopped up. Say a review discusses class attendance one line and then jumps to grades. The system ends up missing the full picture if it slices those facts apart.

3.Many students use slang or just write real short blurbs like “GOAT” or “Best prof ever.” Not only are these comments super vague, but they’re useless for any detailed analysis too.

4.It’s common for the system to bring back wrong matches. For instance, if a review sounds great but’s about the wrong teacher - all because he’s known for easy tests or is a good speaker.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

This architecture follows a standard Retrieval-Augmented Generation (RAG) pipeline. First, professor reviews are ingested and chopped up, then embedded with the all-MiniLM-L6-v2 model. Next, the embeddings go into ChromaDB. This DB finds the best matching pieces for your query. Finally, Groq's Llama 3.3 model generates answers shown via Gradio.


## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I'll have Claude assist in generating Python code to load professor review texts, clean up extra spaces, and chop those files into chunks, sticking to my specified chunk size of 500 characters with a 100-character overlap. After receiving the code, I'll make sure it creates neat and self-contained chunks just like I asked.

**Milestone 4 — Embedding and retrieval:**
Next, I'll get Claude to help out with coding the embedding process for those chunks using the all-MiniLM-L6-v2 sentence-transformers model. The embeddings need to be saved in ChromaDB along with their source info. Once this code is ready, I'll double-check that it retrieves relevant chunks based on my questions and verifies correct sources are linked up.

**Milestone 5 — Generation and interface:**
Additionally, I plan to use Claude for crafting the retrieval-augmented generation pipeline and putting together a Gradio user interface. With inputs on grounding requirements, retrieval approach, and other project specs, I'll confirm the pipeline sticks to answering queries only with supported document evidence, attributes the sources accurately, and refuses to respond appropriately when info isn't found within the documents.
