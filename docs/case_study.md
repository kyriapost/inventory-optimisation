# Case Study: Inventory Optimisation for SME Retail 
  
## The Problem 
  
Small and medium-sized retailers typically set reorder points using 
a fixed weeks-of-supply rule: 'order when we have less than 6 weeks 
of stock left, and order enough for 6 more weeks.' This rule is 
simple but ignores demand variability. A product that sells 50 units 
per week on average but ranges from 10 to 200 units needs a very 
different safety stock than one that consistently sells 48–52. 
  
The fixed rule systematically overstocks stable products and understocks 
variable ones — at the same time. 
  
  --- 
  
## The Dataset 
  
This analysis uses the UCI Online Retail II dataset: - 1028 SKUs with at least 40 weeks of demand history - Dec 2010 – Dec 2011, UK-based online retailer - Weekly demand aggregated from transaction-level data - 9.1% zero-demand weeks after gap-filling 
  
  --- 
  
## The Finding That Changed the Model Choice 
  
Before fitting any inventory model, the demand data was analysed 
for statistical properties. The key finding: 
  
> **100% of SKUs showed variance/mean ratios above 1.3.** 
> The median V/M ratio was 37.99 — nearly 38 times higher than the 
> Poisson distribution assumes. 
  
This matters because the reorder point is calculated from the 
demand distribution. If the Poisson distribution assumes the variance 
equals the mean, but the actual variance is 38 times higher, the 
calculated safety stock would be roughly 6 times too low at the 
median SKU (sqrt(38) ≈ 6.2). 
  
The Negative Binomial distribution handles overdispersion correctly. 
It was fitted to every SKU individually using maximum likelihood 
estimation — not assumed. 
  
  ---
  
## Results 
  
The NB (s,S) policy was compared to the 6-week heuristic on 
Q4 data (the last 25% of each SKU's history, held out from fitting): 
  
| Policy | Mean cost per unit | Q4 service level | 
|--------|--------------------|-----------------| 
| NB (s,S) — this model | £0.2776 | 0.997 | 
| 6-week heuristic | £0.5552 | 0.992 | 
| Normal (s,S) | £0.2755 | 0.996 | 
  
**88% of SKUs** had lower inventory cost under the NB (s,S) policy 
than under the 6-week heuristic on held-out Q4 data. 
  
Mean cost saving vs heuristic: **42.3** 
  --- 
  
## What This Means in Practice 
  
For a retailer with £500,000 in annual inventory cost, a 42.3% 
cost reduction would save £211,500 per year. This saving 
comes from two sources: 
  
1. **Reduced overstock** on stable, predictable SKUs (Smooth/Erratic 
   in the Syntetos-Boylan classification) where the fixed rule sets 
   an unnecessarily high reorder point. 
  
2. **Better service levels** on volatile SKUs (Erratic/Lumpy) where 
   the fixed rule underestimates the safety stock needed to achieve 
   a target fill rate. 
  --- 
  
## Limitations 
  
This analysis is based on one year of data from one business. 
The model does not account for: 
  - Seasonal demand patterns (insufficient data for reliable estimation) - Variable lead times from suppliers - Demand autocorrelation (week-to-week dependency) - Zero-inflated demand (affects ~27% of SKUs — deferred to future work) 
  
These limitations are documented in [docs/methodology.md](methodology.md). 
The tool is intended as a decision-support aid, not an automated 
ordering system. 
  --- 
## Reproducibility 
  
All results in this document are reproducible from the repository: 
  
```bash 
git clone https://github.com/[USERNAME]/inventory-optimisation.git 
# Follow Quick Start in README.md 
# Results are written to policy_results table by run_batch_pipeline.py 
# Validation notebook: notebooks/01_Validation.ipynb 
``` 