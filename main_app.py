import streamlit as st
import requests
from streamlit_molstar import st_molstar_content
from Bio.PDB import PDBParser, MMCIFParser
from io import StringIO
import hashlib  # for stable unique keys per viewer

# --- Page Configuration ---
st.set_page_config(
    page_title="ProViewer",
    page_icon="🧬",
    layout="centered",
)

# --- Custom Styling (including hiding Streamlit's default UI elements) ---
HIDE_ST_STYLE = """
            <style>
            /* Main content area styling */
            .block-container {
                max-width: 1200px;
                padding-top: 0rem;
                padding-right: 3rem;
                padding-left: 3rem;
                padding-bottom: 1rem;
            }

            /* Hide Streamlit's default toolbar, menu, header, and footer */
            div[data-testid='stToolbar'] { visibility: hidden; height: 0%; position: fixed; }
            div[data-testid='stDecoration'] { visibility: hidden; height: 0%; position: fixed; }
            #MainMenu { visibility: hidden; height: 0%; }
            header { visibility: hidden; height: 0%; }
            footer { visibility: hidden; height: 0%; }
            </style>
"""
st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)

# --- Constants ---
MAX_SEQUENCE_LENGTH = 400
DEFAULT_SEQ = "PIAQIHILEGRSDEQKETLIREVSEAISRSLDAPLTSVRVIITEMAKGHFGIGGELASK"
VIEWER_HEIGHT = "600px"

# --- Helpers ---
def do_rerun():
    """Compatibility rerun for Streamlit >=1.27 (st.rerun) and older (experimental_rerun)."""
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()
    else:
        st.warning("Please update Streamlit to 1.27+ to enable rerun.")

def get_average_plddt(structure_str: str, fmt: str) -> float | None:
    """
    Calculate average pLDDT from PDB or CIF string using Biopython.
    Automatically detects 0–1 or 0–100 scale.

    Parameters
    ----------
    structure_str : str
        Structure content in PDB or mmCIF format.
    fmt : str
        'pdb' or 'cif'
    """
    fmt = fmt.lower()
    if fmt == 'pdb':
        parser = PDBParser(QUIET=True)
    elif fmt == 'cif':
        parser = MMCIFParser(QUIET=True)
    else:
        raise ValueError("Format must be 'pdb' or 'cif'")

    handle = StringIO(structure_str)
    try:
        structure = parser.get_structure("model", handle)
    except Exception:
        return None

    b_factors = [atom.bfactor for atom in structure.get_atoms()]
    if not b_factors:
        return None

    avg_plddt = sum(b_factors) / len(b_factors)
    # Normalize to 0–100 if values are in 0–1 range
    if avg_plddt <= 1.0:
        avg_plddt *= 100
    return avg_plddt

def make_viewer_key(prefix: str, content: str, fmt: str) -> str:
    """
    Make a stable unique key for the Mol* component.
    Uses MD5 of content + format so identical structures across tabs don't collide.
    """
    digest = hashlib.md5((fmt + ":" + content).encode("utf-8")).hexdigest()[:12]
    return f"molstar-{prefix}-{fmt}-{digest}"

@st.cache_data(show_spinner="Predicting structure with ESMFold...")
def fold_protein(sequence: str) -> str | None:
    """
    Call the ESMFold API to predict a protein structure in PDB format.
    Returns the PDB content as a string or None if an error occurs.
    """
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(
            'https://api.esmatlas.com/foldSequence/v1/pdb/',
            headers=headers,
            data=sequence,
            timeout=60
        )
        response.raise_for_status()
        return response.content.decode('utf-8')
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

# --- App Title ---
st.title("🧬 ProViewer")

# --- Tab Layout ---
tab_predict, tab_upload, tab_fetch = st.tabs(["🔮 Predict", "📁 Upload", "📦 AlphaFold DB"])

# --- Predict Tab ---
with tab_predict:
    st.subheader("Predict Protein Structure from Sequence")

    # Place the input field and submit button side-by-side
    with st.form("predict_form"):
        # Changed the column ratio to push the button further to the right
        col_text, col_btn = st.columns([8, 1], vertical_alignment="top")
        with col_text:
            sequence = st.text_area(
                "Amino Acid Sequence",
                value=DEFAULT_SEQ,
                height=80,
                key="predict_sequence"  # keep input across reruns
            ).strip()
            st.caption(f"Length: {len(sequence)} / {MAX_SEQUENCE_LENGTH} characters")
        with col_btn:
            # Add vertical space to align with the text area label
            st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
            submit_predict = st.form_submit_button("Predict")

    if submit_predict:
        if not sequence:
            st.warning("Please enter a sequence.")
        elif len(sequence) > MAX_SEQUENCE_LENGTH:
            st.error(f"Sequence too long: max {MAX_SEQUENCE_LENGTH} characters.")
        else:
            pdb_content = fold_protein(sequence)
            if pdb_content:
                st.session_state.predicted_content = pdb_content

    if "predicted_content" in st.session_state:
        pdb_to_show = st.session_state.predicted_content
        col1, col2 = st.columns([1, 4])
        with col1:
            avg_plddt = get_average_plddt(pdb_to_show, 'pdb')
            if avg_plddt is not None:
                st.metric("Avg. pLDDT", f"{avg_plddt:.2f}")
            st.download_button(
                "💾 Download PDB",
                data=pdb_to_show,
                file_name="predicted.pdb",
                mime="chemical/x-pdb",
                key="download_pdb_predict"
            )
            if st.button("🧹 Clear", key="clear_predict",
                         help="Clear the predicted structure view (input is kept)."):
                st.session_state.pop("predicted_content", None)
                do_rerun()
        with col2:
            st_molstar_content(
                pdb_to_show,
                file_format='pdb',
                height=VIEWER_HEIGHT,
                key=make_viewer_key("predict", pdb_to_show, "pdb")
            )

# --- Upload Tab ---
with tab_upload:
    st.subheader("Upload and View Protein Structure")
    uploaded = st.file_uploader("Upload PDB or CIF File", type=['pdb', 'cif'], key="file_uploader")

    # Persist uploaded content and format
    if uploaded:
        st.session_state.uploaded_content = uploaded.getvalue().decode('utf-8')
        st.session_state.uploaded_format = uploaded.name.split('.')[-1].lower()

    # Show uploaded structure and controls if present
    if "uploaded_content" in st.session_state:
        content = st.session_state.get("uploaded_content")
        fmt = st.session_state.get("uploaded_format")

        col1, col2 = st.columns([1, 4])
        with col1:
            avg = get_average_plddt(content, fmt)
            if avg is not None:
                st.metric("Avg. pLDDT", f"{avg:.2f}")
            if st.button(
                "🧹 Clear",
                key="clear_upload",
                help="Clear the uploaded structure view (file picker remains).",
                disabled=False
            ):
                # Clear stored data
                st.session_state.pop("uploaded_content", None)
                st.session_state.pop("uploaded_format", None)
                # IMPORTANT: also reset the uploader widget state
                st.session_state.pop("file_uploader", None)
                do_rerun()
        with col2:
            st_molstar_content(
                content,
                file_format=fmt,
                height=VIEWER_HEIGHT,
                key=make_viewer_key("upload", content, fmt)
            )

# --- AlphaFold DB Tab ---
with tab_fetch:
    st.subheader("Fetch Structure from AlphaFold DB")

    # Use a form to allow submission with the Enter key
    with st.form("afdb_form"):
        # Changed the column ratio to push the button further to the right
        col_input, col_btn = st.columns([8, 1], vertical_alignment="top")
        with col_input:
            uniprot_id = st.text_input(
                "Enter UniProt ID",
                "Q8W3K0",
                key="uniprot_id"
            ).strip()
        with col_btn:
            # Add vertical space to align with the text input label
            st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
            submit_fetch = st.form_submit_button("Fetch")

    if submit_fetch and uniprot_id:
        url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.cif"
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            st.session_state.af_structure = {
                "content": r.content.decode(),
                "id": uniprot_id
            }
        except requests.RequestException:
            st.error(f"Failed to fetch structure for {uniprot_id}. Please check the UniProt ID and try again.")

    if "af_structure" in st.session_state:
        content = st.session_state.af_structure["content"]
        id_ = st.session_state.af_structure["id"]

        col1, col2 = st.columns([1, 4])
        with col1:
            avg = get_average_plddt(content, 'cif')
            if avg is not None:
                st.metric("Avg. pLDDT", f"{avg:.2f}")
            st.download_button(
                "💾 Download CIF",
                data=content,
                file_name=f"AF-{id_}-F1-model_v4.cif",
                mime="chemical/x-mmcif",
                key=f"download_cif_afdb_{id_}"
            )
            if st.button("🧹 Clear", key="clear_afdb",
                         help="Clear the fetched AlphaFold structure view (UniProt ID input is kept)."):
                st.session_state.pop("af_structure", None)
                do_rerun()
        with col2:
            st_molstar_content(
                content,
                file_format='cif',
                height=VIEWER_HEIGHT,
                key=make_viewer_key("afdb", content, "cif")
            )