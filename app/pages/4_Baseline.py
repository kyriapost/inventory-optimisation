import streamlit as st
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import sys, os 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..')) 
  
from app.streamlit_app import load_data 
  
st.title('Baseline Comparison') 
st.caption( 
    'Head-to-head comparison of the NB (s,S) policy against the ' 
    '6-week heuristic and Normal-demand (s,S) baseline.' 
) 
  
try: 
    demand_df, results_df, metadata = load_data() 
except Exception as e: 
    st.error(f'Data load failed: {e}') 
    st.stop() 
  
# ── Portfolio-level summary ─────────────────────────────────────── 
st.subheader('Portfolio Summary') 
  
nb_mean  = results_df['cost_per_unit'].mean() 
h_mean   = results_df['heuristic_cost'].mean() 
n_mean   = results_df['normal_cost'].mean() 
  
col1, col2, col3 = st.columns(3) 
col1.metric('NB (s,S) mean cost/unit',     f'£{nb_mean:.4f}') 
col2.metric('6-week heuristic cost/unit',  f'£{h_mean:.4f}', 
            delta=f'{(nb_mean-h_mean)/h_mean*100:.1f}% vs NB', 
            delta_color='inverse') 
col3.metric('Normal (s,S) cost/unit',      f'£{n_mean:.4f}', 
            delta=f'{(nb_mean-n_mean)/n_mean*100:.1f}% vs NB', 
            delta_color='inverse') 
  
# ── Scatter plot: NB cost vs heuristic cost ─────────────────────── 
st.subheader('NB (s,S) vs 6-Week Heuristic — Per SKU') 
  
fig, axes = plt.subplots(1, 2, figsize=(13, 5)) 
  
# NB vs Heuristic 
axes[0].scatter(results_df['heuristic_cost'], results_df['cost_per_unit'], 
                alpha=0.3, s=8, color='#1F3864') 
lim = max(results_df['heuristic_cost'].max(), 
results_df['cost_per_unit'].max()) 
axes[0].plot([0, lim], [0, lim], 'r--', linewidth=1.5, label='Break-even') 
axes[0].set_xlabel('6-Week heuristic cost/unit (£)') 
axes[0].set_ylabel('NB (s,S) cost/unit (£)') 
axes[0].set_title('NB (s,S) vs 6-Week Heuristic') 
axes[0].legend(fontsize=9) 
# NB vs Normal 
axes[1].scatter(results_df['normal_cost'], results_df['cost_per_unit'], 
                alpha=0.3, s=8, color='#C55A11') 
lim2 = max(results_df['normal_cost'].max(), results_df['cost_per_unit'].max()) 
axes[1].plot([0, lim2], [0, lim2], 'r--', linewidth=1.5, label='Break-even') 
axes[1].set_xlabel('Normal (s,S) cost/unit (£)') 
axes[1].set_ylabel('NB (s,S) cost/unit (£)') 
axes[1].set_title('NB (s,S) vs Normal (s,S)') 
axes[1].legend(fontsize=9) 
  
plt.tight_layout() 
st.pyplot(fig) 
plt.close() 
  
# ── What the Normal comparison isolates ────────────────────────── 
st.info( '**Interpretation:** Points below the red line are SKUs where the NB policy ' 'is cheaper. The left chart shows the value of the full model vs the heuristic. ' 'The right chart isolates the value of the NB distribution specifically — ' 'the only difference between NB (s,S) and Normal (s,S) is the distribution assumption.' ) 
  
# ── Wins and losses breakdown ──────────────────────────────────── 
st.subheader('Wins and Losses vs Heuristic (Q4 Holdout)') 
beats = results_df['beats_heuristic'].value_counts() 
  
fig, ax = plt.subplots(figsize=(6, 4)) 
labels  = ['NB cheaper', 'Heuristic cheaper'] 
sizes   = [beats.get(True, 0), beats.get(False, 0)] 
colors  = ['#2E75B6', '#CCCCCC'] 
ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
       startangle=90, textprops={'fontsize': 11}) 
ax.set_title('Q4 Holdout: NB (s,S) vs 6-Week Heuristic') 
st.pyplot(fig) 
plt.close() 