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
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('data_download.log', mode='a')  # File output
    ]
)
logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome driver with options suitable for cloud deployment"""
    logger.info("🚀 Setting up Chrome driver...")
    
    try:
        chrome_options = Options()
        
        # Essential options for cloud deployment
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Additional stability options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-default-apps")
        
        # Set download preferences
        prefs = {
            "download.default_directory": os.path.abspath("data"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        logger.info("✅ Chrome options configured")
        
        # Try to create driver
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Chrome driver created successfully")
        
        # Test basic functionality
        driver.get("about:blank")
        logger.info("✅ Chrome driver basic test passed")
        
        return driver
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Chrome driver: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

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
    """Check if CSV file already exists"""
    csv_path = "data/boletin_concursal.csv"
    exists = os.path.exists(csv_path)
    logger.info(f"📁 Checking for existing data at {csv_path}: {'Found' if exists else 'Not found'}")
    
    if exists:
        try:
            size = os.path.getsize(csv_path)
            logger.info(f"📊 Existing file size: {size} bytes")
            
            # Check if file has content
            if size > 100:  # At least 100 bytes
                logger.info("✅ Existing file appears to have content")
                return True
            else:
                logger.warning("⚠️ Existing file is too small, might be empty")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking existing file: {e}")
            return False
    
    return False

def update_data(force_update=False):
    """
    Main function to update data - downloads CSV and returns DataFrame
    Args:
        force_update (bool): If True, forces download even if data exists
    Returns: pandas.DataFrame or None
    """
    logger.info("=" * 60)
    logger.info("🚀 STARTING DATA UPDATE PROCESS")
    logger.info("=" * 60)
    
    # Log environment info
    logger.info(f"🖥️ Current working directory: {os.getcwd()}")
    logger.info(f"🐍 Python executable: {os.sys.executable}")
    logger.info(f"📁 Data directory exists: {os.path.exists('data')}")
    
    # List current directory contents
    try:
        contents = os.listdir('.')
        logger.info(f"📂 Current directory contents: {contents}")
        
        if os.path.exists('data'):
            data_contents = os.listdir('data')
            logger.info(f"📂 Data directory contents: {data_contents}")
    except Exception as e:
        logger.error(f"❌ Error listing directory contents: {e}")
    
    # Check if we already have data and don't need to force update
    if not force_update and has_existing_data():
        logger.info("✅ Using existing CSV data (use force_update=True to download fresh data)")
        return get_csv_data()
    
    logger.info("🔄 Attempting to download fresh data...")
    
    # Try Selenium first
    logger.info("🎯 ATTEMPTING METHOD 1: Selenium")
    try:
        if download_boletin_csv():
            logger.info("✅ Selenium download successful!")
            return get_csv_data()
        else:
            logger.warning("❌ Selenium download failed")
    except Exception as e:
        logger.error(f"❌ Selenium method crashed: {str(e)}")
    
    logger.info("🔄 Selenium method failed, trying fallback method...")
    
    # Try the fallback method
    try:
        from .fallback import download_csv_direct
        
        logger.info("🎯 ATTEMPTING METHOD 2: Direct Download")
        if download_csv_direct():
            logger.info("✅ Direct download successful!")
            return get_csv_data()
        else:
            logger.warning("❌ Direct download method failed...")
            
        # If we have existing data, use it
        if has_existing_data():
            logger.info("✅ Using existing CSV data as fallback")
            return get_csv_data()
        else:
            logger.error("❌ No existing data found and all download methods failed")
            logger.info("💡 Try running the app locally first to download data, then deploy")
            return None
                
    except ImportError as e:
        logger.error(f"❌ Fallback module not available: {e}")
        # Try to use existing data
        if has_existing_data():
            logger.info("✅ Using existing CSV data")
            return get_csv_data()
        logger.error("❌ No fallback options available")
        return None
    except Exception as e:
        logger.error(f"❌ Error in fallback: {str(e)}")
        # Try to use existing data
        if has_existing_data():
            logger.info("✅ Using existing CSV data as last resort")
            return get_csv_data()
        logger.error("❌ All methods failed - no real data available")
        return None

if __name__ == "__main__":
    # Test the scraper
    df = update_data()
    if df is not None:
        print("Sample data:")
        print(df.head())
