import sys, os 
sys.path.insert(0, 
os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
  
import streamlit as st 
import pandas as pd 
  
st.set_page_config( 
    page_title='Inventory Optimisation', 
    page_icon='📦', 
    layout='wide', 
    initial_sidebar_state='expanded', 
) 
  
  
@st.cache_data(ttl=3600) 
def load_data(): 
    """ 
    Loads all data from PostgreSQL once per hour. 
    Cached so page navigation does not re-query the database. 
    ttl=3600: cache expires after 1 hour. 
    """ 
    from src.data.loader import ( 
        load_weekly_demand, 
        load_policy_results, 
        load_sku_metadata, 
    ) 
    demand_df  = load_weekly_demand(min_weeks=40) 
    results_df = load_policy_results() 
    metadata   = load_sku_metadata() 
    return demand_df, results_df, metadata 
  
  
# ── Sidebar ─────────────────────────────────────────────────────── 
with st.sidebar: 
    st.title('📦 Inventory Optimiser') 
    st.caption('Data-driven (s,S) policy optimisation') 
    st.divider() 
    st.markdown('**Navigation**') 
    st.markdown('Use the pages above to navigate.') 
    st.divider() 
    st.markdown('**About**') 
    st.caption( 
        'Fits a Negative Binomial demand distribution per SKU ' 
        'and computes cost-minimising reorder policies. ' 
        'Built on the UCI Online Retail dataset.' 
    ) 
    st.markdown('[Methodology](docs/methodology.md)', unsafe_allow_html=False) 
    st.markdown('[GitHub](https://github.com/kyriakos/inventory-optimisation)') 

try: 
    _, results_df, _ = load_data() 
    st.sidebar.divider() 
    st.sidebar.caption(f'Last run: {results_df["run_date"].iloc[0]}') 
    st.sidebar.caption(f'{len(results_df):,} SKUs in database') 
except: 
    pass 
  
  
# ── Main landing page ───────────────────────────────────────────── 
st.title('📦 Inventory Optimisation Dashboard') 
st.markdown( 
    'Data-driven **(s,S)** inventory policy optimisation using ' 
    'Negative Binomial demand modelling. ' 
    'Navigate using the sidebar to explore results.' 
) 
# Load and display quick stats 
try: 
    demand_df, results_df, metadata = load_data() 
  
    col1, col2, col3, col4 = st.columns(4) 
    col1.metric('SKUs optimised',          f'{len(results_df):,}') 
    col2.metric('Beat heuristic (Q4)', f'{results_df["beats_heuristic"].mean()*100:.1f}%') 
    col3.metric('Mean service level', f'{results_df["holdout_sl"].mean():.3f}') 
    col4.metric('Avg cost saving', f'{((results_df["heuristic_cost"] - results_df["cost_per_unit"]) / results_df["heuristic_cost"] * 100).mean():.1f}%') 
  
except Exception as e: 
    st.error(f'Could not load data: {e}') 
    st.info('Make sure Docker is running and the batch pipeline has been executed.') 