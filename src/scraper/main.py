import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import pandas as pd

def setup_chrome_driver():
    """Setup Chrome driver with appropriate options for web scraping"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    
    # Set download directory
    download_dir = os.path.abspath("data")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Use webdriver-manager to handle driver installation
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def download_boletin_csv():
    """
    Download CSV data from Boletín Concursal website
    Returns: bool - True if successful, False otherwise
    """
    url = "https://www.boletinconcursal.cl/boletin/procedimientos"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Setup driver
        driver = setup_chrome_driver()
        
        # Navigate to the website
        print("Navigating to website...")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        
        # Find and click the CSV download button
        print("Looking for CSV download button...")
        csv_button = wait.until(
            EC.element_to_be_clickable((By.ID, "btnRegistroCsv"))
        )
        
        print("Clicking CSV download button...")
        csv_button.click()
        
        # Wait for download to complete
        print("Waiting for download to complete...")
        time.sleep(10)  # Give time for download
        
        # Check if file was downloaded
        expected_files = [f for f in os.listdir("data") if f.endswith('.csv')]
        
        if expected_files:
            # Rename the downloaded file to our expected name
            latest_file = max([os.path.join("data", f) for f in expected_files], 
                            key=os.path.getctime)
            target_file = "data/boletin_concursal.csv"
            
            if latest_file != target_file:
                os.rename(latest_file, target_file)
            
            print(f"Successfully downloaded CSV file: {target_file}")
            return True
        else:
            print("No CSV file found after download attempt")
            return False
            
    except Exception as e:
        print(f"Error downloading CSV: {str(e)}")
        return False
    
    finally:
        if 'driver' in locals():
            driver.quit()

def get_csv_data():
    """
    Read the downloaded CSV file and return as pandas DataFrame
    Returns: pandas.DataFrame or None if file doesn't exist
    """
    csv_path = "data/boletin_concursal.csv"
    
    if os.path.exists(csv_path):
        try:
            # Read CSV without automatic date parsing first
            df = pd.read_csv(csv_path)
            
            # Find and fix date columns with DD/MM/YYYY format
            for col in df.columns:
                if 'fecha' in col.lower() and ('publicacion' in col.lower() or 'publicación' in col.lower()):
                    try:
                        # Parse dates as DD/MM/YYYY format
                        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                        print(f"Parsed {col} column as DD/MM/YYYY format")
                    except:
                        # If DD/MM/YYYY fails, try automatic parsing
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            print(f"Parsed {col} column with automatic format detection")
                        except:
                            print(f"Could not parse {col} column as dates")
            
            print(f"Successfully loaded existing CSV with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return None
    else:
        print("CSV file not found.")
        return None

def has_existing_data():
    """
    Check if CSV file already exists
    Returns: bool - True if file exists and is readable
    """
    csv_path = "data/boletin_concursal.csv"
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return len(df) > 0
        except:
            return False
    return False

def update_data(force_update=False):
    """
    Main function to update data - downloads CSV and returns DataFrame
    Args:
        force_update (bool): If True, forces download even if data exists
    Returns: pandas.DataFrame or None
    """
    print("Starting data update process...")
    
    # Check if we already have data and don't need to force update
    if not force_update and has_existing_data():
        print("Using existing CSV data (use force_update=True to download fresh data)")
        return get_csv_data()
    
    print("Attempting to download fresh data...")
    
    # Try the main Selenium method first
    if download_boletin_csv():
        # Load and return the data
        return get_csv_data()
    else:
        print("Selenium method failed, trying fallback method...")
        # Try the fallback method
        try:
            from .fallback import download_csv_direct, get_sample_data
            
            if download_csv_direct():
                return get_csv_data()
            else:
                print("Fallback method also failed...")
                # If we have existing data, use it
                if has_existing_data():
                    print("Using existing CSV data as fallback")
                    return get_csv_data()
                else:
                    print("No existing data found, creating sample data for demo...")
                    if get_sample_data():
                        return get_csv_data()
                    else:
                        return None
        except ImportError:
            print("Fallback module not available")
            # Try to use existing data
            if has_existing_data():
                print("Using existing CSV data")
                return get_csv_data()
            return None
        except Exception as e:
            print(f"Error in fallback: {str(e)}")
            # Try to use existing data
            if has_existing_data():
                print("Using existing CSV data")
                return get_csv_data()
            return None

if __name__ == "__main__":
    # Test the scraper
    df = update_data()
    if df is not None:
        print("Sample data:")
        print(df.head())
