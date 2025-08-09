# ProViewer
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app/)

An interactive web application built with Streamlit for 3D protein structure visualization.

- **Predict protein structures** from amino acid sequences via the ESMFold API.
- **Visualize local structure files** (PDB or CIF) by uploading them.
- **Fetch structures directly** from the AlphaFold Database using a UniProt ID.

## 🚀 Features
The application features a clean, tab-based interface for three main functionalities:

- **🔮 Predict**: Input an amino acid sequence to generate a 3D structure using ESMFold. The model's confidence score (average pLDDT) is also displayed.
- **📁 Upload**: Upload a `.pdb` or `.cif` file from your computer to view your own protein structures.
- **📦 AlphaFold DB**: Enter a UniProt accession ID to fetch and visualize the corresponding structure from the AlphaFold Protein Structure Database.

<p align="center">
  <img src="https://i.imgur.com/vHq8YyH.png" alt="App Screenshot" width="85%">
</p>

## 📦 Installation & Usage
To run this application on your local machine, please follow these steps.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yosshstd/ProViewer.git
    cd ProViewe
    ```
2.  **Install dependencies:**
    Create a `requirements.txt` file with the content below:
    ```
    streamlit
    requests
    streamlit-molstar
    biopython
    ```
    Then, install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the app:**
    Save the provided code as `app.py` and run the following command in your terminal:
    ```bash
    streamlit run app.py
    ```

## 🛠️ Built With
This project leverages several key technologies and services:

- [Streamlit](https://streamlit.io/): For building the interactive web interface.
- [Mol*](https://molstar.org/) (via [streamlit-molstar](https://github.com/n-yoshikawa/streamlit-molstar)): For high-performance 3D molecular visualization.
- [ESMFold API](https://esmatlas.com/about): For state-of-the-art protein structure prediction.
- [AlphaFold Database](https://alphafold.ebi.ac.uk/): For accessing a vast repository of predicted protein structures.
- [Biopython](https://biopython.org/): For parsing PDB/CIF files and calculating metrics.