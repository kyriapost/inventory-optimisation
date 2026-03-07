## Section 1 - Problem Statement

Problem Statement
---
SME product retailers with 10–100 SKUs and E-commerce businesses typically set reorder points using a fixed weeks-of-supply rule rather than data — leading to simultaneous overstock in slow lines and stockouts in fast ones.

Approach
---
(s,S) — reorder when stock falls to s, order up to S.
To understand why it is so appropriate, we have to look at how the fixed ordering cost and the periodic review schedule interact with the two variables: $s$ (the reorder point) and $S$ (the order-up-to level).

Here is a breakdown of why this policy fits perfectly:
1. The Fixed Ordering Cost Requires a Threshold ($s$)A fixed ordering cost (often denoted as $K$) means you pay a set amount every time you place an order, regardless of whether you order 1 unit or 1,000 units. This could be a setup fee, delivery charge, or administrative cost.

    The Problem: If you didn't have a minimum threshold ($s$) and simply ordered inventory back up to your target level every single review period (a base-stock policy), you might end up placing orders for very small quantities. Paying a high fixed cost to ship two units is highly inefficient.
    
    The Solution: The reorder point ($s$) acts as a gatekeeper. It forces the system to wait until inventory has dropped low enough to justify paying the fixed ordering cost. By creating a gap between $s$ and $S$, you ensure that when an order is placed, it is large enough to absorb and amortize that fixed cost.
2. Periodic Review Requires Dynamic Order Quantities (up to $S$)In a continuous review system, you know the exact moment your inventory hits $s$, so you can order a fixed quantity ($Q$). However, in a periodic review system, you are "blind" between review periods.

    The Problem: When the review day finally arrives, your inventory won't be exactly at $s$. It will likely have dropped below $s$. How far below depends on the unpredictable demand that occurred since the last review. If you used a fixed order quantity ($Q$), an unexpected spike in demand could leave you with too little inventory to survive until the next review period.

    The Solution: Ordering up to a maximum level ($S$) creates a dynamic order size. If demand was moderate and your inventory is just slightly below $s$, you order a moderate amount. If demand spiked and your inventory is drastically below $s$, you order a much larger amount. Ordering up to $S$ ensures that, regardless of how far you dropped below the threshold, you always start the next cycle with the optimal amount of stock to cover the lead time and the upcoming review period.

**Summary of the Mechanics**

Under the periodic $(s, S)$ policy, at each review interval $T$:
1. You check the current inventory position ($I$).
2. If $I > s$, you do nothing (saving the fixed ordering cost).
3. If $I \le s$, you place an order for the quantity $S - I$ (paying the fixed cost, but buying enough to make it mathematically worthwhile and safe).

Ultimately, the $(s, S)$ policy elegantly balances the risk of stocking out during "blind" periodic intervals against the financial pain of triggering fixed ordering costs too often.

## Section 2 - Data

Dataset
---
**UCI online retail**

https://archive.ics.uci.edu/dataset/352/online+retail

This is a transactional data set which contains all the transactions occurring between 01/12/2010 and 09/12/2011 for a UK-based and registered non-store online retail.The company mainly sells unique all-occasion gifts. Many customers of the company are wholesalers.

**Variable Information**
- InvoiceNo: Invoice number. Nominal, a 6-digit integral number uniquely assigned to each transaction. If this code starts with letter 'c', it indicates a cancellation. 
- StockCode: Product (item) code. Nominal, a 5-digit integral number uniquely assigned to each distinct product.
Description: Product (item) name. Nominal.
- Quantity: The quantities of each product (item) per transaction. Numeric.	
- InvoiceDate: Invoice Date and time. Numeric, the day and time when each transaction was generated.
- UnitPrice: Unit price. Numeric, Product price per unit in sterling.
- CustomerID: Customer number. Nominal, a 5-digit integral number uniquely assigned to each customer.
- Country: Country name. Nominal, the name of the country where each customer resides. 

Known limitation: dataset represents a wholesaler's sales, not an SME retailer's inventory. Demand patterns may differ from the target user context. Used as a proxy for real SKU-level demand data.

Source — UCI Online Retail dataset. Cite it properly: Chen, D. (2019). Online Retail II. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D 

Preprocessing — steps applied in ingest_uci_data.py: 
- Filter to UK transactions only 
- Exclude returns (Quantity < 0) and non-product codes 
- Aggregate to weekly demand per StockCode (Monday week start) 
- Retain only SKUs with >= 40 weeks of history 
- Fill zero-demand weeks within each SKU's active period 

**Data quality — reference EDA findings:** 
- No missing values after preprocessing 
- 9.1% zero-demand weeks (intermittency characterisation) 
- Outlier investigation: wholesale spike patterns retained 

## Section 3 - Demand Distrubution

### 3.1 Why distribution choice matters

The reorder point is fundamentally a quantile of the lead-time demand distribution. If we assume lead-time demand $X$ follows a cumulative distribution function $F(x)$, the reorder point $s$ for a target cycle service level $\alpha$ is calculated as the inverse:

$$s = F^{-1}(\alpha)$$

An incorrect distribution assumption means that the shape of $F(x)$ does not match the actual demand reality. This produces incorrect quantiles, which directly calculates an incorrect safety stock requirement. Ultimately, this results in failing to meet the target service levels—either through costly overstocking or damaging stockouts. This is not a minor modelling detail; it is the mathematical foundation of every number the inventory model produces.

### 3.2 The Negative Binomial distribution

To accommodate the varying volatility of lead-time demand, we utilize the Negative Binomial (NB) distribution. 

The Probability Mass Function (PMF) is given by:

$$P(X=k) = \binom{k+r-1}{k} p^r (1-p)^k$$

For implementation, we use the parameterization found in `scipy.stats.nbinom`, which defines the parameters as $(n, p)$, where $n$ takes the place of $r$ as the number of successes, and $p$ is the probability of success. Under this parameterization, the theoretical mean ($\mu$) and variance ($\sigma^2$) are:

$$\mu = \frac{n(1-p)}{p}$$

$$\sigma^2 = \frac{n(1-p)}{p^2}$$

**Derivation of the Variance/Mean Ratio:**
To understand the dispersion of this distribution, we derive the variance-to-mean ratio ($V/M$):

$$\frac{V}{M} = \frac{\sigma^2}{\mu} = \frac{\frac{n(1-p)}{p^2}}{\frac{n(1-p)}{p}}$$

$$\frac{V}{M} = \frac{n(1-p)}{p^2} \cdot \frac{p}{n(1-p)}$$

$$\frac{V}{M} = \frac{1}{p}$$

Because $p$ represents a probability strictly bounded between 0 and 1 ($0 < p < 1$), the ratio $1/p$ must be strictly greater than 1. 

### 3.3 Empirical justification

Analyzing the actual SKU data strongly supports the rejection of a Poisson distribution in favor of the Negative Binomial distribution. 

* **V/M Analysis:** 100% of the SKUs in the dataset exhibit a variance-to-mean ratio greater than 1.3. The median ratio is 37.99, with a range spanning from 1.91 to 1996.
* **Consequence of the Poisson assumption:** If we mistakenly assumed a Poisson distribution, the model would force the variance to equal the mean. This directly underestimates the true variance by a factor equal to the actual $V/M$ ratio.
* **Impact on Safety Stock:** Safety stock scales proportionally with the standard deviation (the square root of the variance). For the median SKU with $V/M = 37.99$, a Poisson assumption would underestimate the required safety stock by a factor of $\sqrt{37.99}$, which is approximately 6x. This would lead to severe, systematic stockouts.

---

### 3.4 Parameter estimation

To fit the Negative Binomial distribution to our empirical data, we use Maximum Likelihood Estimation (MLE) optimized via the Nelder-Mead algorithm using `scipy.optimize.minimize`.

Because MLE requires initial guesses to converge reliably, we derive our starting values ($n_0$ and $p_0$) using the Method of Moments. We set the theoretical mean and variance equal to the sample mean ($\mu$) and sample variance ($\sigma^2$):

1.  Solve for $p$:
    $$\sigma^2 = \frac{\mu}{p} \implies p_0 = \frac{\mu}{\sigma^2}$$

2.  Solve for $n$:
    $$\mu = \frac{n(1-p)}{p} \implies n = \frac{\mu p}{1-p}$$
    Substitute $p = \mu/\sigma^2$:
    $$n_0 = \frac{\mu \left(\frac{\mu}{\sigma^2}\right)}{1 - \frac{\mu}{\sigma^2}} = \frac{\frac{\mu^2}{\sigma^2}}{\frac{\sigma^2 - \mu}{\sigma^2}} = \frac{\mu^2}{\sigma^2 - \mu}$$

During the computational process, the optimization's success status is stored in the `NBParams.converged` flag. This acts as a strict quality filter to prevent poorly fitted parameters from propagating downstream into the safety stock calculations.

---

### 3.5 Goodness of fit

To validate the quality of the Negative Binomial fits, we apply the Kolmogorov-Smirnov (KS) test across the SKU base.

* **Performance:** The KS test yields a pass rate of 72.8%, successfully exceeding our minimum acceptable target of 72%. 
* **Root Causes of Failure:** For the 27.2% of SKUs that fail the KS test, the root causes generally split into two categories:
    1.  Extreme overdispersion where $V/M > 100$.
    2.  Zero-inflation (an excessive number of zero-demand periods that the standard NB distribution cannot sufficiently capture).



* **Limitation:** We must honestly note that while the standard Negative Binomial model handles standard overdispersion well, it structurally underperforms on highly intermittent demand. Implementing a Zero-Inflated Negative Binomial (ZINB) model is deferred to future work.

## Section 4 - Inventory Model

### 4.1 Economic Order Quantity

The Economic Order Quantity (EOQ) provides a deterministic baseline for balancing fixed ordering costs against inventory holding costs. 

The optimal order quantity $Q^*$ is calculated using the classic formula:

$$Q^* = \sqrt{\frac{2DK}{h}}$$

**Parameters:**
* **D:** Annual demand (units/year)
* **K:** Fixed order cost (£/order)
* **h:** Annual holding cost (£/unit/year), calculated as unit_price $\times$ holding_rate

**Proof of the Optimality Condition:**
The fundamental property of the EOQ model is that total variable costs are minimized exactly when annual ordering costs equal annual holding costs. 
Annual ordering cost is $\frac{D}{Q}K$, and annual holding cost is $\frac{Q}{2}h$. 
By substituting $Q^*$ into both cost functions, we can prove they are equal at optimality:

1.  **Holding Cost at $Q^*$:**
    $$\text{Holding} = \frac{\sqrt{\frac{2DK}{h}}}{2}h = \sqrt{\frac{2DKh^2}{4h}} = \sqrt{\frac{DKh}{2}}$$

2.  **Ordering Cost at $Q^*$:**
    $$\text{Ordering} = \frac{D}{\sqrt{\frac{2DK}{h}}}K = \sqrt{\frac{D^2 K^2 h}{2DK}} = \sqrt{\frac{DKh}{2}}$$

Because both equate to $\sqrt{DKh/2}$, ordering costs and holding costs are perfectly balanced at $Q^*$.



**Assumptions and Limitations:**
This derivation relies on strict, idealized assumptions: a constant and known demand rate, instantaneous replenishment (zero lead time), and no quantity discounts. While EOQ provides a useful theoretical foundation, these assumptions rarely hold in retail. The $(s, S)$ policy, detailed next, specifically relaxes the assumptions of constant demand and zero lead time.

---

### 4.2 The (s,S) Inventory Policy

To handle the reality of stochastic demand and periodic reviews, we transition from the deterministic EOQ to the probabilistic $(s, S)$ inventory policy. 

**Definitions:**
* **$s$ (Reorder Point):** The minimum inventory threshold. If the inventory position falls to or below this level, a replenishment order is triggered.
* **$S$ (Order-Up-To Level):** The target maximum inventory. When an order is triggered, the quantity ordered is exactly enough to bring the inventory position back up to $S$.

**Simulation Sequence (Review-then-Demand):**
In our simulation environment, the chronological sequence of events within each period is strictly structured as "review-then-demand":
1.  **Review:** At the start of the period, the system assesses the current inventory position. If it is $\le s$, an order is placed to bring it to $S$.
2.  **Demand:** Stochastic demand for the period occurs and is fulfilled from the available on-hand stock. 

**Cost Structure:**
The performance of the policy is evaluated using a Total Cost (TC) function:
$$\text{TC} = \text{Holding Costs} + \text{Ordering Costs} + \text{Stockout Costs}$$



**Why $(s,S)$ dominates $(s,Q)$ under stochastic demand:**
An alternative approach is the $(s, Q)$ policy, where a fixed quantity $Q$ is ordered whenever inventory drops below $s$. However, $(s, S)$ dominates $(s, Q)$ mathematically and practically under volatile demand. If a massive, unexpected demand spike drops the inventory position far below $s$, ordering a fixed $Q$ might not even be enough to bring the inventory back above the danger zone. Because the $(s, S)$ policy utilizes a variable order quantity ($S - \text{Current Inventory}$), it dynamically adapts to the actual inventory position, guaranteeing that the system always resets to the optimal target level regardless of how severe the prior demand shock was.

---

### 4.3 Reorder Point Derivation

The reorder point $s$ must cover the expected demand during the lead time plus a buffer for uncertainty. It is mathematically defined as the $\alpha$-quantile of the lead-time demand distribution:

$$s = F^{-1}_{D_L}(\alpha)$$

Where $F^{-1}_{D_L}$ is the inverse cumulative distribution function of the lead-time demand, and $\alpha$ is the target cycle service level.

**Lead-Time Demand Distribution:**
Given a weekly demand fitted to a Negative Binomial distribution $\text{NB}(n, p)$ and a constant lead time of $L$ weeks, the lead-time demand $D_L$ scales as:

$$D_L \sim \text{NB}(n \cdot L, p)$$

**The IID Scaling Assumption:**
This linear scaling ($n \cdot L$) relies heavily on the assumption that weekly demands are Independent and Identically Distributed (IID). It assumes that a high-demand week has no mathematical bearing on whether the following week will also have high demand. 

*Limitation:* We must explicitly state that this assumption ignores temporal autocorrelation (seasonality or trend momentum). If demands are positively correlated, variance scales faster than linear time, meaning our current aggregation method may underestimate the true lead-time variance.

**Safety Stock:**
Once $s$ is established, the Safety Stock (SS) is isolated by subtracting the Expected Lead-Time Demand ($E[D_L]$) from the reorder point:

$$SS = s - E[D_L] = s - \frac{n \cdot L \cdot (1-p)}{p}$$

## Section 5 - Optimisation and Evaluation

### 5.1 Optimisation approach

Our optimization routine uses a combination of analytical baselines and a local grid search to find the most cost-effective inventory parameters. 

**Analytical Starting Point:**
We calculate our initial parameters mathematically:
* The reorder point $s$ is derived from the Negative Binomial quantile function (as established in Section 4.3).
* The order-up-to level $S$ is calculated by adding the Economic Order Quantity to the reorder point: $S = s + Q^*$.



**Local Grid Search:**
Instead of blindly accepting the analytical result, we establish a search space around it:
* **$s$ range:** 3 steps above and below the analytical $s$.
* **$S$ range:** 3 steps above and below the analytical $S$.

The objective within this localized grid is to minimize the total cost per unit over the training demand history. 

**Why Grid Search is Appropriate:**
While more advanced optimization algorithms exist, a simple grid search is perfectly suited for this specific problem. The search space is exceptionally small (a $7 \times 7$ grid), meaning the computational overhead is negligible. It requires no gradient calculations, remains entirely transparent, and guarantees finding the exact local optimum within this constrained neighborhood.

---

### 5.2 Baselines

To prove the value of our Negative Binomial $(s, S)$ policy, we evaluate it against two baselines that represent different levels of operational sophistication.

**Baseline 1 — 6-Week Heuristic:**
This represents current standard practice for many SMEs. Parameters are set using a naive rule of thumb:
* $s = 6 \times \text{mean\_weekly\_demand}$
* $S = 12 \times \text{mean\_weekly\_demand}$

This baseline completely ignores demand variability, treating average demand as the sole driver of inventory decisions.

**Baseline 2 — Normal $(s, S)$:**
This baseline isolates and tests the specific contribution of our distribution choice. It uses the exact same EOQ-based $S$ parameter as our main model, but assumes lead-time demand is normally distributed:
* $s = \mu_{LT} + z \cdot \sigma_{LT}$

Where $z = \Phi^{-1}(\alpha)$ is the inverse cumulative distribution function of the standard normal distribution for the target service level $\alpha$. If our Negative Binomial model outperforms this baseline, we mathematically validate that the NB distribution handles demand overdispersion better than the standard normal assumption.

---

### 5.3 Q4 holdout evaluation

To rigorously test the model's performance, we utilize a 75/25 train/test split along the time dimension. 



The model policy is fitted entirely on the first 75% of the chronological data (the training set) and then evaluated strictly on the remaining 25% (Q4 data). This approach guarantees that we are testing true out-of-sample performance—which is the only metric that matters for a predictive operational model.

**Why Random Splits are Wrong for Time Series:**
It is critical to explain that standard random sampling (e.g., shuffling all weeks and picking 25% at random) is fundamentally incorrect for time series data. Random splits introduce severe data leakage; they allow the model to "peek" into the future during training, destroying the integrity of the test and producing artificially inflated performance metrics that will collapse when deployed in real time.

### 6.1 Results summary

Based on the evaluation metrics defined in the project scope, the implemented model achieved the following performance on the test dataset:

* **M1:** Negative Binomial (NB) Kolmogorov-Smirnov (KS) pass rate: **72.4%**
* **M2:** Outperforms the 6-week heuristic on Q4 data for **88%** of SKUs
* **M3:** Mean Q4 cycle service level achieved: **0.997**
* **M4:** Computational speed: Processed 50 SKUs in **1.5s**

**Headline:** The Negative Binomial (s, S) policy reduces total inventory costs by **[X]%** versus the naive 6-week heuristic when evaluated on the held-out Q4 data.

---

### 6.2 Known limitations

**Single year of data (no validated seasonality)**
The current model is trained and evaluated on a single year of historical demand data. This strictly limits our ability to identify, mathematically validate, or incorporate annual seasonality patterns into the inventory parameters, potentially leading to misaligned stock levels during peak seasonal shifts.

**Deterministic lead time**
The implementation assumes a fixed, deterministic lead time for all replenishments. Real-world supply chains frequently experience delivery delays and variability. Accommodating stochastic lead times to buffer against supplier unreliability is a necessary enhancement deferred to the `FUTURE.md` roadmap.

**IID demand assumption (ignores autocorrelation)**
Scaling weekly demand variance to lead-time variance relies heavily on the assumption that weekly demands are Independent and Identically Distributed (IID). This ignores temporal autocorrelation. If consecutive weeks exhibit positively correlated demand (momentum or trend), the current scaling mechanism will systematically underestimate the true lead-time variance.

**ZINB not implemented**
While the standard Negative Binomial distribution captures typical overdispersion, it structurally underperforms on highly intermittent demand. Approximately 27% of the SKUs in the dataset exhibit severe zero-inflation (excessive periods of zero demand). Implementing a Zero-Inflated Negative Binomial (ZINB) model is required to properly handle this subset of inventory.

**Cost parameters assumed**
The financial inputs used to calculate the Economic Order Quantity and evaluate the total policy costs—specifically the holding cost rate and the fixed ordering cost—are assumed standard values. Because these were not empirically measured from the business's actual accounting ledger, the absolute cost savings are illustrative rather than strictly financial.

**Single business dataset**
All empirical justifications, variance-to-mean analyses, and performance metrics are derived exclusively from a single UK-based online retail dataset. Consequently, the external validity of these specific findings across different industries, geographies, or retail structures remains unproven.

---

### 6.3 References

* Silver, E. A., Pyke, D. F., & Thomas, D. J. (2017). *Inventory and Production Management in Supply Chains* (4th ed.). CRC Press.
* Syntetos, A. A., & Boylan, J. E. (2005). The accuracy of intermittent demand estimates. *International Journal of Forecasting*, 21(2), 303–314.
* Chen, D. (2019). *Online Retail II Data Set*. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D