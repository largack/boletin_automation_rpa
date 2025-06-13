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
        if download_csv_with_selenium():
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

def download_csv_with_selenium():
    """Download CSV using Selenium"""
    logger.info("🌐 Starting Selenium download process...")
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    logger.info("📁 Data directory ensured")
    
    # Test directory permissions
    try:
        test_file = "data/test_write.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        logger.info("✅ Data directory is writable")
    except Exception as e:
        logger.error(f"❌ Data directory not writable: {e}")
        return False
    
    driver = setup_chrome_driver()
    if not driver:
        logger.error("❌ Could not setup Chrome driver")
        return False
    
    try:
        url = "https://www.boletinconcursal.cl/boletin/procedimientos"
        logger.info(f"🌐 Navigating to: {url}")
        
        # Set page load timeout
        driver.set_page_load_timeout(60)  # 60 seconds timeout
        
        try:
            driver.get(url)
            logger.info("✅ Page loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load page: {e}")
            return False
        
        # Wait for page to load
        logger.info("⏳ Waiting for page elements to load...")
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("✅ Page body loaded")
        except Exception as e:
            logger.error(f"❌ Page body failed to load: {e}")
            return False
        
        # Log page info
        try:
            page_title = driver.title
            page_url = driver.current_url
            logger.info(f"📄 Page title: {page_title}")
            logger.info(f"📄 Current URL: {page_url}")
        except Exception as e:
            logger.warning(f"⚠️ Could not get page info: {e}")
        
        # Look for the CSV download button
        logger.info("🔍 Looking for CSV download button...")
        csv_button = None
        
        try:
            # Try to find the button by ID first
            csv_button = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "btnRegistroCsv"))
            )
            logger.info("✅ CSV button found by ID")
            
            # Check if button is visible and enabled
            if csv_button.is_displayed():
                logger.info("✅ CSV button is visible")
            else:
                logger.warning("⚠️ CSV button is not visible")
            
            if csv_button.is_enabled():
                logger.info("✅ CSV button is enabled")
            else:
                logger.warning("⚠️ CSV button is not enabled")
                
        except Exception as e:
            logger.error(f"❌ CSV button not found by ID: {e}")
            
            # Try to find any button with CSV-related text
            logger.info("🔍 Searching for alternative CSV buttons...")
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"Found {len(buttons)} buttons on page")
                
                for i, button in enumerate(buttons):
                    try:
                        text = button.text.lower()
                        logger.info(f"Button {i}: '{text}' (visible: {button.is_displayed()}, enabled: {button.is_enabled()})")
                        if 'csv' in text or 'descargar' in text or 'exportar' in text:
                            logger.info(f"✅ Found potential CSV button: '{text}'")
                            csv_button = button
                            break
                    except Exception as btn_e:
                        logger.warning(f"⚠️ Error checking button {i}: {btn_e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Error searching for buttons: {e}")
        
        if not csv_button:
            logger.error("❌ No CSV download button found")
            return False
        
        # Wait for button to be clickable
        logger.info("⏳ Waiting for CSV button to be clickable...")
        try:
            clickable_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(csv_button)
            )
            logger.info("✅ CSV button is clickable")
        except Exception as e:
            logger.error(f"❌ CSV button not clickable: {e}")
            # Try to click anyway
            clickable_button = csv_button
        
        # Get initial file list
        initial_files = set()
        if os.path.exists("data"):
            initial_files = set(os.listdir("data"))
            logger.info(f"📁 Initial files in data directory: {initial_files}")
        
        # Click the button
        logger.info("🖱️ Clicking CSV download button...")
        try:
            # Try regular click first
            clickable_button.click()
            logger.info("✅ Button clicked successfully")
        except Exception as e:
            logger.warning(f"⚠️ Regular click failed: {e}")
            try:
                # Try JavaScript click
                driver.execute_script("arguments[0].click();", clickable_button)
                logger.info("✅ Button clicked via JavaScript")
            except Exception as js_e:
                logger.error(f"❌ JavaScript click also failed: {js_e}")
                return False
        
        # Wait for download to complete
        logger.info("⏳ Waiting for download to complete...")
        download_wait_time = 60  # Increased timeout for large file
        download_detected = False
        
        for i in range(download_wait_time):
            time.sleep(1)
            
            # Check for new files
            current_files = set()
            if os.path.exists("data"):
                current_files = set(os.listdir("data"))
            
            new_files = current_files - initial_files
            if new_files:
                logger.info(f"📁 New files detected: {new_files}")
                download_detected = True
            
            # Check specifically for our CSV file or any CSV file
            csv_path = "data/boletin_concursal.csv"
            actual_csv_files = []
            
            # Look for any CSV files in the data directory
            if os.path.exists("data"):
                for file in os.listdir("data"):
                    if file.endswith('.csv') and not file.startswith('.'):
                        actual_csv_files.append(file)
                        logger.info(f"📄 Found CSV file: {file}")
            
            # Check if our expected file exists
            if os.path.exists(csv_path):
                size = os.path.getsize(csv_path)
                logger.info(f"📊 Expected CSV file found! Size: {size} bytes")
                
                # Wait for file to finish downloading (size should stabilize)
                if size > 1000:  # At least 1KB
                    time.sleep(2)  # Wait a bit more
                    new_size = os.path.getsize(csv_path)
                    if new_size == size and size > 10000:  # Size stable and substantial
                        logger.info(f"✅ Download complete! Final size: {size} bytes")
                        return True
                    elif new_size > size:
                        logger.info(f"📈 Download still in progress... Size: {new_size} bytes")
                        continue
            
            # Check if any other CSV file was downloaded
            elif actual_csv_files:
                for csv_file in actual_csv_files:
                    full_path = f"data/{csv_file}"
                    size = os.path.getsize(full_path)
                    logger.info(f"📊 Found alternative CSV file: {csv_file}, Size: {size} bytes")
                    
                    if size > 10000:  # Substantial size
                        # Wait for file to stabilize
                        time.sleep(2)
                        new_size = os.path.getsize(full_path)
                        
                        if new_size == size:  # Size is stable
                            logger.info(f"✅ Renaming {csv_file} to boletin_concursal.csv")
                            try:
                                # Rename the file to our expected name
                                os.rename(full_path, csv_path)
                                logger.info(f"✅ Download complete! Final size: {size} bytes")
                                return True
                            except Exception as e:
                                logger.error(f"❌ Error renaming file: {e}")
                                # Try copying instead
                                try:
                                    import shutil
                                    shutil.copy2(full_path, csv_path)
                                    logger.info(f"✅ File copied successfully! Size: {size} bytes")
                                    return True
                                except Exception as copy_e:
                                    logger.error(f"❌ Error copying file: {copy_e}")
                        else:
                            logger.info(f"📈 File still growing... Size: {new_size} bytes")
                            continue
            
            # Log progress every 10 seconds
            if i % 10 == 0 and i > 0:
                logger.info(f"⏳ Still waiting for download... ({i}/{download_wait_time}s)")
                
                # Check browser downloads (if accessible)
                try:
                    # Try to get download status from browser
                    downloads = driver.execute_script("return navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.getUserMedia;")
                    if downloads:
                        logger.info("📥 Browser download API detected")
                except:
                    pass
        
        # Final check - look for any CSV files and rename if needed
        csv_path = "data/boletin_concursal.csv"
        
        if os.path.exists(csv_path):
            size = os.path.getsize(csv_path)
            logger.info(f"📊 Final check - CSV file size: {size} bytes")
            if size > 10000:  # At least 10KB
                logger.info("✅ CSV file downloaded successfully!")
                return True
            else:
                logger.error(f"❌ CSV file too small ({size} bytes) - likely incomplete")
                return False
        else:
            # Check for any CSV files that might have been downloaded with different names
            if os.path.exists("data"):
                all_files = os.listdir("data")
                logger.info(f"📁 All files in data directory: {all_files}")
                
                csv_files = [f for f in all_files if f.endswith('.csv') and not f.startswith('.')]
                if csv_files:
                    logger.info(f"📄 Found CSV files: {csv_files}")
                    
                    # Try to use the largest CSV file
                    largest_csv = None
                    largest_size = 0
                    
                    for csv_file in csv_files:
                        full_path = f"data/{csv_file}"
                        size = os.path.getsize(full_path)
                        logger.info(f"📊 {csv_file}: {size} bytes")
                        
                        if size > largest_size and size > 10000:
                            largest_csv = csv_file
                            largest_size = size
                    
                    if largest_csv:
                        logger.info(f"✅ Using largest CSV file: {largest_csv} ({largest_size} bytes)")
                        try:
                            # Rename to expected name
                            os.rename(f"data/{largest_csv}", csv_path)
                            logger.info("✅ CSV file renamed successfully!")
                            return True
                        except Exception as e:
                            logger.error(f"❌ Error renaming file: {e}")
                            # Try copying instead
                            try:
                                import shutil
                                shutil.copy2(f"data/{largest_csv}", csv_path)
                                logger.info("✅ CSV file copied successfully!")
                                return True
                            except Exception as copy_e:
                                logger.error(f"❌ Error copying file: {copy_e}")
                                return False
                else:
                    logger.error("❌ No CSV files found in data directory")
            
            logger.error("❌ CSV file was not downloaded")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during Selenium download: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Try to get more error details
        try:
            logger.error(f"Current URL: {driver.current_url}")
            logger.error(f"Page source length: {len(driver.page_source)}")
        except:
            pass
            
        return False
    finally:
        try:
            driver.quit()
            logger.info("✅ Chrome driver closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing Chrome driver: {e}")

if __name__ == "__main__":
    # Test the scraper
    df = update_data()
    if df is not None:
        print("Sample data:")
        print(df.head())
