import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import requests
import json

# --- Data Loading and Cleaning ---
ORDER_PATH = "Order_Details.csv"
PRODUCT_PATH = "Product_Details.csv"

# Load data
try:
    order_data = pd.read_csv(ORDER_PATH)
    product_data = pd.read_csv(PRODUCT_PATH)
except FileNotFoundError:
    # Fallback dummy data
    print("CSV files not found. Using dummy data structure.")
    order_data = pd.DataFrame(columns=['Order ID', 'Date', 'Customer Name', 'Product ID', 'Quantity (Units)', 'Net Price ($)', 'Shipping Fee ($)', 'Customer Location', 'Customer Age Group', 'Customer Gender', 'Seasonality'])
    product_data = pd.DataFrame(columns=['Product ID', 'Category', 'Product Name'])

order_data.columns = order_data.columns.str.strip()
product_data.columns = product_data.columns.str.strip()

# --- Critical Fix: Force Numeric Conversion for Price Filter ---
def to_numeric_safe(series):
    # Removes '$' and ',' then converts to numeric, coercing errors to NaN
    return pd.to_numeric(series.astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')

if 'Net Price ($)' in order_data.columns:
    order_data['Net Price ($)'] = to_numeric_safe(order_data['Net Price ($)'])
if 'Quantity (Units)' in order_data.columns:
    order_data['Quantity (Units)'] = to_numeric_safe(order_data['Quantity (Units)'])
if 'Shipping Fee ($)' in order_data.columns:
    order_data['Shipping Fee ($)'] = to_numeric_safe(order_data['Shipping Fee ($)'])

def clean_df(df, subset):
    obj_cols = df.select_dtypes(include=['object']).columns
    for col in obj_cols:
        df[col] = df[col].astype(str).str.strip()
    if not df.empty:
        # Dropping duplicates and NaNs based on subset keys
        df = df.drop_duplicates(subset=subset)
        df = df.dropna(subset=subset)
    return df

order_data = clean_df(order_data, ['Product ID'])
product_data = clean_df(product_data, ['Product ID'])
merge_cols = [col for col in ['Product ID', 'Category'] if col in product_data.columns]

if not order_data.empty and not product_data.empty:
    df = pd.merge(order_data, product_data[merge_cols], on='Product ID', how='left')
else:
    df = order_data.copy()
    df['Category'] = 'Unknown'

AGE_ORDER = ['18-24', '25-34', '35-44', '45-54', '55+']
if 'Customer Age Group' in df.columns:
    # Ensure consistency in categorical data
    extended_order = AGE_ORDER + [x for x in df['Customer Age Group'].unique() if x not in AGE_ORDER and pd.notna(x)]
    df['Customer Age Group'] = pd.Categorical(df['Customer Age Group'], ordered=True, categories=extended_order)

# Convert Date column for filtering
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])

# Options for Dropdowns
category_opts = [{'label': x, 'value': x} for x in sorted(df['Category'].dropna().unique())]
location_opts = [{'label': x, 'value': x} for x in sorted(df['Customer Location'].dropna().unique())]
# Use safe conversion for category access
age_opts = [{'label': x, 'value': x} for x in AGE_ORDER if 'Customer Age Group' in df.columns and x in df['Customer Age Group'].cat.categories.astype(str)]
season_opts = [{'label': x, 'value': x} for x in df['Seasonality'].dropna().unique()]

# Price range limits (Ensure float is used for calculations)
price_min_limit = df['Net Price ($)'].min() if 'Net Price ($)' in df.columns and not df.empty and not df['Net Price ($)'].empty and df['Net Price ($)'].min() is not None else 0
price_max_limit = df['Net Price ($)'].max() if 'Net Price ($)' in df.columns and not df.empty and not df['Net Price ($)'].empty and df['Net Price ($)'].max() is not None else 1000

# Date Range Limits
min_date = df['Date'].min()
max_date = df['Date'].max()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# Helper functions for formatting/cleaning
def clean_and_convert(text_value, fallback_value):
    """Removes commas and converts the price string to a float."""
    if text_value is None or text_value == '':
        return fallback_value
    try:
        # Remove commas, spaces, and currency symbols
        clean_value = str(text_value).replace(',', '').replace('$', '').strip()
        if not clean_value or clean_value in ['.', '-']:
            return fallback_value
        return float(clean_value)
    except ValueError:
        return fallback_value

def format_number(numeric_value):
    """Formats a numeric value with commas for display."""
    if numeric_value is None:
        return ""
    # Format the number with commas (no decimal places for cleaner integer input)
    return f'{numeric_value:,.0f}'

# --- CSS Content (Injected via Markdown to avoid html.Style attribute error) ---
css_content = '''
    <style>
    /* Dark Mode Overrides */
    
    /* Dropdowns & Selects */
    .dark-theme .Select-control, .dark-theme .Select-menu-outer, .dark-theme .Select-option {
        background-color: #2d2d2d !important;
        color: #e0e0e0 !important;
        border-color: #555 !important;
    }
    .dark-theme .Select-value-label { color: #e0e0e0 !important; }
    .dark-theme .Select-placeholder { color: #a0a0a0 !important; }
    .dark-theme .Select-option:hover { background-color: #444 !important; }
    .dark-theme .Select--multi .Select-value {
        background-color: #444 !important;
        border: 1px solid #555 !important;
        color: #fff !important;
    }
    .dark-theme .Select--multi .Select-value-label { color: #fff !important; }

    /* Date Picker */
    .dark-theme .DateInput_input {
        background-color: #2d2d2d !important;
        color: #e0e0e0 !important;
        border-bottom: 2px solid #555 !important;
    }
    .dark-theme .DateRangePickerInput, .dark-theme .DateInput {
        background-color: transparent !important;
    }
    .dark-theme .CalendarMonth_table, .dark-theme .CalendarMonth {
        background-color: #2d2d2d !important;
    }
    .dark-theme .DayPicker_weekHeader { color: #e0e0e0 !important; }
    .dark-theme .CalendarDay__default {
        background-color: #2d2d2d !important;
        color: #e0e0e0 !important;
        border: 1px solid #444 !important;
    }
    .dark-theme .CalendarDay__selected {
        background-color: #17a2b8 !important; /* Minty secondary color */
        color: #fff !important;
    }
    
    /* Numeric/Text Inputs (Price Filters) */
    .dark-theme input.form-control {
        background-color: #2d2d2d !important;
        color: #e0e0e0 !important;
        border: 1px solid #555 !important;
    }
    .dark-theme input.form-control::placeholder { color: #888 !important; }

    /* --- FIXED: Bootstrap Tabs (dbc.Tabs) in Dark Mode --- */
    /* Target the standard Bootstrap nav structure */
    .dark-theme .nav-tabs { border-bottom: 1px solid #444 !important; }
    .dark-theme .nav-link { color: #aaa !important; } /* Inactive Text Color */
    .dark-theme .nav-link:hover {
        color: #e0e0e0 !important;
        background-color: #3a3a3a !important;
        border-color: #444 !important;
    }
    .dark-theme .nav-link.active { 
        color: #fff !important; /* Active Text Color */
        background-color: #2d2d2d !important; /* Matches Card BG */
        border-color: #444 #444 #2d2d2d !important; /* Makes the bottom border disappear against the background */
    }
    </style>
'''

app.layout = html.Div([
    # Inject CSS using Markdown to bypass missing html.Style attribute
    dcc.Markdown(css_content, dangerously_allow_html=True, style={'display': 'none'}),
    
    # Stores for state management
    dcc.Store(id='theme-store', data='light'),
    dcc.Store(id='price-min-numeric-store', data=price_min_limit), # Store clean numeric value
    dcc.Store(id='price-max-numeric-store', data=price_max_limit), # Store clean numeric value
    dbc.Card([
    dbc.CardHeader("Ask the AI Chatbot", className="fw-bold"),
    dbc.CardBody([
        dcc.Markdown("💬 You can ask any question about the filtered dashboard data here.", className="mb-3"),
        dcc.Input(id="chatbot-input", type="text", placeholder="Type your question...", style={"width": "70%"}),
        dbc.Button("Send", id="chatbot-send", n_clicks=0, color="primary", className="ms-2"),
        html.Div(id="chatbot-output", style={'padding': '10px', 'marginTop':'15px'})
    ])
], className="mt-4"),

    dbc.Container([
        # Header with Theme Toggle
        dbc.Row([
            dbc.Col([
                html.H2("E-Commerce Analytics Dashboard For Datathon 2025 (IEEE X LUG)", id="header-title", className="mt-4 mb-4 fw-bold")
            ], width=10),
            dbc.Col([
                dbc.Button(
                    "🌙 Dark Mode",
                    id="theme-toggle",
                    color="secondary",
                    className="mt-4",
                    size="sm"
                )
            ], width=2, className="text-end")
        ]),
        
        # Tabs
        dbc.Tabs(id="tabs", active_tab="tab-1", children=[
            dbc.Tab(label="Sales Overview", tab_id='tab-1'),
            dbc.Tab(label="Customer Insights", tab_id='tab-2'),
            dbc.Tab(label="Product & Pricing", tab_id='tab-3'),
        ], className="mb-3", style={'fontWeight':'bold', 'fontSize':'1.2rem'}),
        
        # Filters Container
        dbc.Card([
            dbc.CardBody([
                html.H5("Filters", className="mb-3", id="filter-header"),
                dbc.Row([
                    # Date Range Picker
                    dbc.Col([
                        html.Label("Date Range", className="fw-bold", id="lbl-date"),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            initial_visible_month=min_date,
                            start_date=min_date,
                            end_date=max_date,
                            display_format='YYYY-MM-DD',
                            style={'width': '100%'}
                        )
                    ], width=3),

                    dbc.Col([
                        html.Label("Category", className="fw-bold", id="lbl-cat"), 
                        dcc.Dropdown(id='filter-category', options=category_opts, multi=True, placeholder='All Categories')
                    ], width=3),

                    dbc.Col([
                        html.Label("Location", className="fw-bold", id="lbl-loc"), 
                        dcc.Dropdown(id='filter-location', options=location_opts, multi=True, placeholder='All Locations')
                    ], width=3),

                    dbc.Col([
                        html.Label("Seasonality", className="fw-bold", id="lbl-sea"), 
                        dcc.Dropdown(id='filter-season', options=season_opts, multi=True, placeholder='All Seasons')
                    ], width=3),
                ], className='mb-3'),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("Age Group", className="fw-bold", id="lbl-age"), 
                        dcc.Dropdown(id='filter-age', options=age_opts, multi=True, placeholder='All Ages')
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Price Range ($)", className="fw-bold", id="lbl-price"),
                        dbc.Row([
                            dbc.Col([
                                # Changed to type='text' to allow comma formatting
                                dbc.Input(
                                    id='filter-price-min',
                                    type='text',
                                    placeholder=f'Min: {format_number(price_min_limit)}',
                                    value=format_number(price_min_limit), # Initial formatted value
                                    size="sm"
                                )
                            ], width=6),
                            dbc.Col([
                                # Changed to type='text' to allow comma formatting
                                dbc.Input(
                                    id='filter-price-max',
                                    type='text',
                                    placeholder=f'Max: {format_number(price_max_limit)}',
                                    value=format_number(price_max_limit), # Initial formatted value
                                    size="sm"
                                )
                            ], width=6)
                        ])
                    ], width=4),
                ]),
            ])
        ], id="filter-card", className="mb-4 shadow-sm"),
        
        html.Div(id='tab-content')
    ], fluid=True, style={'padding': '20px'})
], id='main-wrapper', className='light-theme')


# --- Price Formatting Callbacks ---

@app.callback(
    [Output('price-min-numeric-store', 'data'),
     Output('price-max-numeric-store', 'data')],
    [Input('filter-price-min', 'value'),
     Input('filter-price-max', 'value')]
)
def update_numeric_price_store(min_text, max_text):
    """Takes the text input (which may include commas) and stores the clean numeric value."""
    # Use the original limits as fallbacks if parsing fails
    min_val = clean_and_convert(min_text, price_min_limit)
    max_val = clean_and_convert(max_text, price_max_limit)
    
    # Simple validation: ensure min is not greater than max (for filtering logic)
    # The display update callback below will re-format the valid numeric values.
    
    return min_val, max_val

@app.callback(
    [Output('filter-price-min', 'value'),
     Output('filter-price-max', 'value')],
    [Input('price-min-numeric-store', 'data'),
     Input('price-max-numeric-store', 'data')],
    # Prevent initial call because the values are already set correctly in the layout
    prevent_initial_call=True 
)
def format_price_display(min_num, max_num):
    """Formats the clean numeric store value back into the input fields with commas for display."""
    return format_number(min_num), format_number(max_num)


# --- Theme Toggle Callback (Unchanged) ---
@app.callback(
    [Output('theme-store', 'data'),
     Output('theme-toggle', 'children'),
     Output('main-wrapper', 'style'),
     Output('main-wrapper', 'className'),
     Output('header-title', 'style'),
     Output('filter-card', 'style'),
     Output('filter-header', 'style'),
     Output('lbl-date', 'style'),
     Output('lbl-cat', 'style'),
     Output('lbl-loc', 'style'),
     Output('lbl-sea', 'style'),
     Output('lbl-age', 'style'),
     Output('lbl-price', 'style')],
    Input('theme-toggle', 'n_clicks'),
    State('theme-store', 'data'),
    prevent_initial_call=False 
)
def toggle_theme(n_clicks, current_theme):
    if n_clicks and current_theme == 'light':
        theme = 'dark'
    else:
        theme = 'light' if not n_clicks else 'light' # Default to light unless toggled

    if theme == 'dark':
        # Dark Mode Styles
        bg_color = '#1e1e1e'
        text_color = '#e0e0e0' 
        header_color = '#bdbdbd'
        card_bg = '#2d2d2d'
        
        # Wrapper Style
        wrapper_style = {'backgroundColor': bg_color, 'color': text_color, 'minHeight': '100vh'}
        wrapper_class = 'dark-theme' # Activates CSS overrides
        
        header_style = {'color': header_color}
        card_style = {'backgroundColor': card_bg, 'border': '1px solid #404040'}
        label_style = {'color': header_color}
        
        return 'dark', '☀️ Light Mode', wrapper_style, wrapper_class, header_style, card_style, label_style, \
               label_style, label_style, label_style, label_style, label_style, label_style
    else:
        # Light Mode Styles
        bg_color = '#f8f9fa'
        text_color = '#000000'
        header_color = '#2c3e50'
        card_bg = '#ffffff'
        
        wrapper_style = {'backgroundColor': bg_color, 'color': text_color, 'minHeight': '100vh'}
        wrapper_class = 'light-theme'
        
        header_style = {'color': header_color}
        card_style = {'backgroundColor': card_bg, 'border': '1px solid #dee2e6'}
        label_style = {'color': '#495057'} 
        
        return 'light', '🌙 Dark Mode', wrapper_style, wrapper_class, header_style, card_style, label_style, \
               label_style, label_style, label_style, label_style, label_style, label_style

def filter_df(dff, category, location, start_date, end_date, age, season, price_min, price_max):
    # Filter by Date Range
    if start_date and end_date:
        dff = dff[(dff['Date'] >= start_date) & (dff['Date'] <= end_date)]
    
    if category: 
        dff = dff[dff['Category'].isin(category)]
    if location: 
        dff = dff[dff['Customer Location'].isin(location)]
    if age: 
        dff = dff[dff['Customer Age Group'].isin(age)]
    if season: 
        dff = dff[dff['Seasonality'].isin(season)]
    
    # Filter by Price Range (Numeric)
    # Price min/max are now guaranteed to be numeric floats from the dcc.Store
    if price_min is not None and price_max is not None:
        dff = dff[(dff['Net Price ($)'] >= price_min) & (dff['Net Price ($)'] <= price_max)]
        
    return dff

# --- Tab Content Callback (Updated to use Numeric Stores) ---
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab'),
    Input('filter-category', 'value'),
    Input('filter-location', 'value'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('filter-age', 'value'),
    Input('filter-season', 'value'),
    # Reading clean numeric values from the Store components
    Input('price-min-numeric-store', 'data'), 
    Input('price-max-numeric-store', 'data'),
    Input('theme-store', 'data')
)
def update_tabs(tab, category, location, start_date, end_date, age, season, price_min_numeric, price_max_numeric, theme):
    dff = df.copy()
    dff = filter_df(dff, category, location, start_date, end_date, age, season, price_min_numeric, price_max_numeric)
    
    # Set template based on theme
    template = 'plotly_dark' if theme == 'dark' else 'plotly_white'
    
    # Common check for empty data
    if dff.empty:
        return html.Div([
            html.H4("No data available for the selected filters.", className="text-center mt-5"),
            html.P("Try adjusting your date range or filters.", className="text-center")
        ])

    # --- PAGE 1: Sales Overview ---
    if tab == 'tab-1':
        bar1 = dff.groupby('Category')['Quantity (Units)'].sum().reset_index()
        fig1 = px.bar(bar1, x='Category', y='Quantity (Units)', color='Category', 
                      title='Total Quantity Sold by Category', template=template)
        
        bar2 = dff.groupby('Category')['Net Price ($)'].sum().reset_index()
        fig2 = px.bar(bar2, x='Category', y='Net Price ($)', color='Category', 
                      title='Total Revenue by Category', template=template)
        
        line = dff.groupby('Date')['Net Price ($)'].sum().reset_index()
        fig3 = px.line(line, x='Date', y='Net Price ($)', title='Total Revenue Over Time', template=template)
        
        ship = dff.groupby('Customer Location')['Shipping Fee ($)'].mean().reset_index()
        fig4 = px.bar(ship, x='Customer Location', y='Shipping Fee ($)', 
                      title='Average Shipping Fee by Location', template=template)
        
        return dbc.Container([
            dbc.Row([dbc.Col(dcc.Graph(figure=fig1), md=6), dbc.Col(dcc.Graph(figure=fig2), md=6)]),
            dbc.Row([dbc.Col(dcc.Graph(figure=fig3), md=12)], className="mt-4"),
            dbc.Row([dbc.Col(dcc.Graph(figure=fig4), md=12)], className="mt-4"),
        ], fluid=True)
    
    # --- PAGE 2: Customer Insights ---
    elif tab == 'tab-2':
        age_bar = dff.groupby('Customer Age Group', observed=True)['Quantity (Units)'].sum().reset_index()
        fig1 = px.bar(age_bar, x='Customer Age Group', y='Quantity (Units)', color='Customer Age Group', 
                      title='Age Group Distribution (Quantity)', category_orders={'Customer Age Group': AGE_ORDER}, 
                      template=template)
        
        gender_pie = dff['Customer Gender'].value_counts().reset_index()
        gender_pie.columns = ['Customer Gender', 'count']
        fig2 = px.pie(gender_pie, names='Customer Gender', values='count', 
                      title='Gender Distribution', template=template)
        
        cross = dff.groupby(['Customer Age Group','Category'], observed=True)['Quantity (Units)'].sum().reset_index()
        fig3 = px.bar(cross, x='Customer Age Group', y='Quantity (Units)', color='Category',
                      title='Quantity by Age Group and Category', barmode='group', 
                      category_orders={'Customer Age Group': AGE_ORDER}, template=template)
        
        scatter_df = dff.dropna(subset=['Customer Age Group','Net Price ($)','Quantity (Units)','Category'])
        fig4 = px.scatter_3d(
            scatter_df, x='Customer Age Group', y='Net Price ($)', z='Quantity (Units)',
            color='Category', opacity=0.6, size='Quantity (Units)', size_max=10,
            title='3D Scatter: Age Group, Net Price, Quantity', 
            category_orders={'Customer Age Group': AGE_ORDER}, template=template
        )
        
        return dbc.Container([
             dbc.Row([dbc.Col(dcc.Graph(figure=fig1), md=6), dbc.Col(dcc.Graph(figure=fig2), md=6)]),
             dbc.Row([dbc.Col(dcc.Graph(figure=fig3), md=12)], className="mt-4"),
             dbc.Row([dbc.Col(dcc.Graph(figure=fig4), md=12)], className="mt-4")
        ], fluid=True)
    
    # --- PAGE 3: Product & Pricing Analysis ---
    elif tab == 'tab-3':
        scatter_df = dff.dropna(subset=['Net Price ($)','Quantity (Units)','Category'])
        fig1 = px.scatter(scatter_df, x='Net Price ($)', y='Quantity (Units)', color='Category',
            title='Net Price vs Quantity Sold', size='Quantity (Units)', opacity=0.7, 
            template=template) if not scatter_df.empty else go.Figure()
        
        box_df = dff.dropna(subset=['Net Price ($)','Category'])
        fig2 = px.box(box_df, x='Category', y='Net Price ($)', color='Category', 
                      title='Net Price Distribution by Category', template=template) if not box_df.empty else go.Figure()

        top_n_products = dff.groupby('Product ID')['Net Price ($)'].sum().nlargest(50).index
        treemap_df = dff[dff['Product ID'].isin(top_n_products)]
        treemap_fig = px.treemap(
            treemap_df,
            path=['Category', 'Product ID'],
            values='Net Price ($)',
            hover_data=["Quantity (Units)","Net Price ($)"],
            title="Top 50 Products Treemap",
            template=template
        ) if not treemap_df.empty else go.Figure()

        surface_df = dff.groupby(['Customer Location','Category'])['Net Price ($)'].mean().reset_index()
        categories = sorted(surface_df['Category'].unique())
        locations = sorted(surface_df['Customer Location'].unique())
        z_values = []
        for loc in locations:
            row = []
            for cat in categories:
                avg = surface_df[(surface_df['Customer Location'] == loc) &
                                 (surface_df['Category'] == cat)]['Net Price ($)']
                row.append(avg.values[0] if not avg.empty and pd.notna(avg.values[0]) else None)
            z_values.append(row)
        
        fig_heatmap = go.Figure(data=[go.Surface(
            z=z_values,
            x=categories,
            y=locations,
            colorscale='Viridis',
            colorbar_title="Avg Net Price ($)",
            opacity=0.85
        )]) if categories and locations and any(z_values) else go.Figure()
        
        fig_heatmap.update_layout(
            title='3D Heatmap: Location & Category Avg Net Price',
            scene=dict(
                xaxis_title='Category',
                yaxis_title='Location',
                zaxis_title='Avg Net Price ($)'
            ),
            margin=dict(l=20,r=20,b=40,t=40),
            template=template
        )

        table_df = treemap_df[['Product ID','Category','Net Price ($)','Quantity (Units)']].drop_duplicates()
        
        product_table = dash_table.DataTable(
            columns=[{'name': i, 'id': i} for i in table_df.columns],
            data=table_df.to_dict('records'),
            style_table={'overflowX':'auto'},
            style_cell={
                'fontSize':'14px',
                'padding':'8px',
                'backgroundColor': '#2d2d2d' if theme == 'dark' else '#ffffff',
                'color': '#ffffff' if theme == 'dark' else '#000000',
                'border': '1px solid #404040' if theme == 'dark' else '1px solid #dee2e6'
            },
            style_header={
                'backgroundColor': '#1e1e1e' if theme == 'dark' else '#f0f0f0',
                'fontWeight': 'bold',
                'color': '#ffffff' if theme == 'dark' else '#000000',
                'border': '1px solid #404040' if theme == 'dark' else '1px solid #dee2e6'
            },
            sort_action='native',
            page_size=10
        ) if not table_df.empty else html.P("No product data available with current filters.")

        return dbc.Container([
            dbc.Row([dbc.Col(dcc.Graph(figure=fig1), md=6), dbc.Col(dcc.Graph(figure=fig2), md=6)]),
            dbc.Row([dbc.Col(dcc.Graph(figure=treemap_fig), md=12)], className="mt-4"),
            dbc.Row([dbc.Col(dcc.Graph(figure=fig_heatmap), md=12)], className="mt-4"),
            html.H5("Product Table (Top 50)", className="mt-4 mb-3"),
            product_table
        ], fluid=True)
    else:
        return html.H4("Select a tab to begin.")
import requests
import json

OPENROUTER_API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "x-ai/grok-4.1-fast:free"

def generate_dashboard_summary(dff):
    # Create a short summary for the AI about filtered data
    if dff.empty:
        return "No data in current filter."
    result = []
    if 'Category' in dff.columns:
        top_cat = dff.groupby('Category')['Net Price ($)'].sum().sort_values(ascending=False)
        top_cat = top_cat.index[0] if not top_cat.empty else 'None'
        result.append(f"Top Category: {top_cat}")
    if 'Customer Location' in dff.columns:
        top_loc = dff.groupby('Customer Location')['Net Price ($)'].sum().sort_values(ascending=False)
        top_loc = top_loc.index[0] if not top_loc.empty else 'None'
        result.append(f"Top Location: {top_loc}")
    total_rev = dff['Net Price ($)'].sum() if 'Net Price ($)' in dff.columns else 0
    result.append(f"Total Revenue: ${total_rev:,.2f}")
    return "; ".join(result)

@app.callback(
    Output("chatbot-output", "children"),
    Input("chatbot-send", "n_clicks"),
    State("chatbot-input", "value"),
    State('filter-category', 'value'),
    State('filter-location', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
    State('filter-age', 'value'),
    State('filter-season', 'value'),
    State('price-min-numeric-store', 'data'), 
    State('price-max-numeric-store', 'data'),
    prevent_initial_call=True
)



def chatbot_ask(n_clicks, user_question, category, location, start_date, end_date, age, season, price_min, price_max):
    dff = filter_df(df, category, location, start_date, end_date, age, season, price_min, price_max)
    dashboard_context = generate_dashboard_summary(dff)
    prompt = f"Dashboard Context: {dashboard_context}\nUser question: {user_question}\nPlease reply in markdown."
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256
    }
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=20)
        result = response.json()
        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "No reply from AI.")
    except Exception as e:
        reply = f"Error: {str(e)}"
    return dcc.Markdown(reply)

if __name__ == '__main__':
    app.run(debug=True)