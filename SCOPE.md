# Dynamic Inventory Optimisation Dashboard #

Problem Statement
---
SME product retailers with 10–100 SKUs and E-commerce businesses typically set reorder points using a fixed weeks-of-supply rule rather than data — leading to simultaneous overstock in slow lines and stockouts in fast ones.

Target User
---
SME product retailers and E-commerce business owners. They just want a number. They want to reduce costs by refining their order strategy. They want to move on from pen and paper or simple excel spreadsheets with no insight to something that is simple and useful. They are comfortable using a spreadsheet and can export a sales report from their POS or accounting system, but have no programming knowledge and no statistical background.

Definition of Done
---
- User uploads csv with sku_id, week_start and demand
- Tool outputs reorder point and order quantity per SKU in a table
- Tested and CI passed
- Non-technical person uses app without explanation
- Public URL no login required

Out of Scope
---
- Multi-echelon inventory
- Stochastic lead times
- Multi-user authentication
- Database for type of businesses (for marketing purposes)
- API and ERP integrations
- Real-time data 
- Unlimited SKUs with little performance drop
- Information about suppliers and customer suggestions
- Data collection, POS system integration
- Seasonality adjustment in the demand model.

Success Metrics
---
- Technical
    - KS test statistic p-value > 0.05 for 80% of SKUs
    - Computed cost ≤ current 6-week heuristic on held-out test data.
    - 50 SKUs under 1 minute runtime
- Non Technical
    - README communicates the project value to a non-technical reader in under 2 minutes
    - Full math breakdown in methodology.pdf
    - Clean set up on fresh machine under 5 minutes
    - App returns results within 30 seconds of CSV upload.
- Baselines
    - Fixed weeks-of-supply heuristic
    - (s,S) with Normal demand distribution

Both baselines compared against the NB model on average cost per unit and achieved service level on held-out Q4 data.


Dataset
---
UCI online retail

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

Technology Stack
---
- Python 3.12
- Numpy/ SciPy
- Pandas
- Plotly
- Streamlit
- PostgreSQL via Docker
- pytest
- Github Actions

Time Estimate
---
- Data Cleaning and aggregation: 6 hours
- EDA: 10 hours
- Database setup: 5 hours
- Distribution fitting and reorder point: 10 hours
- EOQ and (s,S) optimisation: 10 hours
- Testing: 10 hours
- Streamlit app: 10 hours
- Deployment: 4 hours
- Documentation: 15 hours 

Future
---
See FUTURE.md for new features and extensions.