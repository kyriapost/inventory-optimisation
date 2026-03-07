import streamlit as st 
import os 
  
st.title('Methodology') 
st.caption('Full mathematical derivation of the model and modelling decisions.') 
  
# Read and render the methodology markdown 
methodology_path = os.path.join( 
    os.path.dirname(__file__), '..', '..', 'docs', 'methodology.md' 
) 
  
try: 
    with open(methodology_path, 'r', encoding='utf-8') as f: 
        content = f.read() 
    st.markdown(content) 
except FileNotFoundError: 
    st.error('docs/methodology.md not found. Run from project root.') 
  
st.divider() 
st.caption( 
    'Source: docs/methodology.md · ' 
    '[View on GitHub](https://github.com/kyriapost/inventory-optimisation/blob/main/docs/methodology.md)' 
)