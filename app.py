"""
Smart document analyzer UI using Streamlit
"""

import json
import streamlit as st
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.document_loader import DocumentLoader
from src.classifier import classify_document
from src.extractor import extract_entity_from_document
from src.summarizer import summarize_document
from src.llm_client import llm_client


# =========================================================================================#
#                                       Page Config                                       #
# =========================================================================================#

st.set_page_config(page_title="Smart Document Analyzer", page_icon="📄", layout="wide")


# =========================================================================================#
#                                         Sidebar                                         #
# =========================================================================================#

st.sidebar.title("📄 Smart Document Analyzer")

st.sidebar.markdown(
    """
**Features:**
- 📁 Upload PDF, DOCX, TXT
- 🏷️ Auto-classification
- 🔍 Entity extraction
- 📝 Smart summarization

**Powered by:**
- OpenAI GPT-4o-mini
- Your engineering skills!
"""
)

st.sidebar.divider()

# Categories
categories = st.sidebar.multiselect(
    "Document Categories",
    [
        "Contract",
        "Invoice",
        "Email",
        "Report",
        "License",
        "Contract",
        "Will",
        "Certificates",
        "Technical Spec",
        "Memo",
        "Application",
        "Manuals",
        "Recipe",
        "Financial Statement",
        "Other",
    ],
    default=[
        "Contract",
        "Invoice",
        "Email",
        "Report",
        "License",
        "Contract",
        "Will",
        "Certificates",
        "Technical Spec",
        "Memo",
        "Application",
        "Manuals",
        "Recipe",
        "Financial Statement",
        "Other",
    ],
)

if len(categories) < 2:
    st.sidebar.warning("Select at least 2 categories!")


# =========================================================================================#
#                                          Main app                                        #
# =========================================================================================#

st.title("📄 Smart Document Analyzer")
st.markdown("Upload a document and let AI analyze it for you!")

# File upload
uploaded_file = st.file_uploader(
    "Choose a document",
    type=["pdf", "docx", "txt"],
    help="Supported formats: PDF, DOCX, TXT",
)

st.markdown("OR")
# add url
file_url = st.text_input("Add URL for a pdf or docx or txt file", value="")
goBtn = st.button("Go", help="Get the document from specified URL for analysis")

print("file url: ", file_url)

if uploaded_file:
    # save the file temporarily
    temp_path = Path(f"temp_{uploaded_file.name}")
    temp_path.write_bytes(uploaded_file.read())

    st.divider()

    try:
        # load the document
        with st.spinner("📖 Loading document..."):
            doc_data = DocumentLoader.load(temp_path)

        # Display the file details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Type", doc_data["file_type"])
        with col2:
            st.metric("File Size", f"{doc_data['size'] / 1024:.1f} KB")
        with col3:
            st.metric("Word Count", doc_data["word_count"])

        st.divider()

        # show first 500 characters
        with st.expander("📄 Document Preview", expanded=False):
            st.text(
                doc_data["text"][:500] + "..."
                if len(doc_data["text"]) > 500
                else doc_data["text"]
            )

        # Analyze button

        if st.button("🔍 Analyze Document", type="primary", use_container_width=True):

            # create tabs for results
            tab1, tab2, tab3 = st.tabs(
                ["🏷️ Classification", "🔍 Entities", "📝 Summary"]
            )

            # Tab1 : Classification
            with tab1:
                with st.spinner("Classifying documents..."):
                    try:
                        classification = classify_document(
                            doc_data["text"], categories, llm_client
                        )
                        st.success("✅ Classification Complete!")
                        print("Classification result:\n", classification)
                        print("type of class: ", type(classification))
                        # if type(classification) == str:
                        #     classification = json.loads(classification)
                        # print("new clas: ", classification)
                        print("type: ", type(classification))
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Category", classification.get("category", ""))
                        with col2:
                            st.metric("Confidence", classification.get("confidence", 0))

                        st.info(f"**Reasoning**: {classification.get("reasoning", "")}")
                    except Exception as e:
                        print("Error in classification: ", e)

            with tab2:
                with st.spinner("Extracting entities..."):
                    try:
                        entities = extract_entity_from_document(
                            doc_data["text"], llm_client
                        )
                        st.success("✅ Entity extraction Complete!")

                        # entities = json.loads(entities)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("👤 Names")
                            if entities["names"]:
                                for name in entities["names"]:
                                    st.markdown(f"- {name}")
                            else:
                                st.info("No names found")

                            st.subheader("💰 Amounts")
                            if entities["amounts"]:
                                for amount in entities["amounts"]:
                                    st.markdown(f"- {amount}")
                            else:
                                st.info("No amounts found")

                        with col2:
                            st.subheader("📅 Dates")
                            if entities["dates"]:
                                for date in entities["dates"]:
                                    st.markdown(f"- {date}")
                            else:
                                st.info("No dates found")

                            st.subheader("🏢 Organizations")
                            if entities["organizations"]:
                                for org in entities["organizations"]:
                                    st.markdown(f"- {org}")
                            else:
                                st.info("No organizations found")

                    except Exception as e:
                        print("Error in extracting entities: ", e)

            with tab3:
                with st.spinner("Summarizing the document..."):
                    try:
                        summary = summarize_document(doc_data["text"], llm_client, 100)
                        st.success("✅ Summarising document Complete!")
                        # summary = json.loads(str(summary))

                        st.subheader("📝 Summary")
                        st.write(summary["summary"])

                        st.subheader("🔑 Key Points")
                        for i, point in enumerate(summary["key_points"], 1):
                            st.markdown(f"{i}. {point}")
                    except Exception as e:
                        print("Errro in summarizing: ", e)

    except Exception as e:
        print(f"Exception while processing the file: {e}")
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

# if file_url:
if file_url and goBtn:
    try:
        # load the document
        with st.spinner("📖 Loading document..."):
            doc_data = DocumentLoader.load_from_url(file_url)

        # Display the file details
        # print(doc_data)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Type", doc_data["file_type"])
        with col2:
            st.metric("File Size", f"{doc_data['size'] / 1024:.1f} KB")
        with col3:
            st.metric("Word Count", doc_data["word_count"])

        st.divider()

        # show first 500 characters
        with st.expander("📄 Document Preview", expanded=False):
            st.text(
                doc_data["text"][:500] + "..."
                if len(doc_data["text"]) > 500
                else doc_data["text"]
            )

        # Analyze button

        if st.button("🔍 Analyze Document", type="primary", use_container_width=True):

            # create tabs for results
            tab1, tab2, tab3 = st.tabs(
                ["🏷️ Classification", "🔍 Entities", "📝 Summary"]
            )

            # Tab1 : Classification
            with tab1:
                with st.spinner("Classifying documents..."):
                    try:
                        classification = classify_document(
                            doc_data["text"], categories, llm_client
                        )
                        st.success("✅ Classification Complete!")
                        print("Classification result:\n", classification)
                        print("type of class: ", type(classification))
                        # if type(classification) == str:
                        #     classification = json.loads(classification)
                        # print("new clas: ", classification)
                        print("type: ", type(classification))
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Category", classification.get("category", ""))
                        with col2:
                            st.metric("Confidence", classification.get("confidence", 0))

                        st.info(f"**Reasoning**: {classification.get("reasoning", "")}")
                    except Exception as e:
                        print("Error in classification: ", e)

            with tab2:
                with st.spinner("Extracting entities..."):
                    try:
                        entities = extract_entity_from_document(
                            doc_data["text"], llm_client
                        )
                        st.success("✅ Entity extraction Complete!")

                        # entities = json.loads(entities)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("👤 Names")
                            if entities["names"]:
                                for name in entities["names"]:
                                    st.markdown(f"- {name}")
                            else:
                                st.info("No names found")

                            st.subheader("💰 Amounts")
                            if entities["amounts"]:
                                for amount in entities["amounts"]:
                                    st.markdown(f"- {amount}")
                            else:
                                st.info("No amounts found")

                        with col2:
                            st.subheader("📅 Dates")
                            if entities["dates"]:
                                for date in entities["dates"]:
                                    st.markdown(f"- {date}")
                            else:
                                st.info("No dates found")

                            st.subheader("🏢 Organizations")
                            if entities["organizations"]:
                                for org in entities["organizations"]:
                                    st.markdown(f"- {org}")
                            else:
                                st.info("No organizations found")

                    except Exception as e:
                        print("Error in extracting entities: ", e)

            with tab3:
                with st.spinner("Summarizing the document..."):
                    try:
                        summary = summarize_document(doc_data["text"], llm_client, 100)
                        st.success("✅ Summarising document Complete!")
                        # summary = json.loads(str(summary))

                        st.subheader("📝 Summary")
                        st.write(summary["summary"])

                        st.subheader("🔑 Key Points")
                        for i, point in enumerate(summary["key_points"], 1):
                            st.markdown(f"{i}. {point}")
                    except Exception as e:
                        print("Errro in summarizing: ", e)

        # else:
        #     # Instructions
        #     st.info("👆 Upload a document to get started!")

        #     st.markdown(
        #         """
        #     ### How it works:

        #     1. **Upload** your document (PDF, DOCX, or TXT)
        #     2. **Click** Analyze Document
        #     3. **View** results in tabs:
        #     - Classification: What type of document is it?
        #     - Entities: Names, dates, amounts, organizations
        #     - Summary: Key points and overview

        #     ### Example use cases:
        #     - 📄 Quickly understand contract terms
        #     - 📧 Extract action items from emails
        #     - 📊 Summarize long reports
        #     - 💼 Process invoices automatically
        #     """
        #     )
    except Exception as e:
        print(f"Exception while processing the url: {e}")
# =========================================================================================#
#                                           Footer                                         #
# =========================================================================================#

st.divider()
st.markdown(
    """
<div style='text-align: center; color: gray;'>
    Built with ❤️ using OpenAI GPT-4o-mini | 
    <a href='https://github.com/prnk04/document-analyzer' target='_blank'>View on GitHub</a>
</div>
""",
    unsafe_allow_html=True,
)
