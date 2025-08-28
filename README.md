# Agentic Legal Research Assistant (NotionAI)

An **agentic chatbot assistant** designed for lawyers and legal professionals.  
The system leverages **Hybrid RAG (knowledge graph + vector database)**, multimodal data support, and legal-domain databases to provide **personalized, context-aware legal research and automation**.  

---

## 🚀 Project Overview

Imagine a lawyer using **Notion** as a personal workspace — storing case notes, judgments, documents, links, and multimedia.  
This project builds an **AI-powered assistant** that connects directly with that workspace, enriches it with **legal databases**, and provides intelligent, personalized answers to legal queries.

**Key Capabilities (intended):**
- Retrieve and reason over the lawyer’s **personal case history (Notion workspace)**.  
- Build a **Hybrid RAG** from structured/unstructured sources: text, PDFs, images, audio, video.  
- Access a **comprehensive database of Indian Central and State Acts**.  
- Integrate **High Court and Supreme Court case law repository** (in progress).  
- Invoke **internet search tools** when external knowledge is required.  
- Provide **personalized, agentic responses** aware of user’s past work and legal context.  

---

## ✅ Current Progress

- ✔️ Connected to **Notion workspace** API for ingesting user’s personal database.  
- ✔️ Implemented **Hybrid RAG pipeline** (Knowledge Graph + Vector DB) for text data.  
- ✔️ Integrated **Central and State Acts database**.  

---

## 🔄 Work in Progress

- ⏳ Expanding **Hybrid RAG** to support **multimodal inputs** (PDFs, images, audio, video).  
- ⏳ Sourcing and integrating **High Court & Supreme Court case repositories**.  
- ⏳ Agent orchestration: equipping chatbot with **tool-using abilities** (web search, case lookup, contextual reasoning).  
- ⏳ Building evaluation framework for **retrieval precision, recall, and factuality** in legal domain.  

---

## 🎯 Vision

The goal is to create a **personalized legal research companion** that:  
- Reduces manual effort in finding and cross-referencing cases.  
- Ensures faster, more reliable access to laws, precedents, and personal work history.  
- Bridges cutting-edge **AI retrieval architectures** with **real-world legal practice**.  

---

## 🛠️ Tech Stack

- **Frontend/Integration**: Notion API  
- **Core AI**: Hybrid RAG (Knowledge Graph + Vector DB)  
- **LLM Backbone**: Phi-4 (extendable to other LLMs)  
- **Databases**: Central & State Acts, Case Law (in progress)  
- **Orchestration**: Agentic tool-calling system  
