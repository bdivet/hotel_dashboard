import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
import zipfile
from datetime import datetime
from statsmodels.tsa.seasonal import seasonal_decompose
import numpy as np

st.set_page_config(
    page_title="Hotel Frequency Dashboard",
    page_icon="🏨",
    layout="wide"
)

def load_insee_data(url, region_name):
    """Load and process INSEE CSV data from ZIP archive"""
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Extract CSV from ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Look for CSV files in the ZIP
            csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]

            if not csv_files:
                st.error(f"No CSV files found in {region_name} data")
                return None

            # Read the main data file (usually valeurs_mensuelles.csv)
            data_file = [f for f in csv_files if 'valeurs' in f.lower() or 'donnees' in f.lower()]
            if not data_file:
                data_file = csv_files[0]  # Take first CSV if no specific data file found
            else:
                data_file = data_file[0]

            with zip_file.open(data_file) as csv_file:
                # Try different encodings and skip first 4 lines
                try:
                    df = pd.read_csv(csv_file, encoding='utf-8', sep=';', skiprows=4, header=None)
                except UnicodeDecodeError:
                    csv_file.seek(0)
                    df = pd.read_csv(csv_file, encoding='latin-1', sep=';', skiprows=4, header=None)

                # Set proper column names based on the format: date, value, status
                if len(df.columns) >= 3:
                    if "Hotels" in region_name:
                        df.columns = ['Date', 'Hotel_Count', 'Status'] + [f'Col_{i}' for i in range(3, len(df.columns))]
                        value_col = 'Hotel_Count'
                    else:
                        df.columns = ['Date', 'Occupancy_Rate', 'Status'] + [f'Col_{i}' for i in range(3, len(df.columns))]
                        value_col = 'Occupancy_Rate'

                    # Clean the data
                    # Remove quotes from value and convert to float
                    df[value_col] = df[value_col].astype(str).str.replace('"', '').str.replace(',', '.').astype(float)

                    # Clean the date column and convert to datetime
                    df['Date'] = df['Date'].astype(str).str.replace('"', '')
                    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m', errors='coerce')

                    # Clean status column
                    df['Status'] = df['Status'].astype(str).str.replace('"', '')

                    # Filter out rows with invalid dates or values
                    df = df.dropna(subset=['Date', value_col])

                    # Sort by date
                    df = df.sort_values('Date')

                # Add region identifier
                df['Region'] = region_name
                return df

    except Exception as e:
        st.error(f"Error loading data for {region_name}: {str(e)}")
        return None

@st.cache_data
def get_hotel_data():
    """Fetch and combine hotel frequency data"""
    current_year = datetime.now().year
    current_month = datetime.now().month

    marne_url = f"https://bdm.insee.fr/series/010598981/csv?lang=fr&ordre=antechronologique&transposition=donneescolonne&periodeDebut=1&anneeDebut=2011&periodeFin={current_month}&anneeFin={current_year}&revision=sansrevisions"
    france_url = f"https://bdm.insee.fr/series/010599344/csv?lang=fr&ordre=antechronologique&transposition=donneescolonne&periodeDebut=1&anneeDebut=2011&periodeFin={current_month}&anneeFin={current_year}&revision=sansrevisions"
    grand_est_hotels_url = f"https://bdm.insee.fr/series/010609578/csv?lang=fr&ordre=antechronologique&transposition=donneescolonne&periodeDebut=1&anneeDebut=2011&periodeFin={current_month}&anneeFin={current_year}&revision=sansrevisions"

    marne_data = load_insee_data(marne_url, "Marne")
    france_data = load_insee_data(france_url, "France")
    grand_est_hotels_data = load_insee_data(grand_est_hotels_url, "Grand Est Hotels")

    return marne_data, france_data, grand_est_hotels_data

def process_data(df):
    """Process and clean the data - data is already processed in load_insee_data"""
    if df is None or df.empty:
        return None

    # Data is already cleaned in load_insee_data function
    return df

def main():
    st.title("🏨 Hotel Frequency Dashboard")
    st.markdown("---")

    # Load data
    with st.spinner("Loading hotel frequency data..."):
        marne_data, france_data, grand_est_hotels_data = get_hotel_data()

    if marne_data is None and france_data is None and grand_est_hotels_data is None:
        st.error("Failed to load data from all sources. Please check the URLs and try again.")
        return

    # Process data
    if marne_data is not None:
        marne_processed = process_data(marne_data)
    else:
        marne_processed = None

    if france_data is not None:
        france_processed = process_data(france_data)
    else:
        france_processed = None

    if grand_est_hotels_data is not None:
        grand_est_hotels_processed = process_data(grand_est_hotels_data)
    else:
        grand_est_hotels_processed = None

    # Sidebar for controls
    st.sidebar.header("Dashboard Controls")

    # Data source selection
    available_sources = []
    if marne_processed is not None:
        available_sources.append("Marne")
    if france_processed is not None:
        available_sources.append("France")

    if not available_sources:
        st.error("No data available to display")
        return

    selected_regions = st.sidebar.multiselect(
        "Select Regions to Display",
        available_sources,
        default=available_sources
    )

    # Main content area - focus on visualizations
    # st.header("📈 Hotel Frequency Trends")

    # Individual region charts
    col1, col2 = st.columns(2)

    with col1:
        if "Marne" in selected_regions and marne_processed is not None:
            # st.subheader("📍 Marne")

            # Create visualization using the cleaned data
            if 'Date' in marne_processed.columns and 'Occupancy_Rate' in marne_processed.columns:
                avg_val = marne_processed['Occupancy_Rate'].mean()

                fig = px.line(marne_processed,
                             x='Date',
                             y='Occupancy_Rate',
                             title="Marne Hotel Occupancy Rate (%)",
                             color_discrete_sequence=['#1f77b4'])

                # Add horizontal average line
                fig.add_hline(y=avg_val, line_dash="dash", line_color="red",
                             annotation_text=f"Avg: {avg_val:.1f}%",
                             annotation_position="top right")

                # Get y-axis range for shared scaling
                if "France" in selected_regions and france_processed is not None:
                    france_avg = france_processed['Occupancy_Rate'].mean()
                    all_min = min(marne_processed['Occupancy_Rate'].min(), france_processed['Occupancy_Rate'].min())
                    all_max = max(marne_processed['Occupancy_Rate'].max(), france_processed['Occupancy_Rate'].max())
                    fig.update_layout(yaxis=dict(range=[all_min - 2, all_max + 2]))

                fig.update_layout(
                    height=350,
                    # xaxis_title="Date",
                    yaxis_title="Occupancy Rate (%)",
                    margin=dict(t=40, b=40, l=40, r=40)
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.error("Required columns (Date, Occupancy_Rate) not found in Marne data")

    with col2:
        if "France" in selected_regions and france_processed is not None:
            # st.subheader("🇫🇷 France")

            # Create visualization using the cleaned data
            if 'Date' in france_processed.columns and 'Occupancy_Rate' in france_processed.columns:
                avg_val = france_processed['Occupancy_Rate'].mean()

                fig = px.line(france_processed,
                             x='Date',
                             y='Occupancy_Rate',
                             title="France Hotel Occupancy Rate (%)",
                             color_discrete_sequence=['#ff7f0e'])

                # Add horizontal average line
                fig.add_hline(y=avg_val, line_dash="dash", line_color="red",
                             annotation_text=f"Avg: {avg_val:.1f}%",
                             annotation_position="top right")

                # Set shared y-axis range if both regions are selected
                if "Marne" in selected_regions and marne_processed is not None:
                    marne_avg = marne_processed['Occupancy_Rate'].mean()
                    all_min = min(marne_processed['Occupancy_Rate'].min(), france_processed['Occupancy_Rate'].min())
                    all_max = max(marne_processed['Occupancy_Rate'].max(), france_processed['Occupancy_Rate'].max())
                    fig.update_layout(yaxis=dict(range=[all_min - 2, all_max + 2]))

                fig.update_layout(
                    height=350,
                    # xaxis_title="Date",
                    yaxis_title="Occupancy Rate (%)",
                    margin=dict(t=40, b=40, l=40, r=40)
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.error("Required columns (Date, Occupancy_Rate) not found in France data")

    # Comparison section if both datasets are available
    if len(selected_regions) > 1 and marne_processed is not None and france_processed is not None:
        # st.header("📊 Direct Comparison")

        # Create comparison chart using cleaned data
        if ('Date' in marne_processed.columns and 'Occupancy_Rate' in marne_processed.columns and
            'Date' in france_processed.columns and 'Occupancy_Rate' in france_processed.columns):

            fig = go.Figure()

            # Add Marne data
            fig.add_trace(go.Scatter(
                x=marne_processed['Date'],
                y=marne_processed['Occupancy_Rate'],
                mode='lines+markers',
                name='Marne',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=4)
            ))

            # Add France data
            fig.add_trace(go.Scatter(
                x=france_processed['Date'],
                y=france_processed['Occupancy_Rate'],
                mode='lines+markers',
                name='France',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=4)
            ))

            fig.update_layout(
                title="Hotel Occupancy Rate Comparison: Marne vs France",
                # xaxis_title="Date",
                yaxis_title="Occupancy Rate (%)",
                height=400,
                margin=dict(t=60, b=40, l=40, r=40),
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            fig.update_layout(hovermode='x unified')

            st.plotly_chart(fig, width='stretch')

            # Add comparison metrics
            col1, col2, col3 = st.columns(3)

            marne_avg = marne_processed['Occupancy_Rate'].mean()
            france_avg = france_processed['Occupancy_Rate'].mean()
            ratio = (marne_avg / france_avg * 100) if france_avg != 0 else 0

            with col1:
                st.metric("Marne Average", f"{marne_avg:.1f}%")
            with col2:
                st.metric("France Average", f"{france_avg:.1f}%")
            # with col3:
            #     st.metric("Marne vs France", f"{ratio:.1f}%")

        else:
            st.error("Required data columns not found for comparison")

    # Grand Est Hotels Count
    if grand_est_hotels_processed is not None:
        # st.header("🏨 Number of Hotels in Grand Est Region")

        if 'Date' in grand_est_hotels_processed.columns and 'Hotel_Count' in grand_est_hotels_processed.columns:
            avg_count = grand_est_hotels_processed['Hotel_Count'].mean()

            fig = px.line(grand_est_hotels_processed,
                         x='Date',
                         y='Hotel_Count',
                         title="Grand Est - Number of Hotels Over Time",
                         color_discrete_sequence=['#2ca02c'])

            # Add horizontal average line
            fig.add_hline(y=avg_count, line_dash="dash", line_color="red",
                         annotation_text=f"Avg: {avg_count:.0f} hotels",
                         annotation_position="top right")

            fig.update_layout(
                height=350,
                # xaxis_title="Date",
                yaxis_title="Number of Hotels",
                margin=dict(t=40, b=40, l=40, r=40)
            )
            st.plotly_chart(fig, width='stretch')

            # Show trend information
            recent_count = grand_est_hotels_processed['Hotel_Count'].iloc[-1]
            initial_count = grand_est_hotels_processed['Hotel_Count'].iloc[0]
            trend = "📈 Increasing" if recent_count > initial_count else "📉 Decreasing" if recent_count < initial_count else "➡️ Stable"

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Hotels", f"{recent_count:.0f}")
            with col2:
                st.metric("Average", f"{avg_count:.0f}")
            with col3:
                st.metric("Initial Count", f"{initial_count:.0f}")
            with col4:
                st.metric("Trend", trend)

        else:
            st.error("Required columns (Date, Hotel_Count) not found in Grand Est hotels data")

    # Seasonal Decomposition Analysis
    # st.header("📈 Trend & Seasonal Analysis")

    tab1, tab2 = st.tabs(["Seasonal Decomposition", "Monthly Patterns"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            if "Marne" in selected_regions and marne_processed is not None and len(marne_processed) > 24:
                st.subheader("Marne - Seasonal Decomposition")
                try:
                    # Prepare data for seasonal decomposition
                    marne_ts = marne_processed.set_index('Date')['Occupancy_Rate'].dropna()
                    marne_ts = marne_ts.asfreq('MS')  # Monthly start frequency

                    # Fill missing values with interpolation
                    marne_ts = marne_ts.interpolate(method='linear')

                    # If still missing values at edges, fill with mean
                    marne_ts = marne_ts.fillna(marne_ts.mean())

                    if len(marne_ts) > 24:  # Need at least 2 years for seasonal decomposition
                        decomposition = seasonal_decompose(marne_ts, model='additive', period=12)

                        # Create subplots for decomposition
                        fig = go.Figure()

                        # Original data
                        fig.add_trace(go.Scatter(
                            x=marne_ts.index, y=marne_ts.values,
                            mode='lines', name='Original',
                            line=dict(color='#1f77b4')
                        ))

                        # Trend
                        fig.add_trace(go.Scatter(
                            x=decomposition.trend.index, y=decomposition.trend.values,
                            mode='lines', name='Trend',
                            line=dict(color='red', width=2)
                        ))

                        # Set shared y-axis range if France is also selected
                        if "France" in selected_regions and france_processed is not None:
                            all_min = min(marne_ts.min(), france_processed['Occupancy_Rate'].min())
                            all_max = max(marne_ts.max(), france_processed['Occupancy_Rate'].max())
                            fig.update_layout(yaxis=dict(range=[all_min - 2, all_max + 2]))

                        fig.update_layout(
                            title="Marne: Original Data & Trend",
                            height=320,
                            # xaxis_title="Date",
                            yaxis_title="Occupancy Rate (%)",
                            margin=dict(t=50, b=30, l=40, r=40)
                        )

                        st.plotly_chart(fig, width='stretch')

                        # Seasonal component - store for shared y-axis
                        marne_seasonal_min = decomposition.seasonal.min()
                        marne_seasonal_max = decomposition.seasonal.max()

                        fig_seasonal = px.line(
                            x=decomposition.seasonal.index,
                            y=decomposition.seasonal.values,
                            title="Marne - Seasonal Component"
                        )

                        # Set shared y-axis range for seasonal components if France is also selected
                        if "France" in selected_regions and france_processed is not None:
                            # Calculate combined range (will be updated when France chart is created)
                            try:
                                france_ts_temp = france_processed.set_index('Date')['Occupancy_Rate'].dropna()
                                france_ts_temp = france_ts_temp.asfreq('MS').interpolate(method='linear').fillna(france_ts_temp.mean())
                                if len(france_ts_temp) > 24:
                                    france_decomp_temp = seasonal_decompose(france_ts_temp, model='additive', period=12)
                                    france_seasonal_min = france_decomp_temp.seasonal.min()
                                    france_seasonal_max = france_decomp_temp.seasonal.max()
                                    combined_min = min(marne_seasonal_min, france_seasonal_min)
                                    combined_max = max(marne_seasonal_max, france_seasonal_max)
                                    fig_seasonal.update_layout(yaxis=dict(range=[combined_min - 0.5, combined_max + 0.5]))
                            except:
                                pass

                        fig_seasonal.update_layout(
                            height=250,
                            margin=dict(t=40, b=30, l=40, r=40)
                        )
                        st.plotly_chart(fig_seasonal, width='stretch')

                except Exception as e:
                    st.info(f"Seasonal decomposition not available for Marne: {str(e)}")

        with col2:
            if "France" in selected_regions and france_processed is not None and len(france_processed) > 24:
                st.subheader("France - Seasonal Decomposition")
                try:
                    # Prepare data for seasonal decomposition
                    france_ts = france_processed.set_index('Date')['Occupancy_Rate'].dropna()
                    france_ts = france_ts.asfreq('MS')  # Monthly start frequency

                    # Fill missing values with interpolation
                    france_ts = france_ts.interpolate(method='linear')

                    # If still missing values at edges, fill with mean
                    france_ts = france_ts.fillna(france_ts.mean())

                    if len(france_ts) > 24:  # Need at least 2 years for seasonal decomposition
                        decomposition = seasonal_decompose(france_ts, model='additive', period=12)

                        # Create subplots for decomposition
                        fig = go.Figure()

                        # Original data
                        fig.add_trace(go.Scatter(
                            x=france_ts.index, y=france_ts.values,
                            mode='lines', name='Original',
                            line=dict(color='#ff7f0e')
                        ))

                        # Trend
                        fig.add_trace(go.Scatter(
                            x=decomposition.trend.index, y=decomposition.trend.values,
                            mode='lines', name='Trend',
                            line=dict(color='red', width=2)
                        ))

                        # Set shared y-axis range if Marne is also selected
                        if "Marne" in selected_regions and marne_processed is not None:
                            all_min = min(france_ts.min(), marne_processed['Occupancy_Rate'].min())
                            all_max = max(france_ts.max(), marne_processed['Occupancy_Rate'].max())
                            fig.update_layout(yaxis=dict(range=[all_min - 2, all_max + 2]))

                        fig.update_layout(
                            title="France: Original Data & Trend",
                            height=320,
                            # xaxis_title="Date",
                            yaxis_title="Occupancy Rate (%)",
                            margin=dict(t=50, b=30, l=40, r=40)
                        )

                        st.plotly_chart(fig, width='stretch')

                        # Seasonal component
                        fig_seasonal = px.line(
                            x=decomposition.seasonal.index,
                            y=decomposition.seasonal.values,
                            title="France - Seasonal Component"
                        )

                        # Set shared y-axis range for seasonal components if Marne is also selected
                        if "Marne" in selected_regions and marne_processed is not None:
                            try:
                                marne_ts_temp = marne_processed.set_index('Date')['Occupancy_Rate'].dropna()
                                marne_ts_temp = marne_ts_temp.asfreq('MS').interpolate(method='linear').fillna(marne_ts_temp.mean())
                                if len(marne_ts_temp) > 24:
                                    marne_decomp_temp = seasonal_decompose(marne_ts_temp, model='additive', period=12)
                                    marne_seasonal_min = marne_decomp_temp.seasonal.min()
                                    marne_seasonal_max = marne_decomp_temp.seasonal.max()
                                    france_seasonal_min = decomposition.seasonal.min()
                                    france_seasonal_max = decomposition.seasonal.max()
                                    combined_min = min(marne_seasonal_min, france_seasonal_min)
                                    combined_max = max(marne_seasonal_max, france_seasonal_max)
                                    fig_seasonal.update_layout(yaxis=dict(range=[combined_min - 0.5, combined_max + 0.5]))
                            except:
                                pass

                        fig_seasonal.update_layout(
                            height=250,
                            margin=dict(t=40, b=30, l=40, r=40)
                        )
                        st.plotly_chart(fig_seasonal, width='stretch')

                except Exception as e:
                    st.info(f"Seasonal decomposition not available for France: {str(e)}")

    with tab2:
        st.subheader("Monthly Occupancy Patterns Across Years")

        # Create monthly analysis
        if ((marne_processed is not None and "Marne" in selected_regions) or
            (france_processed is not None and "France" in selected_regions)):

            fig = go.Figure()

            if "Marne" in selected_regions and marne_processed is not None:
                # Add month and year columns for analysis
                marne_analysis = marne_processed.copy()
                marne_analysis['Month'] = marne_analysis['Date'].dt.month
                marne_analysis['Year'] = marne_analysis['Date'].dt.year

                # Group by month and get all years
                monthly_marne = marne_analysis.groupby(['Month', 'Year'])['Occupancy_Rate'].mean().reset_index()

                # Create box plot data
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

                for month in range(1, 13):
                    month_data = monthly_marne[monthly_marne['Month'] == month]['Occupancy_Rate']
                    if len(month_data) > 0:
                        fig.add_trace(go.Box(
                            y=month_data,
                            name=months[month-1],
                            boxmean=True,
                            marker_color='#1f77b4',
                            showlegend=False
                        ))

            if "France" in selected_regions and france_processed is not None:
                # Add month and year columns for analysis
                france_analysis = france_processed.copy()
                france_analysis['Month'] = france_analysis['Date'].dt.month
                france_analysis['Year'] = france_analysis['Date'].dt.year

                # Group by month
                monthly_france = france_analysis.groupby(['Month', 'Year'])['Occupancy_Rate'].mean().reset_index()

                # If we have both datasets, create separate box plots
                if "Marne" in selected_regions and marne_processed is not None:
                    fig2 = go.Figure()
                    for month in range(1, 13):
                        month_data = monthly_france[monthly_france['Month'] == month]['Occupancy_Rate']
                        if len(month_data) > 0:
                            fig2.add_trace(go.Box(
                                y=month_data,
                                name=months[month-1],
                                boxmean=True,
                                marker_color='#ff7f0e',
                                showlegend=False
                            ))

                    # Calculate shared y-axis range for monthly patterns
                    marne_monthly_min = monthly_marne['Occupancy_Rate'].min()
                    marne_monthly_max = monthly_marne['Occupancy_Rate'].max()
                    france_monthly_min = monthly_france['Occupancy_Rate'].min()
                    france_monthly_max = monthly_france['Occupancy_Rate'].max()
                    combined_min = min(marne_monthly_min, france_monthly_min)
                    combined_max = max(marne_monthly_max, france_monthly_max)
                    y_range = [combined_min - 2, combined_max + 2]

                    fig.update_layout(
                        title="Marne - Monthly Occupancy Distribution",
                        xaxis_title="Month",
                        yaxis_title="Occupancy Rate (%)",
                        height=320,
                        margin=dict(t=50, b=40, l=40, r=40),
                        yaxis=dict(range=y_range)
                    )

                    fig2.update_layout(
                        title="France - Monthly Occupancy Distribution",
                        xaxis_title="Month",
                        yaxis_title="Occupancy Rate (%)",
                        height=320,
                        margin=dict(t=50, b=40, l=40, r=40),
                        yaxis=dict(range=y_range)
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig, width='stretch')

                    with col2:
                        st.plotly_chart(fig2, width='stretch')
                else:
                    # Only France data
                    for month in range(1, 13):
                        month_data = monthly_france[monthly_france['Month'] == month]['Occupancy_Rate']
                        if len(month_data) > 0:
                            fig.add_trace(go.Box(
                                y=month_data,
                                name=months[month-1],
                                boxmean=True,
                                marker_color='#ff7f0e',
                                showlegend=False
                            ))

                    fig.update_layout(
                        title="France - Monthly Occupancy Distribution",
                        xaxis_title="Month",
                        yaxis_title="Occupancy Rate (%)",
                        height=400
                    )
                    st.plotly_chart(fig, width='stretch')
            else:
                # Only Marne data
                fig.update_layout(
                    title="Marne - Monthly Occupancy Distribution",
                    xaxis_title="Month",
                    yaxis_title="Occupancy Rate (%)",
                    height=400
                )
                st.plotly_chart(fig, width='stretch')

    # Add data toggle in sidebar for advanced users
    if st.sidebar.checkbox("Show Raw Data (Advanced)", value=False):
        st.header("📋 Raw Data")

        if "Marne" in selected_regions and marne_processed is not None:
            st.subheader("Marne Data")
            st.dataframe(marne_processed, width='stretch')

        if "France" in selected_regions and france_processed is not None:
            st.subheader("France Data")
            st.dataframe(france_processed, width='stretch')

    # Footer
    st.markdown("---")
    st.markdown("**Data Source:** INSEE (Institut National de la Statistique et des Études Économiques)")
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()