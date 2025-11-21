# Asimov Datathon 2025 Dashboard
> This is a Python interactive dashboard built with Dash, Plotly, and Dash Bootstrap Components. It visualizes sales data from CSV files and displays charts interactively.

Our Asimov Datathon 2025 Dashboard is not just a collection of charts—it represents a thoughtful, production-ready solution that excels in three key areas:

1. Advanced Interactivity & User Experience (UX)
We built our dashboard using Dash Bootstrap Components (DBC) and custom CSS, featuring a seamless, fully functional Light/Dark Mode toggle that maintains visual consistency across all charts and tables. This commitment to modern UX, combined with comprehensive filters (Date, Category, Price, etc.), ensures the data is not just displayed, but is immediately accessible and pleasant to analyze for all users.

2. Deep Analytical Power

The dashboard provides deep, multi-dimensional insights that go beyond simple time series:
- 3D Visualizations: We leverage advanced Plotly features, such as the 3D Scatter Plot (Customer Insights) and the 3D Heatmap (Product & Pricing), to simultaneously analyze up to three variables (e.g., Age, Price, and Quantity) allowing for the discovery of complex, non-obvious correlations.
- Categorical Handling: The script includes robust data cleaning and specialized handling for ordered categorical data (like Customer Age Group), ensuring charts are scientifically accurate and easily interpreted.

---

## Project Structure
```bash
├── .venv/ # Virtual environment (optional, not included in git)
├── Product_Details.csv # Product details CSV
├── Order_Details.csv # Order details CSV
├── asimov.py # Main dashboard script
├── requirements.txt # Python dependencies
├── README.md
```
## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/prxcode/datathon25
cd datathon25
```

### 2. Create Virtual Environment (Optional)
- Windows(Powershell): `python -m venv .venv`
- Windows (CMD): `.venv\Scripts\activate.bat`
- Linux/MacOS: `source .venv/bin/activate`
  
### 3. To download all required Python packages
- `pip install -r requirements.txt` 
- or install Manually `pip install dash dash-bootstrap-components pandas plotly requests scikit-learn requests`

### 4. Run the dashboard
`python asimov.py`


### Note 
- Even when the AI features are functional, you may experience significant delays (latency) in receiving a response from the AI assistant.
- This delay is not due to the Dash application itself but is a result of waiting for the external AI API service to process and return its complex request.
