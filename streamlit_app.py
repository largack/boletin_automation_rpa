import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import logging

# Set up logging for Streamlit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('streamlit_app.log', mode='a')  # File output
    ]
)
logger = logging.getLogger(__name__)

# Add src directory to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scraper.main import update_data, get_csv_data, has_existing_data

# Configure Streamlit page
st.set_page_config(
    page_title="Boletín Concursal Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_app():
    """Initialize the application by loading existing data if available"""
    if 'data' not in st.session_state:
        existing_data = get_csv_data()
        if existing_data is not None:
            st.session_state.data = existing_data
            st.session_state.last_updated = "From existing file"
            st.session_state.data_loaded = True
        else:
            st.session_state.data_loaded = False

def main():
    """Main Streamlit application"""
    
    # Initialize the app
    initialize_app()
    
    # Sidebar menu
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["📈 Reports", "📋 Summary"],
        index=1  # Make Summary the default page
    )
    
    # Show data status in sidebar
    if st.session_state.get('data_loaded', False):
        st.sidebar.success("✅ Data Available")
        if 'data' in st.session_state:
            st.sidebar.write(f"Records: {len(st.session_state.data)}")
            st.sidebar.write(f"Last Updated: {st.session_state.get('last_updated', 'Unknown')}")
    else:
        st.sidebar.warning("⚠️ No Data")
        st.sidebar.write("Please update data first")
    
    # Add update button to sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("↻ Actualizar Datos", key="sidebar_update_btn", help="Click to download fresh data from Boletín Concursal", use_container_width=True):
        # Use a flag to trigger update in main area
        st.session_state.trigger_update = True
    
    # Main content based on selected page
    if page == "📈 Reports":
        reports_page()
    elif page == "📋 Summary":
        summary_page()

def update_data_section(force_update=False, context="home"):
    """Handle data update process"""
    logger.info(f"🔄 Streamlit: update_data_section called with force_update={force_update}, context={context}")
    
    st.subheader("📥 Updating Data...")
    
    # Create a progress bar and status
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Set force update in session state
        if force_update:
            st.session_state.force_update = True
            logger.info("🔧 Streamlit: Set force_update flag in session state")
        
        if not force_update and has_existing_data():
            status_text.text("📁 Using existing data...")
            progress_bar.progress(50)
            logger.info("📁 Streamlit: Using existing data")
        else:
            status_text.text("🌐 Connecting to Boletín Concursal website...")
            progress_bar.progress(25)
            logger.info("🌐 Streamlit: Starting fresh data download")
            
            status_text.text("🔍 Looking for CSV download button...")
            progress_bar.progress(50)
            
            status_text.text("⬇️ Downloading CSV file...")
            progress_bar.progress(75)
        
        # Call the load_data function which has comprehensive logging
        logger.info("📊 Streamlit: Calling load_data()...")
        df = load_data()
        
        progress_bar.progress(100)
        
        if df is not None:
            status_text.text("✅ Data loaded successfully!")
            logger.info(f"✅ Streamlit: Data loaded successfully - {len(df)} records")
            
            if force_update:
                st.success(f"Successfully downloaded fresh data with {len(df)} records!")
            else:
                st.success(f"Successfully loaded data with {len(df)} records!")
            
            # Store data in session state for display
            st.session_state.data = df
            st.session_state.data_loaded = True
            st.session_state.last_updated = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info("✅ Streamlit: Data stored in session state")
            
        else:
            status_text.text("❌ Failed to load data")
            logger.error("❌ Streamlit: load_data() returned None")
            st.error("Failed to download or process the CSV file. Please try again.")
            
    except Exception as e:
        progress_bar.progress(100)
        status_text.text("❌ Error occurred during update")
        logger.error(f"❌ Streamlit: Error in update_data_section: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

def reports_page():
    """Reports page with specific filtered reports"""
    st.title("📈 Reports Dashboard")
    st.markdown("---")
    
    # Load data
    if 'data' not in st.session_state:
        existing_data = get_csv_data()
        if existing_data is not None:
            st.session_state.data = existing_data
            st.session_state.last_updated = "From existing file"
    
    if 'data' in st.session_state and st.session_state.data is not None:
        df = st.session_state.data
        
        # Show available columns for debugging
        st.sidebar.header("Available Columns")
        st.sidebar.write("Available columns in dataset:")
        for col in df.columns:
            st.sidebar.write(f"- {col}")
        
        # Report selection
        report_type = st.selectbox(
            "📊 Select Report Type",
            ["Renegociaciones", "Liquidaciones Voluntarias"],
            index=0
        )
        
        st.markdown("---")
        
        if report_type == "Renegociaciones":
            generate_renegociaciones_report(df)
        else:
            generate_liquidaciones_report(df)
            
    else:
        st.warning("⚠️ No data available. Please go to the Summary page and update data first.")
        if st.button("📋 Go to Summary Page"):
            st.rerun()

def generate_renegociaciones_report(df):
    """Generate Renegociaciones report"""
    st.header("🔄 Renegociaciones Report")
    st.markdown("""
    **Audiencia de Renegociación:** Esta audiencia tiene por finalidad que la persona presente su 
    propuesta de pago a los acreedores, quienes, a su vez, presentarán su contrapropuesta y 
    tendrán que votar respecto de la misma.
    
    Aquí hay dos alternativas:
    - Los acreedores y el deudor aceptan la propuesta, en este caso la persona comienza a 
      pagar según lo acordado en la audiencia.
    - Los acreedores no aceptan la propuesta, en este caso la Superintendencia citará a los 
      acreedores y al deudor a la audiencia de ejecución.
    """)
    
    # Check available columns and create flexible filters
    available_cols = df.columns.tolist()
    
    # Try to find the relevant columns (case insensitive)
    procedimiento_col = None
    publicacion_col = None
    
    for col in available_cols:
        col_lower = col.lower()
        if 'procedimiento' in col_lower and 'concursal' in col_lower:
            procedimiento_col = col
        # Be more specific: look for "Nombre Publicación" first, not just any "publicación"
        elif 'nombre' in col_lower and ('publicacion' in col_lower or 'publicación' in col_lower):
            publicacion_col = col
    
    # If we didn't find "Nombre Publicación", look for exact match
    if not publicacion_col:
        for col in available_cols:
            if col == "Nombre Publicación" or col == "Nombre Publicacion":
                publicacion_col = col
                break
    
    # Apply the same filtering as Summary page (using helper function)
    filtered_df = get_renegociaciones_data(df)
    
    st.markdown("---")
    st.subheader(f"📊 Results: {len(filtered_df)} records found")
    
    if len(filtered_df) > 0:
        # Display summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Records", len(filtered_df))
        with col2:
            st.metric("Unique Records", len(filtered_df))
        
        # Display the filtered data with formatted dates
        filtered_df_display = get_renegociaciones_data(df)  # Get fresh data for display
        if len(filtered_df_display) > 0:
            # Find date column for formatting
            _, fecha_col_display = preprocess_dates(filtered_df_display)
            filtered_df_display = format_dates_for_display(filtered_df_display, fecha_col_display)
        st.dataframe(filtered_df_display, use_container_width=True, height=400)
        
        # Download button
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Renegociaciones Report",
            data=csv_data,
            file_name=f"renegociaciones_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No records found matching the criteria.")

def generate_liquidaciones_report(df):
    """Generate Liquidaciones Voluntarias report"""
    st.header("📋 Liquidaciones Voluntarias Report")
    st.markdown("""
    **LIQUIDACIONES VOLUNTARIAS** (Procedimiento más común)
    
    Tiene por finalidad la liquidación rápida y eficiente de los bienes de la Persona Deudora, con el
    objeto de propender al pago de sus acreedores. Se debe tener claridad de quienes pueden ser
    personas deudoras.
    
    **Son personas deudoras:**
    - Las personas naturales contribuyentes del artículo 42 N° 1 del decreto ley N.° 824, del
      Ministerio de Hacienda, de 1974, que aprueba la Ley sobre Impuesto a la Renta. Es decir, las
      personas naturales sujetas a un contrato de trabajo.
    - Y los demás sujetos de crédito no comprendidos en la definición de empresas deudoras, que
      entrega el artículo 2 N.° 13 de la Ley. Esto es, cualquier persona natural sujeto de crédito tales
      como, dueñas de casa, estudiantes, jubilados, entre otros.

    La persona debe presentar la solicitud ante el tribunal competente, la cual debe cumplir con una
    serie de requisitos. También esta solicitud deberá acompañarse con:
    - Lista de sus bienes, lugar en que se encuentren y los gravámenes que les afecten.
    - Lista de los bienes legalmente excluidos de la Liquidación (bienes inembargables).
    - Enumeración de sus juicios pendientes con efectos patrimoniales.
    - Estado de deudas, con nombre, domicilio y datos de contacto de los acreedores, así
      como de la naturaleza de sus créditos.
    """)
    
    # Apply the same filtering as Summary page (using helper function for initial filter)
    filtered_df = get_liquidaciones_data(df)
    
    st.markdown("---")
    st.subheader(f"📊 Results: {len(filtered_df)} records found")
    
    if len(filtered_df) > 0:
        # Display summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Records", len(filtered_df))
        with col2:
            st.metric("Unique Records", len(filtered_df))
        
        # Display the filtered data with formatted dates
        filtered_df_display = get_liquidaciones_data(df)  # Get fresh data for display
        if len(filtered_df_display) > 0:
            # Find date column for formatting
            _, fecha_col_display = preprocess_dates(filtered_df_display)
            filtered_df_display = format_dates_for_display(filtered_df_display, fecha_col_display)
        st.dataframe(filtered_df_display, use_container_width=True, height=400)
        
        # Download button
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Liquidaciones Report",
            data=csv_data,
            file_name=f"liquidaciones_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No records found matching the criteria.")

def get_renegociaciones_data(df, start_date=None, end_date=None):
    """Get filtered data for Renegociaciones report"""
    try:
        # Preprocess dates centrally
        df_processed, fecha_col = preprocess_dates(df)
        
        # Find columns
        procedimiento_col = None
        publicacion_col = None
        
        for col in df_processed.columns:
            col_lower = col.lower()
            if 'procedimiento' in col_lower and 'concursal' in col_lower:
                procedimiento_col = col
            elif 'nombre' in col_lower and ('publicacion' in col_lower or 'publicación' in col_lower):
                publicacion_col = col
        
        if not publicacion_col:
            for col in df_processed.columns:
                if col == "Nombre Publicación" or col == "Nombre Publicacion":
                    publicacion_col = col
                    break
        
        if procedimiento_col and publicacion_col and both_in_columns(df_processed, [procedimiento_col, publicacion_col]):
            # Apply content filters
            mask1 = df_processed[procedimiento_col].astype(str).str.contains(
                'renegociación|renegociacion', case=False, na=False
            )
            mask2 = df_processed[publicacion_col].astype(str).str.contains(
                'resolución de admisibilidad|resolucion de admisibilidad', case=False, na=False
            )
            exclusion_mask = ~df_processed[publicacion_col].astype(str).str.contains(
                'antecedentes resolución de admisibilidad|antecedentes resolucion de admisibilidad', case=False, na=False
            )
            
            final_mask = mask1 & mask2 & exclusion_mask
            
            # Apply date filter if provided and column exists
            if start_date and end_date and fecha_col in df_processed.columns:
                try:
                    date_mask = (
                        (df_processed[fecha_col].dt.date >= start_date) & 
                        (df_processed[fecha_col].dt.date <= end_date)
                    )
                    final_mask = final_mask & date_mask
                except:
                    pass  # Continue without date filter if parsing fails
            
            return df_processed[final_mask]
        else:
            return pd.DataFrame()  # Return empty DataFrame if columns not found
    except Exception:
        return pd.DataFrame()

def get_liquidaciones_data(df, start_date=None, end_date=None):
    """Get filtered data for Liquidaciones Voluntarias report"""
    try:
        # Preprocess dates centrally
        df_processed, fecha_col = preprocess_dates(df)
        
        # Find columns
        procedimiento_col = None
        publicacion_col = None
        
        for col in df_processed.columns:
            col_lower = col.lower()
            if 'procedimiento' in col_lower and 'concursal' in col_lower:
                procedimiento_col = col
            elif 'nombre' in col_lower and ('publicacion' in col_lower or 'publicación' in col_lower):
                publicacion_col = col
        
        if not publicacion_col:
            for col in df_processed.columns:
                if col == "Nombre Publicación" or col == "Nombre Publicacion":
                    publicacion_col = col
                    break
        
        if procedimiento_col and publicacion_col and both_in_columns(df_processed, [procedimiento_col, publicacion_col]):
            # Apply content filters
            procedimiento_mask = (
                df_processed[procedimiento_col].astype(str).str.contains('liquid', case=False, na=False) &
                df_processed[procedimiento_col].astype(str).str.contains('volunt', case=False, na=False)
            )
            publicacion_mask = (
                df_processed[publicacion_col].astype(str).str.contains('reso', case=False, na=False) &
                df_processed[publicacion_col].astype(str).str.contains('liquida', case=False, na=False)
            )
            exclusion_mask = ~df_processed[publicacion_col].astype(str).str.contains(
                'antecedentes de la resolución de liquidación|antecedentes de la resolucion de liquidacion', case=False, na=False
            )
            
            final_mask = procedimiento_mask & publicacion_mask & exclusion_mask
            
            # Apply date filter if provided and column exists
            if start_date and end_date and fecha_col in df_processed.columns:
                try:
                    date_mask = (
                        (df_processed[fecha_col].dt.date >= start_date) & 
                        (df_processed[fecha_col].dt.date <= end_date)
                    )
                    final_mask = final_mask & date_mask
                except:
                    pass  # Continue without date filter if parsing fails
            
            return df_processed[final_mask]
        else:
            return pd.DataFrame()  # Return empty DataFrame if columns not found
    except Exception:
        return pd.DataFrame()

def both_in_columns(df, cols):
    """Helper function to check if both columns exist in dataframe"""
    return all(col in df.columns for col in cols)

def preprocess_dates(df):
    """
    Centralized date preprocessing function
    Converts date columns to datetime once and returns a copy
    """
    df_copy = df.copy()
    
    # Find the date column
    fecha_col = None
    for col in df_copy.columns:
        if 'fecha' in col.lower() and ('publicacion' in col.lower() or 'publicación' in col.lower()):
            fecha_col = col
            break
    
    if not fecha_col:
        fecha_col = "Fecha Publicación"  # fallback
    
    # Convert date column to datetime if it exists and isn't already datetime
    if fecha_col in df_copy.columns:
        try:
            # Only convert if not already datetime (dates should be correctly parsed at source now)
            if not pd.api.types.is_datetime64_any_dtype(df_copy[fecha_col]):
                df_copy[fecha_col] = pd.to_datetime(df_copy[fecha_col], errors='coerce')
        except Exception as e:
            print(f"Warning: Could not convert {fecha_col} to datetime: {e}")
    
    return df_copy, fecha_col

def format_dates_for_display(df, fecha_col):
    """Format date columns for consistent display as dd/mm/YYYY"""
    df_display = df.copy()
    
    if fecha_col in df_display.columns:
        try:
            # Ensure it's datetime first
            if not pd.api.types.is_datetime64_any_dtype(df_display[fecha_col]):
                df_display[fecha_col] = pd.to_datetime(df_display[fecha_col], errors='coerce')
            
            # Format as dd/mm/YYYY string for display
            df_display[fecha_col] = df_display[fecha_col].dt.strftime('%d/%m/%Y')
            
            # Replace NaT with empty string
            df_display[fecha_col] = df_display[fecha_col].replace('NaT', '')
            
        except Exception as e:
            print(f"Warning: Could not format {fecha_col} for display: {e}")
    
    return df_display

def debug_specific_record(df, target_rol="C-789-2025"):
    """Debug function to check why a specific record is not appearing"""
    print(f"\n=== DEBUGGING RECORD: {target_rol} ===")
    
    # Find the record
    if 'Rol' in df.columns:
        target_record = df[df['Rol'] == target_rol]
        if len(target_record) > 0:
            record = target_record.iloc[0]
            print(f"Found record: {record.to_dict()}")
            
            # Test each filter step
            procedimiento = str(record.get('Procedimiento Concursal', ''))
            publicacion = str(record.get('Nombre Publicación', ''))
            fecha = record.get('Fecha Publicación', '')
            
            print(f"\nTesting filters:")
            print(f"  Procedimiento: '{procedimiento}'")
            print(f"  Publicación: '{publicacion}'")
            print(f"  Fecha: '{fecha}'")
            
            # Test procedure filters
            liquid_test = 'liquid' in procedimiento.lower()
            volunt_test = 'volunt' in procedimiento.lower()
            print(f"  Contains 'liquid': {liquid_test}")
            print(f"  Contains 'volunt': {volunt_test}")
            print(f"  Procedure filter passes: {liquid_test and volunt_test}")
            
            # Test publication filters
            reso_test = 'reso' in publicacion.lower()
            liquida_test = 'liquida' in publicacion.lower()
            print(f"  Contains 'reso': {reso_test}")
            print(f"  Contains 'liquida': {liquida_test}")
            print(f"  Publication filter passes: {reso_test and liquida_test}")
            
            # Test exclusion
            exclusion_test = 'antecedentes de la resolución de liquidación' not in publicacion.lower()
            print(f"  Exclusion filter passes: {exclusion_test}")
            
            # Test date parsing
            try:
                parsed_date = pd.to_datetime(fecha, errors='coerce')
                print(f"  Parsed date: {parsed_date}")
                if pd.notna(parsed_date):
                    print(f"  Date as date(): {parsed_date.date()}")
                else:
                    print(f"  Date parsing failed!")
            except Exception as e:
                print(f"  Date parsing error: {e}")
                
        else:
            print(f"Record with Rol '{target_rol}' not found!")
    else:
        print("'Rol' column not found in data!")
    
    print("=== END DEBUG ===\n")

def apply_renegociaciones_filters(df_processed, fecha_col, start_date=None, end_date=None):
    """Apply renegociaciones filters to already-preprocessed data"""
    try:
        # Find columns
        procedimiento_col = None
        publicacion_col = None
        
        for col in df_processed.columns:
            col_lower = col.lower()
            if 'procedimiento' in col_lower and 'concursal' in col_lower:
                procedimiento_col = col
            elif 'nombre' in col_lower and ('publicacion' in col_lower or 'publicación' in col_lower):
                publicacion_col = col
        
        if not publicacion_col:
            for col in df_processed.columns:
                if col == "Nombre Publicación" or col == "Nombre Publicacion":
                    publicacion_col = col
                    break
        
        if procedimiento_col and publicacion_col and both_in_columns(df_processed, [procedimiento_col, publicacion_col]):
            # Apply content filters
            mask1 = df_processed[procedimiento_col].astype(str).str.contains(
                'renegociación|renegociacion', case=False, na=False
            )
            mask2 = df_processed[publicacion_col].astype(str).str.contains(
                'resolución de admisibilidad|resolucion de admisibilidad', case=False, na=False
            )
            exclusion_mask = ~df_processed[publicacion_col].astype(str).str.contains(
                'antecedentes resolución de admisibilidad|antecedentes resolucion de admisibilidad', case=False, na=False
            )
            
            final_mask = mask1 & mask2 & exclusion_mask
            
            # Apply date filter if provided and column exists
            if start_date and end_date and fecha_col in df_processed.columns:
                try:
                    date_mask = (
                        (df_processed[fecha_col].dt.date >= start_date) & 
                        (df_processed[fecha_col].dt.date <= end_date)
                    )
                    final_mask = final_mask & date_mask
                except:
                    pass  # Continue without date filter if parsing fails
            
            return df_processed[final_mask]
        else:
            return pd.DataFrame()  # Return empty DataFrame if columns not found
    except Exception:
        return pd.DataFrame()

def apply_liquidaciones_filters(df_processed, fecha_col, start_date=None, end_date=None):
    """Apply liquidaciones filters to already-preprocessed data"""
    try:
        # Find columns
        procedimiento_col = None
        publicacion_col = None
        
        for col in df_processed.columns:
            col_lower = col.lower()
            if 'procedimiento' in col_lower and 'concursal' in col_lower:
                procedimiento_col = col
            elif 'nombre' in col_lower and ('publicacion' in col_lower or 'publicación' in col_lower):
                publicacion_col = col
        
        if not publicacion_col:
            for col in df_processed.columns:
                if col == "Nombre Publicación" or col == "Nombre Publicacion":
                    publicacion_col = col
                    break
        
        if procedimiento_col and publicacion_col and both_in_columns(df_processed, [procedimiento_col, publicacion_col]):
            # Apply content filters
            procedimiento_mask = (
                df_processed[procedimiento_col].astype(str).str.contains('liquid', case=False, na=False) &
                df_processed[procedimiento_col].astype(str).str.contains('volunt', case=False, na=False)
            )
            publicacion_mask = (
                df_processed[publicacion_col].astype(str).str.contains('reso', case=False, na=False) &
                df_processed[publicacion_col].astype(str).str.contains('liquida', case=False, na=False)
            )
            exclusion_mask = ~df_processed[publicacion_col].astype(str).str.contains(
                'antecedentes de la resolución de liquidación|antecedentes de la resolucion de liquidacion', case=False, na=False
            )
            
            final_mask = procedimiento_mask & publicacion_mask & exclusion_mask
            
            # Apply date filter if provided and column exists
            if start_date and end_date and fecha_col in df_processed.columns:
                try:
                    date_mask = (
                        (df_processed[fecha_col].dt.date >= start_date) & 
                        (df_processed[fecha_col].dt.date <= end_date)
                    )
                    final_mask = final_mask & date_mask
                except Exception as e:
                    pass  # Continue without date filter if parsing fails
            
            return df_processed[final_mask]
        else:
            return pd.DataFrame()  # Return empty DataFrame if columns not found
    except Exception:
        return pd.DataFrame()

def summary_page():
    """Summary page showing both filtered datasets"""
    st.title("📋 PROCEDIMIENTOS DE RENEGOCIACION")
    
    # Handle update trigger from sidebar
    if st.session_state.get('trigger_update', False):
        update_data_section(force_update=True, context="summary")
        st.session_state.trigger_update = False
    
    # Load data
    if 'data' not in st.session_state:
        existing_data = get_csv_data()
        if existing_data is not None:
            st.session_state.data = existing_data
            st.session_state.last_updated = "From existing file"
    
    if 'data' in st.session_state and st.session_state.data is not None:
        df = st.session_state.data
        
        # Date filter section
        st.write("**📅 Filter by Date Range:**")
        
        # Preprocess dates centrally
        df_processed, fecha_col = preprocess_dates(df)
        
        start_date = None
        end_date = None
        
        if fecha_col in df_processed.columns:
            try:
                # Get date range from data for validation
                if not df_processed[fecha_col].isna().all():
                    data_min_date = df_processed[fecha_col].min().date()
                    data_max_date = df_processed[fecha_col].max().date()
                else:
                    data_min_date = pd.Timestamp.now().date()
                    data_max_date = pd.Timestamp.now().date()
                
                # Set default date range: current month - 14 days
                from datetime import date, timedelta
                today = date.today()
                
                # Calculate default start date (current month - 14 days)
                current_month_start = today.replace(day=1)
                default_start = current_month_start - timedelta(days=14)
                
                # Ensure default dates are within data range
                default_start_date = max(default_start, data_min_date)
                default_end_date = min(today, data_max_date)
                
                # Date input widgets
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Start Date",
                        value=default_start_date,
                        min_value=data_min_date,
                        max_value=data_max_date,
                        key="summary_start_date"
                    )
                with col2:
                    end_date = st.date_input(
                        "End Date",
                        value=default_end_date,
                        min_value=data_min_date,
                        max_value=data_max_date,
                        key="summary_end_date"
                    )
                
                if start_date and end_date:
                    st.info(f"📅 Date range: {start_date} to {end_date}")
            
            except Exception as e:
                st.warning(f"⚠️ Could not parse dates in {fecha_col} column: {str(e)}")
        else:
            st.warning(f"⚠️ '{fecha_col}' column not found in data")
        
        st.markdown("---")
        
        # Get filtered data with date filter - use consistent preprocessing
        # Since we already have preprocessed data, apply filters directly
        renegociaciones_df = apply_renegociaciones_filters(df_processed, fecha_col, start_date, end_date)
        liquidaciones_df = apply_liquidaciones_filters(df_processed, fecha_col, start_date, end_date)
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Records", f"{len(df):,}")
        with col2:
            st.metric("🔄 Renegociaciones", f"{len(renegociaciones_df):,}")
        with col3:
            st.metric("📋 Liquidaciones Voluntarias", f"{len(liquidaciones_df):,}")
        
        st.markdown("---")
        
        # Renegociaciones Section
        st.subheader("🔄 Renegociaciones")
        if len(renegociaciones_df) > 0:
            st.success(f"Found {len(renegociaciones_df):,} renegociaciones records")
            
            # Download button
            csv_data_renegociaciones = renegociaciones_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Renegociaciones Data",
                data=csv_data_renegociaciones,
                file_name=f"renegociaciones_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Format dates for display
            renegociaciones_display = format_dates_for_display(renegociaciones_df, fecha_col)
            st.dataframe(renegociaciones_display, use_container_width=True, height=300)
        else:
            st.warning("No renegociaciones records found matching the criteria")
        
        st.markdown("---")
        
        # Liquidaciones Section
        st.subheader("📋 Liquidaciones Voluntarias")
        if len(liquidaciones_df) > 0:
            st.success(f"Found {len(liquidaciones_df):,} liquidaciones voluntarias records")
            
            # Download button
            csv_data_liquidaciones = liquidaciones_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Liquidaciones Data",
                data=csv_data_liquidaciones,
                file_name=f"liquidaciones_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Format dates for display
            liquidaciones_display = format_dates_for_display(liquidaciones_df, fecha_col)
            st.dataframe(liquidaciones_display, use_container_width=True, height=300)
        else:
            st.warning("No liquidaciones voluntarias records found matching the criteria")
        
        # Combined download
        if len(renegociaciones_df) > 0 or len(liquidaciones_df) > 0:
            st.markdown("---")
            st.subheader("📦 Combined Export")
            
            # Create combined Excel file with separate sheets
            from io import BytesIO
            buffer = BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if len(renegociaciones_df) > 0:
                    renegociaciones_df.to_excel(writer, sheet_name='Renegociaciones', index=False)
                if len(liquidaciones_df) > 0:
                    liquidaciones_df.to_excel(writer, sheet_name='Liquidaciones_Voluntarias', index=False)
            
            st.download_button(
                label="📊 Download Combined Excel Report",
                data=buffer.getvalue(),
                file_name=f"boletin_summary_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    else:
        st.warning("⚠️ No data available. Please go to the Summary page and update data first.")
        if st.button("📋 Go to Summary Page"):
            st.rerun()

def has_existing_data():
    """Check if CSV file already exists"""
    try:
        from src.scraper.main import has_existing_data as check_existing
        return check_existing()
    except:
        return False

def get_csv_data():
    """Get CSV data if it exists"""
    try:
        from src.scraper.main import get_csv_data as get_data
        return get_data()
    except:
        return None

def load_data():
    """Load data with comprehensive logging"""
    logger.info("🔄 Streamlit: Starting data load process...")
    
    try:
        from src.scraper.main import update_data
        logger.info("✅ Streamlit: Successfully imported update_data function")
        
        # Check if we should force update
        force_update = st.session_state.get('force_update', False)
        logger.info(f"🔧 Streamlit: Force update = {force_update}")
        
        # Load the data
        logger.info("📊 Streamlit: Calling update_data()...")
        df = update_data(force_update=force_update)
        
        if df is not None:
            logger.info(f"✅ Streamlit: Data loaded successfully - Shape: {df.shape}")
            logger.info(f"📋 Streamlit: Columns: {list(df.columns)}")
            
            # Reset force update flag
            if 'force_update' in st.session_state:
                st.session_state.force_update = False
                logger.info("🔧 Streamlit: Reset force_update flag")
            
            return df
        else:
            logger.error("❌ Streamlit: update_data() returned None")
            return None
            
    except ImportError as e:
        logger.error(f"❌ Streamlit: Import error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Streamlit: Error loading data: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

if __name__ == "__main__":
    main() 