import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

def download_csv_direct():
    """
    Alternative method to download CSV using requests
    This tries to get real data from the website without Selenium
    """
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        print("🌐 Attempting direct download from Boletín Concursal...")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # First, get the main page to establish session and get any required tokens
        url = "https://www.boletinconcursal.cl/boletin/procedimientos"
        print(f"📄 Fetching main page: {url}")
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        print(f"✅ Main page loaded successfully (status: {response.status_code})")
        
        # Parse the page to understand the structure
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the CSV download button and any associated forms or AJAX endpoints
        csv_button = soup.find('button', {'id': 'btnRegistroCsv'})
        if csv_button:
            print("🔍 Found CSV download button")
            
            # Look for any data attributes or onclick handlers
            onclick = csv_button.get('onclick', '')
            data_url = csv_button.get('data-url', '')
            
            print(f"Button onclick: {onclick}")
            print(f"Button data-url: {data_url}")
            
            # Try to find any forms that might be related
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '')
                if 'csv' in action.lower() or 'export' in action.lower():
                    print(f"Found potential CSV form: {action}")
        
        # Try common CSV export endpoints
        potential_csv_urls = [
            "https://www.boletinconcursal.cl/boletin/procedimientos/export/csv",
            "https://www.boletinconcursal.cl/boletin/export/csv",
            "https://www.boletinconcursal.cl/api/procedimientos/csv",
            "https://www.boletinconcursal.cl/procedimientos.csv",
        ]
        
        for csv_url in potential_csv_urls:
            try:
                print(f"🔄 Trying CSV endpoint: {csv_url}")
                csv_response = session.get(csv_url, timeout=30)
                
                if csv_response.status_code == 200:
                    content_type = csv_response.headers.get('content-type', '').lower()
                    if 'csv' in content_type or 'text' in content_type:
                        # Check if it looks like CSV data
                        content = csv_response.text[:1000]  # First 1000 chars
                        if ',' in content and '\n' in content:
                            print(f"✅ Found CSV data at {csv_url}")
                            
                            with open("data/boletin_concursal.csv", 'w', encoding='utf-8') as f:
                                f.write(csv_response.text)
                            
                            print("✅ CSV downloaded successfully using direct method")
                            return True
                        else:
                            print(f"❌ Response doesn't look like CSV data")
                    else:
                        print(f"❌ Wrong content type: {content_type}")
                else:
                    print(f"❌ HTTP {csv_response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error trying {csv_url}: {e}")
                continue
        
        # Try to make a POST request to simulate the button click
        try:
            print("🔄 Trying to simulate button click with POST request...")
            post_data = {
                'action': 'export_csv',
                'format': 'csv'
            }
            
            post_response = session.post(url, data=post_data, timeout=30)
            if post_response.status_code == 200:
                content_type = post_response.headers.get('content-type', '').lower()
                if 'csv' in content_type or 'application/octet-stream' in content_type:
                    with open("data/boletin_concursal.csv", 'w', encoding='utf-8') as f:
                        f.write(post_response.text)
                    print("✅ CSV downloaded via POST request")
                    return True
                    
        except Exception as e:
            print(f"❌ POST request failed: {e}")
        
        print("❌ All direct download methods failed")
        return False
        
    except Exception as e:
        print(f"❌ Error in fallback download: {str(e)}")
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