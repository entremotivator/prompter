import streamlit as st
import gspread
import pandas as pd
import json
import requests
from io import StringIO
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

# --- Configuration ---
# Default values for the sheet ID and video column name
DEFAULT_SHEET_ID = "1_fICV_W3ru3zm4aAO6rU8zSXIw7dchD9tKD3JcFpF1k"
DEFAULT_VIDEO_COLUMN_NAME = "Video URL" 

# --- Custom CSS for Colorful Theme ---
# Using a light blue theme with vibrant accents
CUSTOM_CSS = """
<style>
    /* Main container styling */
    .main {
        background-color: #f0f8ff; /* Light blue background */
        padding: 20px;
    }
    
    /* Sidebar styling */
    .css-1lcbmhc {
        background-color: #e6f7ff; /* Slightly darker light blue for sidebar */
        padding: 15px;
        border-right: 3px solid #4da6ff; /* Vibrant blue border */
    }
    
    /* Title styling */
    h1 {
        color: #0056b3; /* Dark blue for main title */
        text-align: center;
        border-bottom: 3px solid #4da6ff;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Header styling */
    h2, h3 {
        color: #007bff; /* Bright blue for headers */
        border-left: 5px solid #4da6ff;
        padding-left: 10px;
        margin-top: 30px;
    }
    
    /* Info and Warning boxes styling */
    .stAlert {
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: #d4edda;
        color: #155724;
        border-color: #c3e6cb;
    }
    
    /* Dataframe styling (optional, Streamlit's default is usually good) */
    .stDataFrame {
        border: 1px solid #4da6ff;
        border-radius: 5px;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #4da6ff;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #007bff;
    }
    
    /* Video container styling */
    .stVideo {
        border: 5px solid #4da6ff;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 5px 5px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Separator line styling */
    hr {
        border-top: 2px solid #4da6ff;
    }
</style>
"""

st.set_page_config(
    page_title="Enhanced VLIVE Google Sheets Viewer & Form",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.title("📺 Enhanced VLIVE Google Sheets Data Viewer & Form")
st.markdown("### A dynamic and colorful application to view data from Google Sheets, embed video links, and submit new data.")

# --- Authentication in Sidebar ---
st.sidebar.header("🔑 Google Sheets Authentication")
uploaded_file = st.sidebar.file_uploader(
    "Upload Google Service Account JSON File", 
    type="json", 
    help="Upload the JSON key file for your Google Service Account."
)

# --- Configuration in Sidebar ---
st.sidebar.header("⚙️ Sheet Configuration")
sheet_id = st.sidebar.text_input(
    "Google Sheet ID", 
    value=DEFAULT_SHEET_ID,
    help="The unique ID from your Google Sheet URL."
)
video_col_name = st.sidebar.text_input(
    "Video Link Column Name", 
    value=DEFAULT_VIDEO_COLUMN_NAME,
    help="The exact name of the column containing the video URLs."
)

st.sidebar.header("🔗 Webhook Configuration")
webhook_url = st.sidebar.text_input(
    "Webhook URL (Optional)",
    placeholder="e.g., https://your.webhook.site/endpoint",
    help="URL to send form data to upon submission."
)

@st.cache_resource(ttl=3600)
def get_gspread_client(service_account_info):
    """Authenticates gspread using the service account info."""
    try:
        gc = gspread.service_account_from_dict(service_account_info)
        return gc
    except Exception as e:
        st.error(f"Authentication failed. Please check your JSON file format and ensure the service account has access. Error: {e}")
        return None

@st.cache_data(ttl=600)
def load_data(gc, sheet_id, worksheet_name):
    """Loads data from the specified worksheet of the Google Sheet."""
    try:
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except SpreadsheetNotFound:
        st.error(f"Error: Spreadsheet with ID **'{sheet_id}'** not found. Check the ID and ensure the service account has access.")
        return pd.DataFrame()
    except WorksheetNotFound:
        st.error(f"Error: Worksheet **'{worksheet_name}'** not found in the spreadsheet.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# --- Main Application Logic ---
if uploaded_file is not None:
    # Read the uploaded JSON file content
    try:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        service_account_info = json.load(stringio)
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file uploaded. Please ensure it is the correct Service Account key file.")
        st.stop()

    gc = get_gspread_client(service_account_info)
    
    if gc:
        st.sidebar.success("✅ Authentication successful!")
        
        # --- Dynamic Worksheet Selection ---
        try:
            spreadsheet = gc.open_by_key(sheet_id)
            worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
            
            selected_worksheet = st.sidebar.selectbox(
                "Select Worksheet (Tab)",
                options=worksheet_titles,
                help="Choose the tab in your Google Sheet to load data from."
            )
        except SpreadsheetNotFound:
            st.error(f"Spreadsheet with ID **'{sheet_id}'** not found.")
            st.stop()
        except Exception as e:
            st.error(f"Could not retrieve worksheet list. Error: {e}")
            st.stop()

        # --- Tabs for Viewer and Form ---
        viewer_tab, form_tab = st.tabs(["👁️ Data Viewer", "📝 Data Submission Form"])

        # --- Data Viewer Tab ---
        with viewer_tab:
            df = load_data(gc, sheet_id, selected_worksheet)
            
            if not df.empty:
                st.header(f"📊 Data from Worksheet: **{selected_worksheet}**")
                
                # --- Data Filtering ---
                search_term = st.text_input("🔍 Search Data", help="Enter text to filter the table and videos.", placeholder="Search by title, description, or any column...")
                
                if search_term:
                    df_filtered = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
                else:
                    df_filtered = df
                
                st.subheader(f"Displaying {len(df_filtered)} of {len(df)} Records")
                st.dataframe(df_filtered, use_container_width=True)
                
                # --- Video Embedding ---
                st.header("🎬 Embedded Videos")
                
                if video_col_name in df_filtered.columns:
                    video_data = df_filtered[df_filtered[video_col_name].astype(str).str.startswith('http')].reset_index(drop=True)
                    
                    if not video_data.empty:
                        st.info(f"Found and displaying **{len(video_data)}** video(s) matching your criteria.")
                        
                        video_container = st.container()
                        
                        with video_container:
                            cols = st.columns(2)
                            
                            for index, row in video_data.iterrows():
                                col = cols[index % 2]
                                
                                with col:
                                    other_cols = [c for c in df_filtered.columns if c != video_col_name]
                                    title_text = f"Record {row.name + 1}"
                                    
                                    if other_cols:
                                        title_text = str(row[other_cols[0]])
                                    
                                    st.subheader(f"🎥 {title_text}")
                                    
                                    with st.expander("View Details"):
                                        for c in other_cols:
                                            st.markdown(f"**{c}:** {row[c]}")
                                    
                                    st.video(row[video_col_name])
                                    st.markdown("---")
                    else:
                        st.warning(f"⚠️ No valid video links found in the column **'{video_col_name}'** in the filtered data.")
                else:
                    st.error(f"❌ Could not find the configured video column **'{video_col_name}'**. Please check the configuration in the sidebar.")
                    st.info(f"Available columns: {', '.join(df_filtered.columns)}")
            else:
                st.warning("⚠️ The DataFrame is empty after loading or filtering. Please check the sheet content and service account permissions.")

        # --- Data Submission Form Tab ---
        with form_tab:
            st.header("📝 Submit New Data")
            st.markdown("Use this form to submit new video links and data to your Google Sheet and/or a webhook.")

            with st.form("data_submission_form"):
                # Form fields - adjust these to match your expected sheet columns
                title = st.text_input("Title / Description (Column 1)", max_chars=100)
                video_url_input = st.text_input("Video URL (Required)", placeholder="https://cdn.pipio.ai/...", key="video_url_form")
                additional_data = st.text_area("Additional Data (Column 3+)", help="Enter any other data you want to submit.")
                
                # Submission options
                submit_to_sheet = st.checkbox(f"Append to Google Sheet: **{selected_worksheet}**", value=True)
                submit_to_webhook = st.checkbox("Send to Webhook", value=False, disabled=(not webhook_url))
                
                submitted = st.form_submit_button("Submit Data", type="primary")

                if submitted:
                    if not video_url_input:
                        st.error("The Video URL field is required.")
                    else:
                        data_to_submit = {
                            "Title": title,
                            video_col_name: video_url_input,
                            "Additional_Data": additional_data,
                            "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        success = True
                        
                        # 1. Append to Google Sheet
                        if submit_to_sheet:
                            try:
                                sh = gc.open_by_key(sheet_id)
                                worksheet = sh.worksheet(selected_worksheet)
                                
                                # Prepare data as a list of values
                                # NOTE: This assumes the sheet has columns in the order: Title, Video URL, Additional_Data, Timestamp
                                # You may need to adjust this list based on your actual sheet structure.
                                values = [
                                    data_to_submit["Title"],
                                    data_to_submit[video_col_name],
                                    data_to_submit["Additional_Data"],
                                    data_to_submit["Timestamp"]
                                ]
                                
                                worksheet.append_row(values)
                                st.success(f"✅ Successfully appended data to Google Sheet: **{selected_worksheet}**")
                                
                                # Clear the data cache so the viewer tab can load the new data
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"❌ Failed to append data to Google Sheet. Error: {e}")
                                success = False

                        # 2. Send to Webhook
                        if submit_to_webhook and webhook_url:
                            try:
                                response = requests.post(webhook_url, json=data_to_submit, timeout=5)
                                if response.status_code == 200:
                                    st.success(f"✅ Successfully sent data to webhook: **{webhook_url}**")
                                else:
                                    st.warning(f"⚠️ Webhook received data but returned status code: {response.status_code}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"❌ Failed to send data to webhook. Error: {e}")
                                success = False
                        elif submit_to_webhook and not webhook_url:
                            st.warning("⚠️ Cannot send to webhook: Webhook URL is not configured in the sidebar.")
                            success = False
                            
                        if success:
                            st.balloons()
                            st.experimental_rerun() # Rerun to clear form and update viewer tab

# --- Instructions for the user ---
st.sidebar.markdown("""
---
**📚 Setup Guide**

1.  **Get Service Account Key:** Create a Google Service Account and download the JSON key file.
2.  **Share Sheet:** Share your Google Sheet with the email address found in the `client_email` field of the JSON key file.
3.  **Upload & Configure:** Upload the JSON file and enter the correct **Google Sheet ID**, **Video Link Column Name**, and optionally a **Webhook URL** in the sidebar.
4.  **Select Tab:** Use the tabs to switch between the **Data Viewer** and the **Data Submission Form**.
""")
