import os
import streamlit as st
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
@st.cache_resource
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=api_key)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Set page config
st.set_page_config(page_title="PDF Chat Assistant", page_icon="📚")
st.title("📚 Chat with your PDF")

# Initialize session states
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# File uploader
pdf_file = st.file_uploader("Upload your PDF file", type='pdf')

if pdf_file and not st.session_state.pdf_content:
    with st.spinner("Processing PDF..."):
        # Extract text from PDF
        st.session_state.pdf_content = extract_text_from_pdf(pdf_file)
        st.success("PDF processed successfully!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your PDF:"):
    if not st.session_state.pdf_content:
        st.error("Please upload a PDF first!")
    else:
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get AI response
        with st.chat_message("assistant"):
            client = get_groq_client()
            with st.spinner("Thinking..."):
                # Prepare the system message and user query
                messages = [
                    {
                        "role": "system",
                        "content": f"""You are a helpful assistant that answers questions based only on the provided PDF content. 
                        Here's the content from the PDF:
                        {st.session_state.pdf_content}
                        
                        Only answer questions based on the information provided in the PDF above. 
                        If the answer cannot be found in the PDF content, respond with "I cannot find information about this in the provided PDF."
                        Be concise and accurate in your responses."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="llama-3.3-70b-versatile",
                    temperature=0.1  # Lower temperature for more focused answers
                )
                response = chat_completion.choices[0].message.content
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})