# 📄 Smart Document Analyzer

An intelligent document analysis system powered by OpenAI GPT-4o-mini. Automatically classifies documents, extracts entities, and generates summaries.

## 🎯 Features

- **Multi-Format Support**: PDF, DOCX, TXT
- **Auto-Classification**: Categorizes documents intelligently
- **Entity Extraction**: Names, dates, amounts, organizations
- **Smart Summarization**: Key points and concise summaries
- **Production-Ready**: Error handling, caching, fallback strategies

## 🏗️ Architecture

```
User uploads document or enters link to a document
        ↓
Document Loader (extract text)
        ↓
LLM Client (with retry + fallback + caching)
        ↓
├─ Classification
├─ Entity Extraction
└─ Summarization
        ↓
Streamlit UI (results display)
```

## 🛠️ Technical Stack

- **LLM**: OpenAI GPT-4o-mini with GPT-4o fallback
- **UI**: Streamlit
- **Document Processing**: PyPDF2, python-docx
- **Caching**: File-based with TTL expiry
- **Error Handling**: Exponential backoff, graceful degradation

## 📦 Installation

```bash
# Clone repository
gh repo clone prnk04/Smart_Document_Analyser
cd Smart_Document_Analyser

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run application
streamlit run app.py
```

## 🚀 Usage

1. Upload a document or enter link to a document(PDF, DOCX, or TXT)
2. Click "Analyze Document"
3. View results in three tabs:
   - **Classification**: Document type and confidence
   - **Entities**: Extracted names, dates, amounts, organizations
   - **Summary**: Concise overview and key points

## 💡 Key Design Decisions

### 1. Improved LLM Client Architecture

- Centralized retry logic in `_call_openai_with_retry()`
- Orchestration layer `call_with_fallback()` for model selection
- Error translation layer `handle_user_error()` for UX

### 2. Smart Caching with TTL

- Cache deterministic responses (temperature=0.0)
- TTL-based expiry (default 24 hours)
- Significant cost savings on repeated queries

### 3. Graceful Degradation

- Primary model: GPT-4o (quality)
- Fallback model: GPT-4o-mini (cost-effective)
- Fast failure to maintain good UX

## 📊 Performance

- **Classification**: ~2-3s per document
- **Entity Extraction**: ~3-4s per document
- **Summarization**: ~3-5s per document
- **Cache Hit**: <100ms (instant!)

## 🔮 Future Enhancements

- [ ] Batch processing
- [ ] Custom categories
- [ ] Export results (PDF, JSON)
- [ ] Document comparison
- [ ] Multi-language support
- [ ] Advanced entity linking

## 👨‍💻 Author

Built by Priyanka Pandey as part of GenAI → RAG → Agentic AI learning path.

**Skills Demonstrated:**

- Production LLM application design
- Error handling and resilience patterns
- Cost optimization through caching
- Clean architecture and separation of concerns
- 7+ years of software engineering best practices

## 📄 License

MIT License
