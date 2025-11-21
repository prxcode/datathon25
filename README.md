# Asimov Datathon 2025 Dashboard
> This is a Python interactive dashboard built with Dash, Plotly, and Dash Bootstrap Components. It visualizes sales data from CSV files and displays charts interactively.

## Why We Think Our Dashboard Stands Out
We put a lot of time into making this dashboard practical and insightful. We have added three key features:

1. Focus on User Experience (UX) and Interaction
We wanted this to be a tool people would actually use, not just a one-off project.
- Comfort and Aesthetics: We built the layout with Dash Bootstrap Components (DBC) and made sure to include a working Light/Dark Mode toggle. This wasn't just for looks; it ensures the dashboard is comfortable to stare at for hours, and the color scheme remains consistent across all the charts and tables.
- Practical Filtering: We designed a robust filter panel with everything you need—Date ranges, Categories, Price limits, and more. This makes slicing the sales data straightforward and quick, allowing any user to find specific insights without needing to write code.

2. Serious Analytical Depth
We weren't satisfied with simple 2D charts. To pull out the tricky, hidden connections in the data, we needed a deeper approach.
- Multi-Dimensional Views: We integrated powerful, advanced Plotly visualizations to tackle complexity:
  - The 3D Scatter Plot helps us look at three variables at once (like how Customer Age, Price, and Purchase Quantity interact), which can reveal correlations you'd easily miss in a standard chart.
  - The 3D Heatmap gives a great overview of how different factors—like Location and Product Category—combine to affect the Average Net Price.
- Tidy Data Science: Behind the scenes, we included solid data cleaning and specialized handling for things like the Customer Age Group. By properly ordering these categories, we ensure the analysis is scientifically accurate, making the resulting charts much more reliable and easier to interpret.

3. AI Integration 
We think this balance of a great user interface with genuine analytical depth makes our solution uniquely effective.
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
