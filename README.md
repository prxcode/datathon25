# Asimov Datathon 2025 Dashboard

This is a Python interactive dashboard built with Dash, Plotly, and Dash Bootstrap Components. It visualizes sales data from CSV files and displays charts interactively.

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
git clone <your-repo-url>
cd asimov-datathon25
```

### 2. Create Virtual Environment (Optional)
- Windows(Powershell): `python -m venv .venv`
- Windows (CMD): `.venv\Scripts\activate.bat`
- Linux/MacOS: `source .venv/bin/activate`
  
### 3. To download all required Python packages
- `pip install -r requirements.txt` 
- or install Manually `pip install dash dash-bootstrap-components pandas plotly`

### 4. Run the dashboard
`python asimov.py`
