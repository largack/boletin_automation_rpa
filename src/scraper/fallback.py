import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging

# Set up logging
logger = logging.getLogger(__name__)

def download_csv_direct():
    """
    Alternative method to download CSV using requests
    This tries to get real data from the website without Selenium
    """
    logger.info("🌐 Starting direct download method...")
    
    try:
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
        
        logger.info("🌐 Attempting direct download from Boletín Concursal...")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        logger.info("🔧 HTTP session configured with browser headers")
        
        # First, get the main page to establish session and get any required tokens
        url = "https://www.boletinconcursal.cl/boletin/procedimientos"
        logger.info(f"📄 Fetching main page: {url}")
        
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            logger.info(f"✅ Main page loaded successfully (status: {response.status_code})")
            logger.info(f"📊 Response size: {len(response.content)} bytes")
            logger.info(f"📋 Content type: {response.headers.get('content-type', 'unknown')}")
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout while fetching main page")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ Connection error while fetching main page")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error while fetching main page: {e}")
            return False
        
        # Parse the page to understand the structure
        logger.info("🔍 Parsing page structure...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Log some basic page info
        title = soup.find('title')
        if title:
            logger.info(f"📄 Page title: {title.get_text().strip()}")
        
        # Look for the CSV download button and any associated forms or AJAX endpoints
        logger.info("🔍 Looking for CSV download button...")
        csv_button = soup.find('button', {'id': 'btnRegistroCsv'})
        if csv_button:
            logger.info("✅ Found CSV download button with ID 'btnRegistroCsv'")
            
            # Look for any data attributes or onclick handlers
            onclick = csv_button.get('onclick', '')
            data_url = csv_button.get('data-url', '')
            
            logger.info(f"🔧 Button onclick: {onclick}")
            logger.info(f"🔧 Button data-url: {data_url}")
            
            # Try to find any forms that might be related
            forms = soup.find_all('form')
            logger.info(f"📋 Found {len(forms)} forms on page")
            for i, form in enumerate(forms):
                action = form.get('action', '')
                method = form.get('method', 'GET')
                logger.info(f"  Form {i}: action='{action}', method='{method}'")
                if 'csv' in action.lower() or 'export' in action.lower():
                    logger.info(f"✅ Found potential CSV form: {action}")
        else:
            logger.warning("⚠️ CSV download button with ID 'btnRegistroCsv' not found")
            
            # Look for any buttons with CSV-related text
            all_buttons = soup.find_all('button')
            logger.info(f"🔍 Found {len(all_buttons)} buttons total, checking for CSV-related text...")
            for i, button in enumerate(all_buttons):
                text = button.get_text().strip().lower()
                if text and ('csv' in text or 'descargar' in text or 'exportar' in text):
                    logger.info(f"✅ Found potential CSV button {i}: '{text}'")
        
        # Try common CSV export endpoints
        potential_csv_urls = [
            "https://www.boletinconcursal.cl/boletin/procedimientos/export/csv",
            "https://www.boletinconcursal.cl/boletin/export/csv",
            "https://www.boletinconcursal.cl/api/procedimientos/csv",
            "https://www.boletinconcursal.cl/procedimientos.csv",
            "https://www.boletinconcursal.cl/boletin/procedimientos.csv",
            "https://www.boletinconcursal.cl/export/procedimientos.csv",
        ]
        
        logger.info(f"🔄 Trying {len(potential_csv_urls)} potential CSV endpoints...")
        
        for i, csv_url in enumerate(potential_csv_urls):
            try:
                logger.info(f"🔄 [{i+1}/{len(potential_csv_urls)}] Trying: {csv_url}")
                csv_response = session.get(csv_url, timeout=30)
                
                logger.info(f"📊 Response status: {csv_response.status_code}")
                logger.info(f"📊 Response size: {len(csv_response.content)} bytes")
                
                if csv_response.status_code == 200:
                    content_type = csv_response.headers.get('content-type', '').lower()
                    logger.info(f"📋 Content type: {content_type}")
                    
                    if 'csv' in content_type or 'text' in content_type or 'application/octet-stream' in content_type:
                        # Check if it looks like CSV data
                        content = csv_response.text[:1000]  # First 1000 chars
                        logger.info(f"📄 Content preview: {repr(content[:200])}")
                        
                        # More strict CSV validation
                        is_valid_csv = (
                            ',' in content and 
                            '\n' in content and 
                            len(content.strip()) > 50 and
                            not content.strip().startswith('<!') and  # Not HTML
                            not content.strip().startswith('<html') and  # Not HTML
                            not '<html' in content.lower() and  # Not HTML anywhere
                            not '<!doctype' in content.lower() and  # Not HTML doctype
                            len(csv_response.content) > 10000  # Must be substantial size (>10KB)
                        )
                        
                        if is_valid_csv:
                            logger.info(f"✅ Found valid CSV data at {csv_url}")
                            
                            with open("data/boletin_concursal.csv", 'w', encoding='utf-8') as f:
                                f.write(csv_response.text)
                            
                            # Verify file was written
                            if os.path.exists("data/boletin_concursal.csv"):
                                size = os.path.getsize("data/boletin_concursal.csv")
                                logger.info(f"✅ CSV file saved successfully! Size: {size} bytes")
                                return True
                            else:
                                logger.error("❌ File was not saved properly")
                        else:
                            logger.warning(f"⚠️ Response doesn't look like valid CSV data - appears to be HTML or too small")
                            logger.warning(f"   Size: {len(csv_response.content)} bytes, starts with: {repr(content[:50])}")
                    else:
                        logger.warning(f"⚠️ Wrong content type: {content_type}")
                elif csv_response.status_code == 404:
                    logger.info(f"📄 Endpoint not found (404)")
                elif csv_response.status_code == 403:
                    logger.warning(f"🚫 Access forbidden (403)")
                elif csv_response.status_code == 500:
                    logger.error(f"💥 Server error (500)")
                else:
                    logger.warning(f"❓ Unexpected status: {csv_response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout for {csv_url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error for {csv_url}")
            except Exception as e:
                logger.error(f"❌ Error trying {csv_url}: {e}")
                continue
        
        # Try to make a POST request to simulate the button click
        logger.info("🔄 Trying to simulate button click with POST request...")
        try:
            # First, let's analyze the form more carefully
            forms = soup.find_all('form')
            main_form = None
            for form in forms:
                action = form.get('action', '')
                if '/boletin/procedimientos' in action:
                    main_form = form
                    logger.info(f"✅ Found main form with action: {action}")
                    break
            
            if main_form:
                # Extract all form inputs to build proper POST data
                form_data = {}
                
                # Get all input fields
                inputs = main_form.find_all(['input', 'select', 'textarea'])
                for input_field in inputs:
                    name = input_field.get('name')
                    if name:
                        input_type = input_field.get('type', 'text').lower()
                        value = input_field.get('value', '')
                        
                        if input_type == 'hidden':
                            form_data[name] = value
                            logger.info(f"🔧 Hidden field: {name} = {value}")
                        elif input_type == 'submit':
                            # Don't include submit buttons unless specifically needed
                            pass
                        else:
                            # For other fields, use default values
                            form_data[name] = value
                            logger.info(f"🔧 Form field: {name} = {value}")
                
                # Try different approaches to trigger CSV download
                csv_download_attempts = [
                    # Attempt 1: Add CSV export parameter
                    {**form_data, 'export': 'csv', 'format': 'csv'},
                    # Attempt 2: Simulate button click
                    {**form_data, 'btnRegistroCsv': 'Exportar CSV'},
                    # Attempt 3: Add download parameter
                    {**form_data, 'download': 'csv', 'action': 'export'},
                    # Attempt 4: Try with different export formats
                    {**form_data, 'exportFormat': 'csv'},
                    # Attempt 5: Just the form data as-is
                    form_data,
                ]
                
                for i, post_data in enumerate(csv_download_attempts):
                    logger.info(f"🔄 CSV download attempt {i+1}: {post_data}")
                    
                    try:
                        # Use the form's action URL
                        form_action = main_form.get('action', '/boletin/procedimientos')
                        if not form_action.startswith('http'):
                            post_url = f"https://www.boletinconcursal.cl{form_action}"
                        else:
                            post_url = form_action
                        
                        logger.info(f"📤 Posting to: {post_url}")
                        
                        # Add proper headers for form submission
                        headers = {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Referer': url,
                            'Origin': 'https://www.boletinconcursal.cl',
                        }
                        
                        post_response = session.post(post_url, data=post_data, headers=headers, timeout=30)
                        logger.info(f"📊 POST response status: {post_response.status_code}")
                        logger.info(f"📊 POST response size: {len(post_response.content)} bytes")
                        
                        if post_response.status_code == 200:
                            content_type = post_response.headers.get('content-type', '').lower()
                            logger.info(f"📋 POST content type: {content_type}")
                            
                            # Check if this might be a CSV download
                            if ('csv' in content_type or 
                                'application/octet-stream' in content_type or
                                'text/plain' in content_type):
                                
                                content = post_response.text[:500]
                                
                                # Apply same strict validation for POST responses
                                is_valid_csv = (
                                    ',' in content and 
                                    '\n' in content and
                                    not content.strip().startswith('<!') and  # Not HTML
                                    not content.strip().startswith('<html') and  # Not HTML
                                    not '<html' in content.lower() and  # Not HTML anywhere
                                    not '<!doctype' in content.lower() and  # Not HTML doctype
                                    len(post_response.content) > 10000  # Must be substantial size (>10KB)
                                )
                                
                                if is_valid_csv:
                                    logger.info("✅ POST request returned valid CSV data!")
                                    with open("data/boletin_concursal.csv", 'w', encoding='utf-8') as f:
                                        f.write(post_response.text)
                                    
                                    if os.path.exists("data/boletin_concursal.csv"):
                                        size = os.path.getsize("data/boletin_concursal.csv")
                                        logger.info(f"✅ CSV downloaded via POST! Size: {size} bytes")
                                        return True
                                else:
                                    logger.warning(f"⚠️ POST response appears to be HTML, not CSV data")
                                    logger.warning(f"   Size: {len(post_response.content)} bytes, starts with: {repr(content[:50])}")
                            else:
                                logger.info(f"📄 Response content type doesn't indicate CSV: {content_type}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error in POST attempt {i+1}: {e}")
                        continue
            
            else:
                logger.warning("⚠️ Could not find main form for POST simulation")
                
                # Fallback to simple POST attempts
                post_data_variants = [
                    {'action': 'export_csv', 'format': 'csv'},
                    {'export': 'csv'},
                    {'download': 'csv'},
                    {'btnRegistroCsv': 'true'},
                    {'type': 'csv'},
                ]
                
                for i, post_data in enumerate(post_data_variants):
                    logger.info(f"🔄 Simple POST attempt {i+1}: {post_data}")
                    post_response = session.post(url, data=post_data, timeout=30)
                    logger.info(f"📊 POST response status: {post_response.status_code}")
                    
                    if post_response.status_code == 200:
                        content_type = post_response.headers.get('content-type', '').lower()
                        logger.info(f"📋 POST content type: {content_type}")
                        
                        if 'csv' in content_type or 'application/octet-stream' in content_type:
                            content = post_response.text[:500]
                            
                            # Apply same strict validation for POST responses
                            is_valid_csv = (
                                ',' in content and 
                                '\n' in content and
                                not content.strip().startswith('<!') and  # Not HTML
                                not content.strip().startswith('<html') and  # Not HTML
                                not '<html' in content.lower() and  # Not HTML anywhere
                                not '<!doctype' in content.lower() and  # Not HTML doctype
                                len(post_response.content) > 10000  # Must be substantial size (>10KB)
                            )
                            
                            if is_valid_csv:
                                logger.info("✅ POST request returned CSV data!")
                                with open("data/boletin_concursal.csv", 'w', encoding='utf-8') as f:
                                    f.write(post_response.text)
                                
                                if os.path.exists("data/boletin_concursal.csv"):
                                    size = os.path.getsize("data/boletin_concursal.csv")
                                    logger.info(f"✅ CSV downloaded via POST! Size: {size} bytes")
                                    return True
                            else:
                                logger.warning(f"⚠️ POST response appears to be HTML, not CSV data")
                                logger.warning(f"   Size: {len(post_response.content)} bytes, starts with: {repr(content[:50])}")
                     
        except Exception as e:
            logger.error(f"❌ POST request failed: {e}")
        
        logger.error("❌ All direct download methods failed")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error in fallback download: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def get_sample_data():
    """
    Create sample data for testing when real data is not available
    This matches the expected format from the real Boletín Concursal data
    """
    print("📝 Creating sample data with realistic format...")
    
    sample_data = {
        'Rol': ['C-123-2025', 'C-456-2025', 'C-789-2025', 'C-101-2025', 'C-202-2025'],
        'Procedimiento Concursal': [
            'Renegociación - Persona Deudora',
            'Liquidación voluntaria simplificada - Persona Deudora', 
            'Renegociación - Persona Deudora',
            'Liquidación voluntaria simplificada - Persona Deudora',
            'Renegociación - Persona Deudora'
        ],
        'Deudor': [
            'JUAN PEREZ GONZALEZ',
            'MARIA RODRIGUEZ SILVA', 
            'CARLOS MARTINEZ LOPEZ',
            'ANA FERNANDEZ TORRES',
            'LUIS SANCHEZ MORALES'
        ],
        'RUT': ['12345678-9', '87654321-0', '11111111-1', '22222222-2', '33333333-3'],
        'Veedor Liquidador Titular': [
            'PEDRO GONZALEZ RUIZ',
            'CARMEN LOPEZ HERRERA',
            'MIGUEL TORRES SILVA',
            'SOFIA MORALES CASTRO',
            'DIEGO HERRERA VEGA'
        ],
        'Nombre Publicación': [
            'Resolución de admisibilidad',
            'Resolución de Liquidación',
            'Resolución de admisibilidad', 
            'Resolución de Liquidación',
            'Resolución de admisibilidad'
        ],
        'Tribunal': [
            '1º Juzgado de Letras de Santiago',
            '2º Juzgado de Letras de Valparaíso',
            '3º Juzgado de Letras de Concepción',
            '1º Juzgado de Letras de La Serena',
            '2º Juzgado de Letras de Temuco'
        ],
        'Fecha Publicación': [
            '15/01/2025',
            '20/01/2025', 
            '25/01/2025',
            '30/01/2025',
            '05/02/2025'
        ]
    }
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        df = pd.DataFrame(sample_data)
        csv_path = "data/boletin_concursal.csv"
        df.to_csv(csv_path, index=False)
        
        print(f"✅ Sample data created successfully at {csv_path}")
        print(f"📊 Created {len(df)} sample records")
        print(f"📋 Columns: {list(df.columns)}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

if __name__ == "__main__":
    # Test the fallback method
    if not download_csv_direct():
        print("Fallback method failed, creating sample data")
        get_sample_data() 