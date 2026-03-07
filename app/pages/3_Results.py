import streamlit as st 
import pandas as pd 
import matplotlib.pyplot as plt 
import sys, os 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..')) 
  
from app.streamlit_app import load_data 
  
st.title('Results Dashboard') 
st.caption('Full optimisation results for all SKUs. Filter, sort, and download.')
try: 
    demand_df, results_df, metadata = load_data() 
except Exception as e: 
    st.error(f'Data load failed: {e}') 
    st.stop() 
  
# ── Filters ────────────────────────────────────────────────────── 
col1, col2, col3 = st.columns(3) 
  
with col1: 
    show_beats = st.checkbox('Show only SKUs beating heuristic', value=False) 
with col2: 
    min_sl = st.slider('Minimum Q4 service level', 0.0, 1.0, 0.0, 0.05) 
with col3: 
    sort_by = st.selectbox('Sort by', 
        ['saving_pct', 'cost_per_unit', 'holdout_sl', 'nb_vm_ratio'], 
        format_func=lambda x: { 
            'saving_pct':   'Cost saving %', 
            'cost_per_unit':'NB cost/unit', 
            'holdout_sl':   'Q4 service level', 
            'nb_vm_ratio':  'V/M ratio', 
        }[x]) 
  
# ── Compute saving % ────────────────────────────────────────────── 
results_df['saving_pct'] = ( 
    (results_df['heuristic_cost'] - results_df['cost_per_unit']) 
    / results_df['heuristic_cost'] * 100 
).round(2) 
  
# ── Apply filters ───────────────────────────────────────────────── 
filtered = results_df.copy() 
if show_beats: 
    filtered = filtered[filtered['beats_heuristic'] == True] 
if min_sl > 0: 
    filtered = filtered[filtered['holdout_sl'] >= min_sl] 
  
filtered = filtered.sort_values(sort_by, ascending=False) 
  
st.caption(f'Showing {len(filtered):,} of {len(results_df):,} SKUs') 
  
# ── Display table ───────────────────────────────────────────────── 
display_cols = { 
    'sku_id':          'SKU', 
    'reorder_point':   's', 
    'order_up_to':     'S', 
    'safety_stock':    'Safety Stock', 
    'cost_per_unit':   'NB Cost/Unit', 
    'heuristic_cost':  'Heuristic Cost/Unit', 
    'saving_pct':      'Saving %', 
    'holdout_sl':      'Q4 Service Level', 
    'nb_vm_ratio':     'V/M Ratio', 
    'nb_ks_pvalue':    'KS p-value', 
    'beats_heuristic': 'Beats Heuristic', 
} 
table = filtered[list(display_cols.keys())].rename(columns=display_cols).round(4) 
st.dataframe(table, use_container_width=True, hide_index=True) 
  
# ── Download button ─────────────────────────────────────────────── 
csv = table.to_csv(index=False) 
st.download_button( 
    label='Download results as CSV', 
    data=csv, 
    file_name='inventory_optimisation_results.csv', 
    mime='text/csv', 
) 
  
# ── Summary chart ───────────────────────────────────────────────── 
st.subheader('Cost per Unit: NB (s,S) vs 6-Week Heuristic') 
fig, ax = plt.subplots(figsize=(13, 5)) 
x = range(len(filtered)) 
ax.bar(x, filtered['heuristic_cost'], color='#CCCCCC', label='Heuristic', 
alpha=0.9) 
ax.bar(x, filtered['cost_per_unit'],  color='#2E75B6', label='NB (s,S)',  
alpha=0.8) 
ax.set_xlabel('SKU (sorted by saving)') 
ax.set_ylabel('Cost per unit (£)') 
ax.set_title('NB (s,S) vs 6-Week Heuristic Cost per Unit') 
ax.legend() 
ax.set_xticks([]) 
st.pyplot(fig) 
plt.close() 