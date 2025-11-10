import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import tempfile
import time
import base64

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="বাংলা ইনসাইট হাব",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1a202c;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #718096;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-container {
        background-color: #f0fff4;
        border: 1px solid #9ae6b4;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1.5rem;
    }
    .error-container {
        background-color: #fed7d7;
        border: 1px solid #fc8181;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }
    .api-key-container {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">বাংলা ইনসাইট হাব</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Upload your videos to get AI-powered insights in Bangla</p>', unsafe_allow_html=True)

# Sidebar for API key
with st.sidebar:
    st.header("🔑 API Key Settings")
    
    # Option to use environment variable or input
    use_env = st.checkbox("Use API key from environment", value=True)
    
    if use_env:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            st.success("API key loaded from environment")
        else:
            st.error("No API key found in environment")
            st.info("Please set up a .env file with your API key or uncheck the box above")
    else:
        api_key = st.text_input("Enter your Gemini API Key:", type="password")
    
    st.markdown("---")
    st.markdown("### How to get an API Key:")
    st.markdown("1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.markdown("2. Sign in with your Google account")
    st.markdown("3. Click 'Create API Key'")
    st.markdown("4. Copy the key and use it here")

# Check if API key is available
if not api_key:
    st.markdown('<div class="api-key-container">Please provide an API key to continue.</div>', unsafe_allow_html=True)
    st.stop()

# Configure the Gemini API
genai.configure(api_key=api_key)

# Main content area
st.header("📹 Video Upload and Analysis")

# File upload
uploaded_file = st.file_uploader(
    "Choose a video file...", 
    type=["mp4", "mov", "avi", "mkv", "webm"],
    help="Upload a video file to analyze. Maximum recommended size: 20MB"
)

if uploaded_file is not None:
    # Display video details
    video_details = {
        "Filename": uploaded_file.name,
        "File Size": f"{uploaded_file.size / (1024 * 1024):.2f} MB",
        "File Type": uploaded_file.type
    }
    
    st.write("### Video Details:")
    for key, value in video_details.items():
        st.write(f"- **{key}**: {value}")
    
    # Check file size
    if uploaded_file.size > 20 * 1024 * 1024:  # 20MB limit
        st.error("File is too large. Please upload a video smaller than 20MB.")
        st.stop()
    
    # Process button
    if st.button("🔍 Process Video", type="primary"):
        with st.spinner("Processing video... This may take a few minutes."):
            try:
                # Read and encode the video file
                video_bytes = uploaded_file.read()
                base64_video = base64.b64encode(video_bytes).decode('utf-8')
                
                # Initialize the model
                model = genai.GenerativeModel('gemini-pro-vision')
                
                # Prepare the prompt
                prompt = "এই ভিডিওটি বিশ্লেষণ করুন এবং বাংলায় বিস্তারিত অন্তর্দৃষ্টি প্রদান করুন। ভিডিওর মূল বিষয়বস্তু, গুরুত্বপূর্ণ পয়েন্ট, এবং সম্ভাব্য সুপারিশগুলি অন্তর্ভুক্ত করুন।"
                
                # Create the parts for the content
                parts = [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": uploaded_file.type,
                            "data": base64_video
                        }
                    }
                ]
                
                # Generate content
                st.write("Generating insights...")
                response = model.generate_content(parts)
                
                # Display the result
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown("### 🎯 Analysis Results:")
                st.write(response.text)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.markdown(f'<div class="error-container">Error: {str(e)}</div>', unsafe_allow_html=True)

# Instructions at the bottom
with st.expander("📖 How to use this app"):
    st.markdown("""
    1. **Get an API Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to get your free Gemini API key
    2. **Enter API Key**: Either add it to your environment variables or enter it in the sidebar
    3. **Upload Video**: Click "Browse files" to select a video from your device
    4. **Process Video**: Click the "Process Video" button to analyze the video
    5. **View Results**: The AI will provide insights in Bangla about your video
    """)
