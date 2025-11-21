# Import Libraries
import dash
# --- FIX: Use modern Dash imports for HTML and DCC components ---
from dash import html, dcc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import numpy as np

# --- 1. Load and Prepare Data ---

# Load the two CSV files from the same directory where this script is executed.
df = pd.DataFrame()
df_orders = None
df_products = None

# Delimiter precedence: Comma -> Semicolon -> Tab
DELIMITERS = [',', ';', '\t']
successful_sep = None

for sep in DELIMITERS:
    try:
        # We rely on the observation that the comma delimiter is correct
        df_orders = pd.read_csv('Order_Details.csv', sep=sep)
        df_products = pd.read_csv('Product_Details.csv', sep=sep)
        
        # Validation: Check if the key column ('Product ID') was loaded correctly
        if 'Product ID' in df_orders.columns and 'Product ID' in df_products.columns and len(df_orders.columns) > 1 and len(df_products.columns) > 1:
            print(f"Data successfully loaded using '{sep}' delimiter.")
            successful_sep = sep
            break # Exit the loop if loading and basic validation succeed
        else:
            # If loaded but only one column exists (failed separation), continue to the next delimiter
            df_orders = None
            df_products = None
            continue
    except FileNotFoundError:
        print(f"Error: One or both files not found.")
        break # No need to try other delimiters if files aren't there
    except Exception as e:
        # Catching the previous MemoryError here is tricky, we rely on the successful delimiter check
        print(f"Initial data load failed with separator '{sep}': {e}.")
        continue # Try the next delimiter

if df_orders is not None and df_products is not None:
    try:
        # --- FIX: Data Cleaning and Validation for Merge Key ---
        key_column = 'Product ID'
        
        # 1. Clean the key columns (remove whitespace and ensure string type)
        df_orders[key_column] = df_orders[key_column].astype(str).str.strip()
        df_products[key_column] = df_products[key_column].astype(str).str.strip()

        # 2. CRITICAL FIX: Ensure the product details table is unique on Product ID
        # This prevents the many-to-many merge (Cartesian Product) that causes the memory overflow.
        products_before_dedupe = df_products.shape[0]
        df_products = df_products.drop_duplicates(subset=[key_column], keep='first')
        products_after_dedupe = df_products.shape[0]

        if products_before_dedupe != products_after_dedupe:
            print(f"INFO: Removed {products_before_dedupe - products_after_dedupe} duplicate Product IDs from Product_Details.csv to ensure unique product mapping.")
            
        print(f"df_orders shape BEFORE merge: {df_orders.shape}")
        print(f"df_products shape BEFORE merge: {df_products.shape}")

        # 3. Merge the two DataFrames on 'Product ID'
        df = pd.merge(df_orders, df_products, on=key_column, how='left')

        print(f"df shape AFTER merge: {df.shape}")

        # --- Sanity Check for Data Explosion (Cartesian Product) ---
        # The merged shape should now be very close to the order file shape.
        if df.shape[0] > (df_orders.shape[0] * 1.5) and df.shape[0] > 1000:
             print("CRITICAL WARNING: The merged DataFrame size is still significantly larger than the orders file. The merge may still be causing issues.")
        
        # Check if required columns exist after merge
        if all(col in df.columns for col in ['Quantity (Units)', 'Net Price ($)', 'Tax Rate (%)']):
            # Calculate Total Sales (Net Price * Quantity) and Total Price (Net Price + Tax)
            df['Total Sales ($)'] = df['Net Price ($)'] * df['Quantity (Units)']
            df['Total Tax ($)'] = df['Total Sales ($)'] * (df['Tax Rate (%)'] / 100)
            df['Grand Total ($)'] = df['Total Sales ($)'] + df['Total Tax ($)']
        else:
            print("Warning: Missing key columns after merging. Check CSV integrity and 'Product ID' match.")
            df = pd.DataFrame() # Set df to empty if core columns are missing

    except Exception as e:
        # Catch any residual memory or merge errors
        print(f"Error during DataFrame merge or calculation: {e}")
        df = pd.DataFrame()
else:
    print("Dashboard cannot run: Failed to load data with any tested delimiter. Please check your CSV file separators.")


# --- 2. Create Dash App and Layout ---

# Initialize Dash App with an external stylesheet for better styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])
server = app.server # Required for deployment

# Get unique values for dropdowns (use empty lists if df is empty)
customer_locations = sorted(df['Customer Location'].unique()) if 'Customer Location' in df.columns else []
age_groups = sorted(df['Customer Age Group'].unique()) if 'Customer Age Group' in df.columns else []

app.layout = dbc.Container([
    # Header Row
    dbc.Row(dbc.Col(
        html.H1("Sales Performance Dashboard", className="text-center my-4 text-primary"),
        width=12
    )),

    # Control Row (Dropdowns)
    dbc.Row([
        # Location Dropdown
        dbc.Col([
            html.Label("Filter by Location:"),
            dcc.Dropdown(
                id='location-dropdown',
                options=[{'label': loc, 'value': loc} for loc in customer_locations],
                value=customer_locations, # Default to all selected
                multi=True,
                placeholder="Select Locations",
                className="mb-3"
            )
        ], md=6), # Takes half the width on medium screens

        # Age Group Dropdown
        dbc.Col([
            html.Label("Filter by Age Group:"),
            dcc.Dropdown(
                id='age-group-dropdown',
                options=[{'label': age, 'value': age} for age in age_groups],
                value=age_groups, # Default to all selected
                multi=True,
                placeholder="Select Age Groups",
                className="mb-3"
            )
        ], md=6),
    ], className="mb-4"),

    # KPI Row (Displaying summary metrics)
    dbc.Row([
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H4(id="kpi-total-sales", className="card-title text-success"),
                html.P("Total Sales Value", className="card-text"),
            ]),
        ), md=4),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H4(id="kpi-total-units", className="card-title text-info"),
                html.P("Total Units Sold", className="card-text"),
            ]),
        ), md=4),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H4(id="kpi-avg-price", className="card-title text-warning"),
                html.P("Average Net Price", className="card-text"),
            ]),
        ), md=4),
    ], className="mb-4"),

    # Graph Row
    dbc.Row([
        dbc.Col([
            html.H3("Sales by Product Category & Gender", className="text-center mb-3"),
            dcc.Graph(id='sales-by-category-gender-chart')
        ], width=12)
    ]),

], fluid=True) # Makes the container stretch to the full width

# --- 3. Define Callbacks for Interactivity ---

# Callback to update KPIs and Graph
@app.callback(
    [Output('kpi-total-sales', 'children'),
     Output('kpi-total-units', 'children'),
     Output('kpi-avg-price', 'children'),
     Output('sales-by-category-gender-chart', 'figure')],
    [Input('location-dropdown', 'value'),
     Input('age-group-dropdown', 'value')]
)
def update_dashboard(selected_locations, selected_age_groups):
    # Check if the DataFrame is empty (e.g., due to FileNotFoundError or failed merge)
    if df.empty:
        # Return error/zero indicators if data loading failed
        return "$N/A", "N/A", "$N/A", {
            'layout': {
                'title': 'Error: Data files not loaded or columns missing. Check CSV delimiters.',
                'xaxis': {'visible': False},
                'yaxis': {'visible': False}
            }
        }

    # Filter the DataFrame based on dropdown selections
    filtered_df = df[
        df['Customer Location'].isin(selected_locations) &
        df['Customer Age Group'].isin(selected_age_groups)
    ]

    # 1. Update KPIs
    total_sales = filtered_df['Total Sales ($)'].sum()
    total_units = filtered_df['Quantity (Units)'].sum()
    avg_price = filtered_df['Net Price ($)'].mean()

    kpi_sales = f"${total_sales:,.2f}"
    kpi_units = f"{int(total_units):,}"
    kpi_avg = f"${avg_price:,.2f}"

    # Handle case where filtered_df is empty (to avoid errors in formatting)
    if filtered_df.empty:
        kpi_sales = "$0.00"
        kpi_units = "0"
        kpi_avg = "$0.00"

    # 2. Create Figure (Grouped Bar Chart)
    if not filtered_df.empty:
        # Group by Category and Gender, then sum the total sales
        grouped_data = filtered_df.groupby(['Category', 'Customer Gender'])['Grand Total ($)'].sum().reset_index()

        fig = px.bar(
            grouped_data,
            x='Category',
            y='Grand Total ($)',
            color='Customer Gender',
            barmode='group',
            title='Total Grand Sales by Product Category and Customer Gender',
            labels={'Grand Total ($)': 'Total Revenue ($)', 'Category': 'Product Category'},
            height=500
        )
        # Apply visual styling
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_color='#333',
            margin=dict(l=20, r=20, t=60, b=20)
        )
    else:
        # Return an empty figure if no data is selected
        fig = {
            'layout': {
                'title': 'No Data Selected',
                'xaxis': {'visible': False},
                'yaxis': {'visible': False}
            }
        }

    return kpi_sales, kpi_units, kpi_avg, fig

# --- 4. Run the App ---
if __name__ == '__main__':
    if not df.empty:
        app.run(debug=True)
    else:
        print("Dashboard cannot be run because data loading failed.")