import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import requests
from io import StringIO
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
from datetime import datetime
import time

# --- Configuration ---
DEFAULT_SHEET_ID = "1_fICV_W3ru3zm4aAO6rU8zSXIw7dchD9tKD3JcFpF1k"
DEFAULT_VIDEO_COLUMN_NAME = "Video URL"

# Define the scope for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# --- Enhanced Custom CSS with Modern Design ---
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container styling with gradient background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        min-height: 100vh;
    }
    
    /* Content wrapper with glass morphism effect */
    .block-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Sidebar styling with gradient */
    .css-1lcbmhc, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Title styling with animation */
    h1 {
        color: #667eea;
        text-align: center;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        animation: fadeInDown 0.8s ease-in-out;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Header styling */
    h2, h3 {
        color: #764ba2;
        font-weight: 600;
        margin-top: 30px;
        padding-left: 15px;
        border-left: 5px solid #667eea;
        animation: fadeIn 1s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Alert boxes with modern styling */
    .stAlert {
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: none;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Success message styling */
    .stSuccess {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
    }
    
    /* Info message styling */
    .stInfo {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: #1a1a1a;
        font-weight: 600;
    }
    
    /* Warning message styling */
    .stWarning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        font-weight: 600;
    }
    
    /* Error message styling */
    .stError {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: #1a1a1a;
        font-weight: 600;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border: 2px solid #667eea;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Button styling with hover effect */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 12px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(102, 126, 234, 0.6);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Video container styling with modern frame */
    .stVideo {
        border: 5px solid transparent;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        background: linear-gradient(white, white) padding-box,
                    linear-gradient(135deg, #667eea 0%, #764ba2 100%) border-box;
        transition: transform 0.3s ease;
    }
    
    .stVideo:hover {
        transform: scale(1.02);
    }
    
    /* Input fields styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Separator line styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 30px 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        background-color: #f0f0f0;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 10px;
        font-weight: 600;
        transition: background-color 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #e9ecef;
    }
    
    /* Card-like containers */
    .element-container {
        animation: fadeIn 0.5s ease-in-out;
    }
    
    /* Checkbox styling */
    .stCheckbox {
        padding: 10px;
        border-radius: 8px;
        transition: background-color 0.3s ease;
    }
    
    .stCheckbox:hover {
        background-color: rgba(102, 126, 234, 0.1);
    }
    
    /* Select box styling */
    .stSelectbox>div>div>div {
        border-radius: 10px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #667eea;
        font-weight: 700;
    }
</style>
"""

# --- Page Configuration ---
st.set_page_config(
    page_title="Enhanced VLIVE Google Sheets Viewer & Form",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📺"
)

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Main Title with Emoji ---
st.title("📺 Enhanced VLIVE Google Sheets Data Viewer & Form")
st.markdown("""
<div style='text-align: center; margin-bottom: 30px;'>
    <p style='font-size: 1.2rem; color: #666;'>
        A dynamic and colorful application to view data from Google Sheets, embed video links, and submit new data.
    </p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.markdown("# 🔐 Configuration Panel")
st.sidebar.markdown("---")

# Authentication Section
st.sidebar.header("🔑 Google Sheets Authentication")
st.sidebar.markdown("""
<div style='background-color: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; margin-bottom: 15px;'>
    <small>Upload your Google Service Account JSON file to authenticate.</small>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader(
    "Upload Service Account JSON", 
    type="json", 
    help="Upload the JSON key file for your Google Service Account with access to Google Sheets API."
)

# Sheet Configuration Section
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Sheet Configuration")

sheet_id = st.sidebar.text_input(
    "Google Sheet ID", 
    value=DEFAULT_SHEET_ID,
    help="The unique ID from your Google Sheet URL (the long string between /d/ and /edit)."
)

video_col_name = st.sidebar.text_input(
    "Video Link Column Name", 
    value=DEFAULT_VIDEO_COLUMN_NAME,
    help="The exact name of the column containing the video URLs (case-sensitive)."
)

# Webhook Configuration Section
st.sidebar.markdown("---")
st.sidebar.header("🔗 Webhook Configuration")
st.sidebar.markdown("""
<div style='background-color: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; margin-bottom: 15px;'>
    <small>Optional: Configure a webhook to receive form submissions.</small>
</div>
""", unsafe_allow_html=True)

webhook_url = st.sidebar.text_input(
    "Webhook URL",
    placeholder="https://your.webhook.site/endpoint",
    help="URL to send form data to upon submission (optional)."
)

# Display Settings Section
st.sidebar.markdown("---")
st.sidebar.header("🎨 Display Settings")

items_per_page = st.sidebar.slider(
    "Videos Per Page",
    min_value=2,
    max_value=20,
    value=10,
    step=2,
    help="Number of videos to display per page in the viewer."
)

video_columns = st.sidebar.radio(
    "Video Layout",
    options=[1, 2, 3],
    index=1,
    help="Number of columns for video display."
)

show_index = st.sidebar.checkbox(
    "Show Row Numbers",
    value=True,
    help="Display row numbers in the data table."
)

# --- Helper Functions ---

@st.cache_resource(ttl=3600)
def get_gspread_client(service_account_info):
    """Authenticates gspread using the service account info with proper credentials."""
    try:
        # Create credentials object
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )
        
        # Authorize gspread client
        gc = gspread.authorize(credentials)
        return gc
    except Exception as e:
        st.error(f"❌ Authentication failed. Error details: {str(e)}")
        st.info("💡 Make sure your JSON file contains valid service account credentials and that the Google Sheets API is enabled.")
        return None

@st.cache_data(ttl=600)
def load_data(_gc, sheet_id, worksheet_name):
    """Loads data from the specified worksheet of the Google Sheet."""
    try:
        sh = _gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df, None
    except SpreadsheetNotFound:
        error_msg = f"Spreadsheet with ID '{sheet_id}' not found. Please check the Sheet ID and ensure the service account has access."
        return pd.DataFrame(), error_msg
    except WorksheetNotFound:
        error_msg = f"Worksheet '{worksheet_name}' not found in the spreadsheet."
        return pd.DataFrame(), error_msg
    except Exception as e:
        error_msg = f"Error loading data: {str(e)}"
        return pd.DataFrame(), error_msg

def get_worksheet_list(_gc, sheet_id):
    """Retrieves list of worksheet names from the spreadsheet."""
    try:
        spreadsheet = _gc.open_by_key(sheet_id)
        worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
        return worksheet_titles, None
    except SpreadsheetNotFound:
        return [], f"Spreadsheet with ID '{sheet_id}' not found."
    except Exception as e:
        return [], f"Could not retrieve worksheet list. Error: {str(e)}"

def extract_video_id(url):
    """Extracts video ID from various video platforms."""
    # This is a placeholder - you can expand this for different platforms
    if 'youtube.com' in url or 'youtu.be' in url:
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[-1].split('?')[0]
        elif 'v=' in url:
            return url.split('v=')[-1].split('&')[0]
    return None

def format_timestamp(timestamp):
    """Formats timestamp for display."""
    try:
        if isinstance(timestamp, str):
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%B %d, %Y at %I:%M %p")
        return timestamp
    except:
        return timestamp

# --- Main Application Logic ---
if uploaded_file is not None:
    # Read and parse the uploaded JSON file
    try:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        service_account_info = json.load(stringio)
        
        # Validate that it's a proper service account file
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in service_account_info]
        
        if missing_fields:
            st.error(f"❌ Invalid Service Account JSON file. Missing fields: {', '.join(missing_fields)}")
            st.stop()
            
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file uploaded. Please ensure it is the correct Service Account key file.")
        st.info("💡 The file should be downloaded from Google Cloud Console under 'Service Accounts'.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        st.stop()

    # Authenticate with Google Sheets
    with st.spinner("🔄 Authenticating with Google Sheets..."):
        gc = get_gspread_client(service_account_info)
    
    if gc:
        st.sidebar.success("✅ Authentication successful!")
        
        # Display service account email
        service_email = service_account_info.get('client_email', 'Unknown')
        st.sidebar.info(f"📧 Connected as:\n`{service_email}`")
        
        # Retrieve worksheet list
        worksheet_titles, error = get_worksheet_list(gc, sheet_id)
        
        if error:
            st.error(f"❌ {error}")
            st.info("💡 Make sure you've shared your Google Sheet with the service account email shown in the sidebar.")
            st.stop()
        
        if not worksheet_titles:
            st.error("❌ No worksheets found in the spreadsheet.")
            st.stop()
        
        # Worksheet selection
        st.sidebar.markdown("---")
        st.sidebar.header("📑 Worksheet Selection")
        selected_worksheet = st.sidebar.selectbox(
            "Select Worksheet (Tab)",
            options=worksheet_titles,
            help="Choose the tab in your Google Sheet to load data from."
        )
        
        # Add a refresh button
        if st.sidebar.button("🔄 Refresh Data", help="Clear cache and reload data from Google Sheets"):
            st.cache_data.clear()
            st.rerun()

        # --- Create Tabs for Different Functions ---
        viewer_tab, form_tab, analytics_tab = st.tabs([
            "👁️ Data Viewer", 
            "📝 Data Submission Form",
            "📊 Analytics Dashboard"
        ])

        # ==========================================
        # DATA VIEWER TAB
        # ==========================================
        with viewer_tab:
            st.markdown("## 📊 Data Viewer")
            
            # Load data
            with st.spinner("📥 Loading data from Google Sheets..."):
                df, load_error = load_data(gc, sheet_id, selected_worksheet)
            
            if load_error:
                st.error(f"❌ {load_error}")
                st.stop()
            
            if not df.empty:
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📝 Total Records", len(df))
                
                with col2:
                    video_count = 0
                    if video_col_name in df.columns:
                        video_count = df[video_col_name].astype(str).str.startswith('http').sum()
                    st.metric("🎬 Video Links", video_count)
                
                with col3:
                    st.metric("📋 Columns", len(df.columns))
                
                with col4:
                    if 'Timestamp' in df.columns:
                        recent_count = len(df[df['Timestamp'].astype(str).str.contains('2025')])
                        st.metric("🆕 Recent (2025)", recent_count)
                    else:
                        st.metric("📊 Data Quality", "N/A")
                
                st.markdown("---")
                
                # Advanced Filtering Section
                st.markdown("### 🔍 Filter & Search")
                
                filter_col1, filter_col2 = st.columns([3, 1])
                
                with filter_col1:
                    search_term = st.text_input(
                        "Search across all columns",
                        help="Enter text to filter the table and videos.",
                        placeholder="Type to search titles, descriptions, URLs..."
                    )
                
                with filter_col2:
                    # Column-specific filtering
                    if len(df.columns) > 0:
                        filter_column = st.selectbox(
                            "Filter by column",
                            options=["All Columns"] + list(df.columns)
                        )
                
                # Apply filters
                df_filtered = df.copy()
                
                if search_term:
                    if filter_column == "All Columns":
                        df_filtered = df[df.apply(
                            lambda row: row.astype(str).str.contains(search_term, case=False).any(), 
                            axis=1
                        )]
                    else:
                        df_filtered = df[df[filter_column].astype(str).str.contains(search_term, case=False)]
                
                # Display filtered results count
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 15px; border-radius: 10px; color: white; text-align: center; margin: 20px 0;'>
                    <h3 style='margin: 0; color: white;'>Displaying {len(df_filtered)} of {len(df)} Records</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Data table with options
                if show_index:
                    st.dataframe(df_filtered, use_container_width=True, height=400)
                else:
                    st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True, height=400)
                
                # Download options
                csv = df_filtered.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name=f'{selected_worksheet}_filtered_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv',
                )
                
                st.markdown("---")
                
                # ==========================================
                # VIDEO EMBEDDING SECTION
                # ==========================================
                st.markdown("### 🎬 Embedded Videos")
                
                if video_col_name in df_filtered.columns:
                    video_data = df_filtered[
                        df_filtered[video_col_name].astype(str).str.startswith('http')
                    ].reset_index(drop=True)
                    
                    if not video_data.empty:
                        st.success(f"✨ Found **{len(video_data)}** video(s) matching your criteria")
                        
                        # Pagination
                        if len(video_data) > items_per_page:
                            total_pages = (len(video_data) - 1) // items_per_page + 1
                            
                            page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
                            with page_col2:
                                current_page = st.number_input(
                                    f"Page (1-{total_pages})",
                                    min_value=1,
                                    max_value=total_pages,
                                    value=1,
                                    key="video_page"
                                )
                            
                            start_idx = (current_page - 1) * items_per_page
                            end_idx = start_idx + items_per_page
                            video_data_page = video_data.iloc[start_idx:end_idx]
                        else:
                            video_data_page = video_data
                        
                        # Video display
                        cols = st.columns(video_columns)
                        
                        for index, row in video_data_page.iterrows():
                            col = cols[index % video_columns]
                            
                            with col:
                                # Card-like container for each video
                                with st.container():
                                    # Determine title
                                    other_cols = [c for c in df_filtered.columns if c != video_col_name]
                                    
                                    if other_cols and 'Title' in other_cols:
                                        title_text = str(row['Title'])
                                    elif other_cols:
                                        title_text = str(row[other_cols[0]])
                                    else:
                                        title_text = f"Record {index + 1}"
                                    
                                    st.markdown(f"#### 🎥 {title_text}")
                                    
                                    # Expandable details
                                    with st.expander("📋 View Full Details", expanded=False):
                                        for c in other_cols:
                                            value = row[c]
                                            if c == 'Timestamp':
                                                value = format_timestamp(value)
                                            st.markdown(f"**{c}:** {value}")
                                    
                                    # Video embed
                                    try:
                                        st.video(row[video_col_name])
                                    except Exception as e:
                                        st.error(f"❌ Error loading video: {str(e)}")
                                        st.code(row[video_col_name])
                                    
                                    st.markdown("---")
                        
                        # Page navigation summary
                        if len(video_data) > items_per_page:
                            st.info(f"📄 Showing videos {start_idx + 1}-{min(end_idx, len(video_data))} of {len(video_data)}")
                    else:
                        st.warning(f"⚠️ No valid video links found in column **'{video_col_name}'** in the filtered data.")
                        st.info("💡 Video links must start with 'http' to be displayed.")
                else:
                    st.error(f"❌ Column **'{video_col_name}'** not found in the worksheet.")
                    st.info(f"📋 Available columns: **{', '.join(df_filtered.columns)}**")
            else:
                st.warning("⚠️ The worksheet appears to be empty or has no data.")
                st.info("💡 Please check the worksheet content and ensure your service account has proper permissions.")

        # ==========================================
        # DATA SUBMISSION FORM TAB
        # ==========================================
        with form_tab:
            st.markdown("## 📝 Submit New Data")
            st.markdown("""
            <div style='background-color: rgba(102, 126, 234, 0.1); padding: 20px; border-radius: 15px; margin-bottom: 25px;'>
                <p style='margin: 0; color: #666;'>
                    Use this form to submit new video links and data to your Google Sheet and/or a webhook endpoint.
                    All submissions are timestamped automatically.
                </p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("data_submission_form", clear_on_submit=True):
                st.markdown("### 📋 Form Fields")
                
                # Dynamic form based on existing columns
                form_data = {}
                
                # Title field
                title = st.text_input(
                    "📌 Title / Description",
                    max_chars=200,
                    help="Enter a descriptive title for this entry"
                )
                form_data['Title'] = title
                
                # Video URL field (required)
                video_url_input = st.text_input(
                    f"🎬 {video_col_name} (Required)",
                    placeholder="https://example.com/video.mp4",
                    help="Enter the full URL of the video",
                    key="video_url_form"
                )
                form_data[video_col_name] = video_url_input
                
                # Additional data field
                additional_data = st.text_area(
                    "📝 Additional Information",
                    help="Enter any additional data or notes",
                    height=100
                )
                form_data['Additional_Data'] = additional_data
                
                # Optional: Category/Tags
                col1, col2 = st.columns(2)
                
                with col1:
                    category = st.text_input(
                        "🏷️ Category",
                        placeholder="e.g., Tutorial, Review, Demo"
                    )
                    form_data['Category'] = category
                
                with col2:
                    tags = st.text_input(
                        "🔖 Tags",
                        placeholder="tag1, tag2, tag3"
                    )
                    form_data['Tags'] = tags
                
                st.markdown("---")
                st.markdown("### ⚙️ Submission Options")
                
                # Submission options
                col1, col2 = st.columns(2)
                
                with col1:
                    submit_to_sheet = st.checkbox(
                        f"📊 Append to Google Sheet: **{selected_worksheet}**",
                        value=True,
                        help="Add this data as a new row in the selected worksheet"
                    )
                
                with col2:
                    submit_to_webhook = st.checkbox(
                        "🔗 Send to Webhook",
                        value=False,
                        disabled=(not webhook_url),
                        help="Send this data to the configured webhook URL"
                    )
                
                st.markdown("---")
                
                # Submit button
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    submitted = st.form_submit_button(
                        "🚀 Submit Data",
                        type="primary",
                        use_container_width=True
                    )

                # Handle form submission
                if submitted:
                    if not video_url_input:
                        st.error("❌ The Video URL field is required. Please enter a valid URL.")
                    elif not video_url_input.startswith('http'):
                        st.error("❌ Please enter a valid URL starting with http:// or https://")
                    else:
                        # Add timestamp
                        form_data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        success_count = 0
                        total_operations = sum([submit_to_sheet, submit_to_webhook])
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # 1. Append to Google Sheet
                        if submit_to_sheet:
                            status_text.text("📊 Submitting to Google Sheets...")
                            try:
                                sh = gc.open_by_key(sheet_id)
                                worksheet = sh.worksheet(selected_worksheet)
                                
                                # Prepare data as a list
                                values = [
                                    form_data.get("Title", ""),
                                    form_data.get(video_col_name, ""),
                                    form_data.get("Additional_Data", ""),
                                    form_data.get("Category", ""),
                                    form_data.get("Tags", ""),
                                    form_data.get("Timestamp", "")
                                ]
                                
                                worksheet.append_row(values)
                                st.success(f"✅ Successfully added data to worksheet: **{selected_worksheet}**")
                                success_count += 1
                                progress_bar.progress(success_count / total_operations)
                                
                                # Clear cache
                                st.cache_data.clear()
                                
                            except Exception as e:
                                st.error(f"❌ Failed to append to Google Sheet: {str(e)}")
                                progress_bar.progress(success_count / total_operations)

                        # 2. Send to Webhook
                        if submit_to_webhook and webhook_url:
                            status_text.text("🔗 Sending to webhook...")
                            try:
                                response = requests.post(
                                    webhook_url,
                                    json=form_data,
                                    timeout=10,
                                    headers={'Content-Type': 'application/json'}
                                )
                                
                                if response.status_code in [200, 201, 202]:
                                    st.success(f"✅ Successfully sent data to webhook")
                                    success_count += 1
                                else:
                                    st.warning(f"⚠️ Webhook returned status code: {response.status_code}")
                                    st.code(response.text)
                                
                                progress_bar.progress(success_count / total_operations)
                                
                            except requests.exceptions.Timeout:
                                st.error("❌ Webhook request timed out (10 seconds)")
                                progress_bar.progress(success_count / total_operations)
                            except requests.exceptions.RequestException as e:
                                st.error(f"❌ Failed to send to webhook: {str(e)}")
                                progress_bar.progress(success_count / total_operations)
                        
                        elif submit_to_webhook and not webhook_url:
                            st.warning("⚠️ Webhook URL not configured in the sidebar")
                        
                        # Completion
                        status_text.empty()
                        progress_bar.empty()
                        
                        if success_count == total_operations:
                            st.balloons()
                            st.success(f"🎉 All operations completed successfully! ({success_count}/{total_operations})")
                            time.sleep(2)
                            st.rerun()
                        elif success_count > 0:
                            st.info(f"⚠️ Partially completed: {success_count}/{total_operations} operations succeeded")
                        else:
                            st.error("❌ All operations failed. Please check your configuration and try again.")

        # ==========================================
        # ANALYTICS DASHBOARD TAB
        # ==========================================
        with analytics_tab:
            st.markdown("## 📊 Analytics Dashboard")
            
            # Load data for analytics
            df, load_error = load_data(gc, sheet_id, selected_worksheet)
            
            if load_error or df.empty:
                st.warning("⚠️ No data available for analytics")
            else:
                # Overview metrics
                st.markdown("### 📈 Overview Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "📝 Total Entries",
                        len(df),
                        help="Total number of records in the sheet"
                    )
                
                with col2:
                    if video_col_name in df.columns:
                        video_count = df[video_col_name].astype(str).str.startswith('http').sum()
                        st.metric(
                            "🎬 Videos",
                            video_count,
                            help="Number of valid video links"
                        )
                    else:
                        st.metric("🎬 Videos", "N/A")
                
                with col3:
                    if 'Category' in df.columns:
                        unique_categories = df['Category'].nunique()
                        st.metric(
                            "🏷️ Categories",
                            unique_categories,
                            help="Number of unique categories"
                        )
                    else:
                        st.metric("🏷️ Categories", "N/A")
                
                with col4:
                    st.metric(
                        "📋 Columns",
                        len(df.columns),
                        help="Number of data columns"
                    )
                
                st.markdown("---")
                
                # Time-based analytics
                if 'Timestamp' in df.columns:
                    st.markdown("### 📅 Timeline Analysis")
                    
                    try:
                        df['Timestamp_Parsed'] = pd.to_datetime(df['Timestamp'], errors='coerce')
                        df_timeline = df.dropna(subset=['Timestamp_Parsed'])
                        
                        if not df_timeline.empty:
                            df_timeline['Date'] = df_timeline['Timestamp_Parsed'].dt.date
                            daily_counts = df_timeline.groupby('Date').size().reset_index(name='Count')
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 📊 Entries by Date")
                                st.bar_chart(daily_counts.set_index('Date'))
                            
                            with col2:
                                st.markdown("#### 📈 Recent Activity")
                                recent = daily_counts.tail(7)
                                st.dataframe(
                                    recent.rename(columns={'Date': 'Date', 'Count': 'Submissions'}),
                                    use_container_width=True,
                                    hide_index=True
                                )
                        else:
                            st.info("💡 No valid timestamps found for timeline analysis")
                    
                    except Exception as e:
                        st.warning(f"⚠️ Could not parse timestamps: {str(e)}")
                
                st.markdown("---")
                
                # Category distribution
                if 'Category' in df.columns:
                    st.markdown("### 🏷️ Category Distribution")
                    
                    category_counts = df['Category'].value_counts().reset_index()
                    category_counts.columns = ['Category', 'Count']
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.bar_chart(category_counts.set_index('Category'))
                    
                    with col2:
                        st.dataframe(
                            category_counts,
                            use_container_width=True,
                            hide_index=True
                        )
                
                st.markdown("---")
                
                # Data quality metrics
                st.markdown("### ✅ Data Quality Metrics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Completeness
                    total_cells = len(df) * len(df.columns)
                    filled_cells = df.count().sum()
                    completeness = (filled_cells / total_cells * 100) if total_cells > 0 else 0
                    
                    st.metric(
                        "📊 Data Completeness",
                        f"{completeness:.1f}%",
                        help="Percentage of non-empty cells"
                    )
                
                with col2:
                    # Valid video links
                    if video_col_name in df.columns:
                        valid_videos = df[video_col_name].astype(str).str.startswith('http').sum()
                        total_videos = len(df)
                        video_validity = (valid_videos / total_videos * 100) if total_videos > 0 else 0
                        
                        st.metric(
                            "🎬 Valid Video Links",
                            f"{video_validity:.1f}%",
                            help="Percentage of rows with valid video URLs"
                        )
                    else:
                        st.metric("🎬 Valid Video Links", "N/A")
                
                with col3:
                    # Duplicate check
                    if 'Title' in df.columns:
                        duplicates = df.duplicated(subset=['Title']).sum()
                        st.metric(
                            "🔍 Duplicate Titles",
                            duplicates,
                            help="Number of duplicate title entries",
                            delta=f"-{duplicates}" if duplicates > 0 else "0"
                        )
                    else:
                        st.metric("🔍 Duplicates", "N/A")
                
                # Column statistics
                st.markdown("---")
                st.markdown("### 📋 Column Statistics")
                
                col_stats = []
                for col in df.columns:
                    non_null = df[col].count()
                    null_count = len(df) - non_null
                    unique_values = df[col].nunique()
                    
                    col_stats.append({
                        'Column': col,
                        'Non-Empty': non_null,
                        'Empty': null_count,
                        'Unique Values': unique_values,
                        'Completeness': f"{(non_null/len(df)*100):.1f}%"
                    })
                
                st.dataframe(
                    pd.DataFrame(col_stats),
                    use_container_width=True,
                    hide_index=True
                )

else:
    # Landing page when no file is uploaded
    st.markdown(""
    <div style='text-align: center; padding: 50px 20px;'>
        <h2 style='color: #667eea;'>Welcome!</h2>
        <p style='font-size: 1.1rem; color: #666; margin: 20px 0;'>
            Get started by uploading your Google Service Account JSON file in the sidebar.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Setup instructions
    st.markdown("## 📚 Quick Setup Guide")
    
    with st.expander("**Step 1: Create a Google Service Account** 🔑", expanded=True):
        st.markdown(""
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select an existing one
        3. Enable the **Google Sheets API** and **Google Drive API**
        4. Go to **IAM & Admin** → **Service Accounts**
        5. Click **Create Service Account**
        6. Give it a name and click **Create**
        7. Skip the optional steps and click **Done**
        8. Click on the newly created service account
        9. Go to **Keys** tab → **Add Key** → **Create New Key**
        10. Choose **JSON** format and download the file
        """)
    
    with st.expander("**Step 2: Share Your Google Sheet** 📊"):
        st.markdown(""
        1. Open your Google Sheet
        2. Click the **Share** button (top right)
        3. Share it with the email address from your service account JSON file
           - Look for the `client_email` field in your JSON file
           - It looks like: `your-service-account@project-id.iam.gserviceaccount.com`
        4. Give it **Editor** permissions
        5. Click **Send**
        """)
    
    with st.expander("**Step 3: Get Your Sheet ID** 🆔"):
        st.markdown(""
        Your Google Sheet ID is in the URL:
        
        ```
        https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
        ```
        
        Copy the long string between `/d/` and `/edit` - that's your Sheet ID!
        """)
    
    with st.expander("**Step 4: Upload and Configure** ⚙️"):
        st.markdown(""
        1. Upload your service account JSON file using the sidebar uploader
        2. Enter your Sheet ID in the configuration section
        3. Specify the column name that contains video URLs
        4. (Optional) Add a webhook URL for form submissions
        5. Start viewing and managing your data!
        """)
    
    st.markdown("---")
    
    # Features showcase
    st.markdown("## ✨ Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 👁️ Data Viewer
        - View all your Google Sheets data
        - Advanced search and filtering
        - Embedded video playback
        - Pagination for large datasets
        - Download filtered data as CSV
        """)
    
    with col2:
        st.markdown("""
        ### 📝 Submission Form
        - Add new entries easily
        - Automatic timestamping
        - Webhook integration
        - Form validation
        - Real-time progress tracking
        """)
    
    with col3:
        st.markdown("""
        ### 📊 Analytics
        - Overview statistics
        - Timeline analysis
        - Category distribution
        - Data quality metrics
        - Column statistics
        """)

# --- Sidebar Footer ---
st.sidebar.markdown("---")
st.sidebar.markdown(""
<div style='text-align: center; padding: 15px; background-color: rgba(255,255,255,0.2); border-radius: 10px;'>
    <p style='margin: 5px 0; font-size: 0.9rem;'><strong>📺 VLIVE Sheets Viewer</strong></p>
    <p style='margin: 5px 0; font-size: 0.8rem;'>Version 2.0</p>
    <p style='margin: 5px 0; font-size: 0.7rem;'>Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)

# Help section in sidebar
with st.sidebar.expander("❓ Need Help?"):
    st.markdown(""
    **Common Issues:**
    
    - **Authentication fails**: Check JSON file format
    - **Sheet not found**: Verify Sheet ID and sharing
    - **No videos showing**: Check column name spelling
    - **Webhook fails**: Verify URL and endpoint
    
    **Tips:**
    - Use the refresh button to update data
    - Column names are case-sensitive
    - Video URLs must start with 'http'
    ""
