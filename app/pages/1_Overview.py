import streamlit as st 
import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np 
import sys, os 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..')) 
  
from app.streamlit_app import load_data 
  
st.title('Overview — Portfolio Performance') 
  
try: 
    demand_df, results_df, metadata = load_data() 
except Exception as e: 
    st.error(f'Data load failed: {e}') 
    st.stop() 
  
# ── Cost saving distribution ────────────────────
st.subheader('Cost Saving vs 6-Week Heuristic')   
results_df['saving_pct'] = ( 
    (results_df['heuristic_cost'] - results_df['cost_per_unit']) 
    / results_df['heuristic_cost'] * 100 
) 
  
col1, col2 = st.columns(2) 
  
with col1: 
    fig, ax = plt.subplots(figsize=(7, 4)) 
    ax.hist(results_df['saving_pct'], bins=40, color='#2E75B6', 
edgecolor='white') 
    ax.axvline(0,  color='red',  linestyle='--', linewidth=1.5, label='Breakeven') 
    ax.axvline(results_df['saving_pct'].mean(), color='gold', 
               linestyle='--', linewidth=1.5, 
               label=f'Mean {results_df["saving_pct"].mean():.1f}%') 
    ax.set_xlabel('Cost saving (%)') 
    ax.set_ylabel('Number of SKUs') 
    ax.set_title('Distribution of Cost Savings') 
    ax.legend(fontsize=9) 
    st.pyplot(fig) 
    plt.close() 
  
with col2: 
    fig, ax = plt.subplots(figsize=(7, 4)) 
    ax.hist(results_df['holdout_sl'].dropna(), bins=30, 
            color='#1E7145', edgecolor='white') 
    ax.axvline(0.95, color='red', linestyle='--', linewidth=1.5, label='95% target') 
    ax.set_xlabel('Service level') 
    ax.set_ylabel('Number of SKUs') 
    ax.set_title('Q4 Holdout Service Level Distribution') 
    ax.legend(fontsize=9) 
    st.pyplot(fig) 
    plt.close() 
  
# ── SCOPE metrics summary ───────────────────────────────────────── 
st.subheader('SCOPE.md Success Metrics') 
  
pass_rate = (results_df['nb_ks_pvalue'] > 0.05).mean() * 100 
beats_pct = results_df['beats_heuristic'].mean() * 100 
mean_sl   = results_df['holdout_sl'].mean() 
  
m1_ok = pass_rate >= 72 
m2_ok = beats_pct >= 50 
m3_ok = mean_sl   >= 0.90 
  
cols = st.columns(3) 
cols[0].metric('M1 NB KS pass rate',   f'{pass_rate:.1f}%', 
               delta='MET' if m1_ok else 'NOT MET', 
               delta_color='normal' if m1_ok else 'inverse') 
cols[1].metric('M2 Beats heuristic',   f'{beats_pct:.1f}%', 
               delta='MET' if m2_ok else 'NOT MET', 
               delta_color='normal' if m2_ok else 'inverse') 
cols[2].metric('M3 Mean service level', f'{mean_sl:.3f}', 
               delta='MET' if m3_ok else 'NOT MET', 
               delta_color='normal' if m3_ok else 'inverse') 
  
# ── Top 10 SKUs by cost saving ───────────────────────────────────── 
st.subheader('Top 10 SKUs by Cost Saving') 
top10 = ( 
    results_df.nlargest(10, 'saving_pct') 
    [['sku_id','reorder_point','order_up_to','safety_stock', 
      'cost_per_unit','heuristic_cost','saving_pct','holdout_sl']] 
    .rename(columns={ 
        'sku_id':'SKU', 'reorder_point':'s', 'order_up_to':'S', 
        'safety_stock':'SS', 'cost_per_unit':'NB cost/unit', 
        'heuristic_cost':'Heuristic cost/unit', 
        'saving_pct':'Saving %', 'holdout_sl':'Q4 SL'}) 
    .round(4) 
) 
st.dataframe(top10, use_container_width=True, hide_index=True)