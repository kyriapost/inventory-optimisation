import streamlit as st 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from scipy.stats import nbinom 
import sys, os 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..')) 
  
from app.streamlit_app import load_data 
  
st.title('SKU Explorer') 
st.caption('Select a SKU to explore its demand history, fitted distribution, and optimised policy.') 
  
try: 
    demand_df, results_df, metadata = load_data() 
except Exception as e: 
    st.error(f'Data load failed: {e}') 
    st.stop() 
  
# ── SKU selector ────────────────────────────────────────────────── 
skus = sorted(results_df['sku_id'].tolist()) 
  
# Merge with description for readable labels 
meta_map = dict(zip(metadata['sku_id'], metadata['description'])) 
sku_labels = {s: f'{s} — {meta_map.get(s, "Unknown")[:40]}' for s in skus} 
  
selected_sku = st.selectbox( 
    'Select SKU', 
    options=skus, 
    format_func=lambda s: sku_labels[s], 
) 
  
# ── Load data for selected SKU ───────────────────────────────────── 
sku_demand  = demand_df[demand_df['sku_id'] == selected_sku]['demand'].values 
sku_weeks   = demand_df[demand_df['sku_id'] == selected_sku]['week_start'] 
sku_result  = results_df[results_df['sku_id'] == selected_sku].iloc[0] 
  
# ── Policy parameters panel ─────────────────────────────────────── 
st.subheader(f'Policy Parameters — {selected_sku}') 
  
col1, col2, col3, col4, col5 = st.columns(5) 
col1.metric('Reorder Point (s)',  int(sku_result['reorder_point'])) 
col2.metric('Order Up To (S)',    int(sku_result['order_up_to'])) 
col3.metric('Safety Stock',       int(sku_result['safety_stock'])) 
col4.metric('NB cost/unit',       f'£{sku_result["cost_per_unit"]:.4f}') 
col5.metric('Q4 Service Level',   f'{sku_result["holdout_sl"]:.3f}')
# ── Demand history chart ────────────────────────────────────────── 
st.subheader('Demand History') 
  
fig, ax = plt.subplots(figsize=(13, 4)) 
ax.bar(range(len(sku_demand)), sku_demand, color='#2E75B6', alpha=0.7, 
width=0.8) 
ax.axhline(sku_demand.mean(), color='red', linestyle='--', linewidth=1.5, 
           label=f'Mean {sku_demand.mean():.1f}') 
ax.set_xlabel('Week') 
ax.set_ylabel('Units') 
ax.set_title(f'Weekly Demand — {selected_sku}') 
ax.legend() 
st.pyplot(fig) 
plt.close() 
  
# ── NB distribution fit ─────────────────────────────────────────── 
st.subheader('Fitted Negative Binomial Distribution') 
  
col1, col2 = st.columns(2) 
  
with col1: 
    nb_n = sku_result['nb_n'] 
    nb_p = sku_result['nb_p'] 
  
    x_max = int(np.percentile(sku_demand, 99)) + 10 
    x     = np.arange(0, x_max) 
    pmf   = nbinom.pmf(x, nb_n, nb_p) 
  
    fig, ax = plt.subplots(figsize=(7, 4)) 
    # Empirical histogram (normalised) 
    ax.hist(sku_demand, bins=30, density=True, alpha=0.5, 
            color='#2E75B6', label='Observed demand', edgecolor='white') 
    # NB PMF overlay 
    ax.plot(x, pmf, 'r-', linewidth=2, label=f'NB fit (n={nb_n:.2f}, p={nb_p:.3f})') 
    ax.set_xlabel('Weekly demand (units)') 
    ax.set_ylabel('Probability') 
    ax.set_title('Empirical vs Fitted Distribution') 
    ax.legend(fontsize=9) 
    st.pyplot(fig) 
    plt.close() 
  
with col2: 
    st.markdown('**Distribution diagnostics**') 
    ks_ok = sku_result['nb_ks_pvalue'] > 0.05 
    conv  = sku_result['nb_converged'] 
    st.metric('V/M ratio',     f'{sku_result["nb_vm_ratio"]:.2f}', 
              help='> 1.3 = overdispersed — NB preferred over Poisson') 
    st.metric('KS p-value',    f'{sku_result["nb_ks_pvalue"]:.4f}', 
              delta='Good fit' if ks_ok else 'Poor fit', 
              delta_color='normal' if ks_ok else 'inverse') 
    st.metric('MLE converged', 'Yes' if conv else 'No', 
              delta_color='normal' if conv else 'inverse') 
    st.divider() 
    st.markdown('**Baseline comparison**') 
    st.metric('6-week heuristic cost/unit', 
f'£{sku_result["heuristic_cost"]:.4f}') 
    st.metric('Normal (s,S) cost/unit',     
f'£{sku_result["normal_cost"]:.4f}') 
    saving = (sku_result['heuristic_cost'] - sku_result['cost_per_unit']) / sku_result['heuristic_cost'] * 100 
    st.metric('Saving vs heuristic', f'{saving:.1f}%', 
              delta_color='normal' if saving > 0 else 'inverse') 