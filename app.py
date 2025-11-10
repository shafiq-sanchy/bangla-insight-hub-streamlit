import streamlit as st
import google.generativeai as genai
import openai
import os
from dotenv import load_dotenv
import base64
import mimetypes
import tempfile

# --- Page Configuration ---
st.set_page_config(
    page_title="বাংলা ইনসাইট হাব - Pro",
    page_icon="🎬",
    layout="centered"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1a202c; text-align: center; margin-bottom: 1rem; }
    .sub-header { font-size: 1.2rem; color: #718096; text-align: center; margin-bottom: 2rem; }
    .result-container { background-color: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; margin-top: 1.5rem; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #2d3748; border-bottom: 2px solid #667eea; padding-bottom: 0.5rem; margin-top: 1.5rem; }
    .stDownloadButton { margin-top: 1rem; }
    .warning-box { background-color: #fef5e7; border: 1px solid #f9e79f; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def process_with_openai(uploaded_file, api_key):
    """Processes video using OpenAI's Whisper for transcription and GPT for translation/summary."""
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Use a temporary file for OpenAI's API
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmpfile:
            tmpfile.write(uploaded_file.read())
            tmpfile_path = tmpfile.name

        transcription = ""
        translation = ""
        summary = ""

        with st.status("Processing with OpenAI...", expanded=True) as status:
            # Step 1: Transcribe
            status.update(label="Step 1/3: Transcribing audio with Whisper...", state="running")
            with open(tmpfile_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    language='en'
                )
            transcription = transcript.text
            status.update(label="✅ Transcription complete!", state="running")

            # Step 2: Translate
            status.update(label="Step 2/3: Translating to Bengali with GPT...", state="running")
            translation_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate the given English text to simple, easy-to-understand Bengali (সহজ বাংলা). Only provide the translated Bengali text."},
                    {"role": "user", "content": transcription}
                ]
            )
            translation = translation_response.choices[0].message.content
            status.update(label="✅ Translation complete!", state="running")

            # Step 3: Summarize
            status.update(label="Step 3/3: Summarizing and explaining meaning with GPT...", state="running")
            summary_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Based on the Bengali text, provide a detailed summary and explain its core meaning in Bengali. Use clear headings for 'সারসংক্ষেপ' (Summary) and 'অর্থবোধ' (Meaning)."},
                    {"role": "user", "content": translation}
                ]
            )
            summary = summary_response.choices[0].message.content
            status.update(label="✅ All steps complete!", state="complete")

        os.unlink(tmpfile_path) # Clean up temp file
        return {"transcription": transcription, "translation": translation, "summary": summary}

    except Exception as e:
        st.error(f"An error occurred with OpenAI: {e}")
        return None

def process_with_gemini(uploaded_file, api_key):
    """Processes video using Google Gemini in a single call."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        video_bytes = uploaded_file.read()
        base64_video = base64.b64encode(video_bytes).decode('utf-8')
        mime_type = uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0]

        prompt = """
        Analyze the video content and provide the following three parts, clearly labeling each one:
        
        1. English Transcription:
        [Provide the full English transcription of the spoken words in the video here.]
        
        2. Bengali Translation (সহজ বাংলা):
        [Translate the English transcription into simple, easy-to-understand Bengali here.]
        
        3. Summary & Meaning in Bengali:
        [Based on the Bengali translation, provide a detailed summary and explain its core meaning in Bengali here.]
        """
        
        with st.status("Processing with Gemini...", expanded=True) as status:
            status.update(label="Analyzing video and generating insights...", state="running")
            
            contents = [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_video
                    }
                }
            ]
            
            response = model.generate_content(contents)
            full_text = response.text
            
            # Parse the response
            parts = {
                "transcription": "Could not parse.",
                "translation": "Could not parse.",
                "summary": "Could not parse."
            }
            
            if "English Transcription:" in full_text:
                parts["transcription"] = full_text.split("English Transcription:")[1].split("2. Bengali Translation")[0].strip()
            if "Bengali Translation" in full_text:
                parts["translation"] = full_text.split("Bengali Translation")[1].split("3. Summary & Meaning")[0].strip()
            if "Summary & Meaning" in full_text:
                parts["summary"] = full_text.split("Summary & Meaning")[1].strip()
                
            status.update(label="✅ Analysis complete!", state="complete")
            
        return parts

    except Exception as e:
        st.error(f"An error occurred with Gemini: {e}")
        return None

# --- Main App ---
st.markdown('<h1 class="main-header">বাংলা ইনসাইট হাব - Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced video analysis with multiple AI providers</p>', unsafe_allow_html=True)

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    provider = st.radio(
        "Choose AI Provider:",
        ["Google Gemini (Faster)", "OpenAI (More Detailed)"],
        help="Gemini is faster (1 API call). OpenAI uses Whisper for transcription and GPT for analysis, which can be more accurate."
    )
    
    gemini_key = None
    openai_key = None
    
    if provider == "Google Gemini (Faster)":
        gemini_key = st.text_input("Gemini API Key:", type="password", help="Get your key from Google AI Studio")
    else:
        openai_key = st.text_input("OpenAI API Key:", type="password", help="Get your key from OpenAI Platform")

# --- Main Content Area ---
st.header("📹 Video Upload & Analysis")

uploaded_file = st.file_uploader(
    "Choose a video file...", 
    type=["mp4", "mov", "webm", "mkv"],
    help="Supports larger files up to 200MB. Processing time and costs may increase with file size."
)

if uploaded_file:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.write(f"**File:** {uploaded_file.name} ({file_size_mb:.2f} MB)")

    if file_size_mb > 200:
        st.error("File size exceeds 200MB limit.")
        st.stop()
        
    st.markdown('<div class="warning-box">⏱️ Processing large files can take several minutes and may incur higher API costs.</div>', unsafe_allow_html=True)

    # Check for required keys before showing the button
    keys_ok = (provider == "Google Gemini (Faster)" and gemini_key) or \
               (provider == "OpenAI (More Detailed)" and openai_key)

    if st.button("🚀 Start Analysis", type="primary", disabled=not keys_ok):
        if not keys_ok:
            st.error("Please enter the required API key(s) in the sidebar.")
            st.stop()
            
        results = None
        if provider == "Google Gemini (Faster)":
            results = process_with_gemini(uploaded_file, gemini_key)
        else:
            results = process_with_openai(uploaded_file, openai_key)

        if results:
            # --- Display Results ---
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            
            st.markdown('<h2 class="section-title">1. English Transcription</h2>', unsafe_allow_html=True)
            st.code(results["transcription"], language="en")
            
            st.markdown('<h2 class="section-title">2. Bengali Translation (সহজ বাংলা)</h2>', unsafe_allow_html=True)
            st.markdown(f"```\n{results['translation']}\n```")
            
            st.markdown('<h2 class="section-title">3. Summary & Meaning in Bengali</h2>', unsafe_allow_html=True)
            st.markdown(f"```\n{results['summary']}\n```")
            
            # --- Download Functionality ---
            combined_text = f"""--- English Transcription ---
{results['transcription']}

--- Bengali Translation ---
{results['translation']}

--- Bengali Summary & Meaning ---
{results['summary']}
"""
            st.download_button(
                label="📥 Download All Results (TXT)",
                data=combined_text,
                file_name="video_analysis_results.txt",
                mime="text/plain"
            )
            
            st.markdown('</div>', unsafe_allow_html=True)

# --- Instructions ---
with st.expander("📖 How to use this app"):
    st.markdown("""
    1. **Choose Provider**: Select between Google Gemini (faster, one API call) or OpenAI (more detailed, three-step process).
    2. **Enter API Key**: Paste your corresponding API key in the sidebar.
    3. **Upload Video**: Select a video file (up to 200MB).
    4. **Analyze**: Click "Start Analysis" and wait for real-time status updates.
    5. **View & Download**: Review the three-part results and download them as a text file.
    """)
