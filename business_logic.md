# Business Logic Documentation

## Overview
This document describes the business logic implemented in the Boletín Concursal Streamlit application for filtering and displaying procedural data.

## Data Source
- **Source**: https://www.boletinconcursal.cl/boletin/procedimientos
- **Method**: CSV download via button ID "btnRegistroCsv"
- **File**: `data/boletin_concursal.csv`

## Data Structure
The CSV contains the following columns:
- **Rol**: Case identifier
- **Procedimiento Concursal**: Type of bankruptcy procedure
- **Deudor**: Debtor name
- **RUT**: Tax identification number
- **Veedor Liquidador Titular**: Appointed liquidator/supervisor
- **Nombre Publicación**: Publication name/type
- **Tribunal**: Court name
- **Fecha Publicación**: Publication date

## Summary Tables Logic

### 1. Renegociaciones (Debt Renegotiations)

#### Purpose
Identifies debt renegotiation procedures that have been admitted for processing.

#### Filtering Criteria
The system applies **ALL** of the following conditions (AND logic):

1. **Procedure Type Filter**:
   - `Procedimiento Concursal` column must contain "renegociación" (case-insensitive)

2. **Publication Type Filter**:
   - `Nombre Publicación` column must contain "resolución de admisibilidad" (case-insensitive)

3. **Exclusion Filter**:
   - `Nombre Publicación` column must **NOT** contain "antecedentes resolución de admisibilidad" (case-insensitive)
   - This excludes preliminary documentation records

4. **Date Filter** (optional):
   - If date range is specified, filters by `Fecha Publicación` within the selected range
   - Default range: Current month start minus 14 days to today

#### Implementation Logic
```python
# Step 1: Procedure type check
procedimiento_mask = df['Procedimiento Concursal'].str.contains('renegociación', case=False, na=False)

# Step 2: Publication type check
publicacion_mask = df['Nombre Publicación'].str.contains('resolución de admisibilidad', case=False, na=False)

# Step 3: Exclusion check
exclusion_mask = ~df['Nombre Publicación'].str.contains('antecedentes resolución de admisibilidad', case=False, na=False)

# Step 4: Combine all conditions
final_mask = procedimiento_mask & publicacion_mask & exclusion_mask

# Step 5: Apply date filter if specified
if date_range_specified:
    date_mask = (df['Fecha Publicación'] >= start_date) & (df['Fecha Publicación'] <= end_date)
    final_mask = final_mask & date_mask
```

#### Business Rationale
- Focuses on renegotiation procedures that have been formally admitted
- Excludes preliminary documentation to avoid duplicates
- Provides current/recent activity through date filtering

---

### 2. Liquidaciones Voluntarias (Voluntary Liquidations)

#### Purpose
Identifies voluntary liquidation procedures with liquidation resolutions.

#### Filtering Criteria
The system applies **ALL** of the following conditions (AND logic):

1. **Procedure Type Filter** (compound condition):
   - `Procedimiento Concursal` column must contain "liquid" (case-insensitive) **AND**
   - `Procedimiento Concursal` column must contain "volunt" (case-insensitive)

2. **Publication Type Filter** (compound condition):
   - `Nombre Publicación` column must contain "reso" (case-insensitive) **AND**
   - `Nombre Publicación` column must contain "liquida" (case-insensitive)

3. **Exclusion Filter**:
   - `Nombre Publicación` column must **NOT** contain "antecedentes de la resolución de liquidación" (case-insensitive)
   - This excludes preliminary documentation records

4. **Date Filter** (optional):
   - If date range is specified, filters by `Fecha Publicación` within the selected range
   - Default range: Current month start minus 14 days to today

#### Implementation Logic
```python
# Step 1: Procedure type check (both conditions must be true)
liquid_mask = df['Procedimiento Concursal'].str.contains('liquid', case=False, na=False)
volunt_mask = df['Procedimiento Concursal'].str.contains('volunt', case=False, na=False)
procedimiento_mask = liquid_mask & volunt_mask

# Step 2: Publication type check (both conditions must be true)
reso_mask = df['Nombre Publicación'].str.contains('reso', case=False, na=False)
liquida_mask = df['Nombre Publicación'].str.contains('liquida', case=False, na=False)
publicacion_mask = reso_mask & liquida_mask

# Step 3: Exclusion check
exclusion_mask = ~df['Nombre Publicación'].str.contains('antecedentes de la resolución de liquidación', case=False, na=False)

# Step 4: Combine all conditions
final_mask = procedimiento_mask & publicacion_mask & exclusion_mask

# Step 5: Apply date filter if specified
if date_range_specified:
    date_mask = (df['Fecha Publicación'] >= start_date) & (df['Fecha Publicación'] <= end_date)
    final_mask = final_mask & date_mask
```

#### Business Rationale
- Focuses specifically on voluntary liquidation procedures
- Ensures only liquidation resolutions are included (not other types of resolutions)
- Excludes preliminary documentation to avoid duplicates
- Provides current/recent activity through date filtering

---

## Date Filtering Logic

### Centralized Date Processing
- **Function**: `preprocess_dates(df)` handles all date conversions consistently
- **Single Conversion**: Dates are converted only once per DataFrame to avoid conflicts
- **Copy Protection**: Works on DataFrame copies to prevent modifying original data
- **Type Detection**: Only converts if column is not already datetime type

### Default Date Range
- **Start Date**: Current month start minus 14 days
- **End Date**: Today's date
- **Rationale**: Captures recent activity while including end-of-previous-month publications

### Date Column Detection
The system automatically detects the date column by looking for:
1. Column names containing "fecha" (case-insensitive)
2. Column names containing "publicacion" or "publicación" (case-insensitive)
3. Falls back to "Fecha Publicación" if no match found

### Date Parsing
- Converts date strings to datetime objects using `pd.to_datetime(errors='coerce')`
- Handles parsing errors gracefully by continuing without date filter
- Validates date ranges against actual data boundaries
- **Consistency**: All functions use the same centralized preprocessing

---

## Error Handling

### Missing Columns
- If required columns are not found, returns empty DataFrame
- Provides user-friendly error messages
- Continues operation with available data

### Data Quality Issues
- Handles null/NaN values in text columns using `na=False` parameter
- Graceful handling of date parsing errors
- Case-insensitive string matching for robustness

### Fallback Mechanisms
- Uses existing CSV data if scraping fails
- Creates sample data for testing if no data available
- Multiple scraping methods (Selenium + fallback requests)

---

## Performance Considerations

### Efficient Filtering
- Uses pandas vectorized operations for fast filtering
- Boolean masking for optimal performance
- Minimal data copying during filter operations

### Memory Management
- Processes data in-place where possible
- Cleans up temporary variables
- Efficient DataFrame operations

---

## Export Functionality

### Individual Reports
- CSV downloads for each filtered dataset
- Dynamic filenames with timestamps
- Preserves all original columns

### Combined Export
- Excel workbook with separate sheets
- Sheet names: "Renegociaciones" and "Liquidaciones_Voluntarias"
- Maintains data integrity across formats

---

## Configuration

### Customizable Parameters
- Date range selection
- Force data update option
- Export file formats
- Column name variations (accent handling)

### System Settings
- Data directory: `data/`
- CSV filename: `boletin_concursal.csv`
- Update frequency: Manual trigger
- Session state management for data persistence 