import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

def download_csv_direct():
    """
    Alternative method to download CSV using requests
    This is a fallback if Selenium doesn't work in the deployment environment
    """
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # First, get the main page to establish session
        url = "https://www.boletinconcursal.cl/boletin/procedimientos"
        print("Fetching main page...")
        
        response = session.get(url)
        response.raise_for_status()
        
        # Parse the page to find the CSV download link
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for forms or direct links that might handle CSV download
        # This is a simplified approach - the actual implementation might need
        # to handle AJAX requests or form submissions
        
        # Try to find any CSV download links
        csv_links = []
        for link in soup.find_all(['a', 'button'], {'id': 'btnRegistroCsv'}):
            if link.get('href'):
                csv_links.append(link['href'])
        
        # If we found direct links, try to download
        if csv_links:
            for csv_url in csv_links:
                if not csv_url.startswith('http'):
                    csv_url = f"https://www.boletinconcursal.cl{csv_url}"
                
                print(f"Trying to download from: {csv_url}")
                csv_response = session.get(csv_url)
                
                if csv_response.status_code == 200:
                    with open("data/boletin_concursal.csv", 'wb') as f:
                        f.write(csv_response.content)
                    print("CSV downloaded successfully using direct method")
                    return True
        
        # If direct method doesn't work, try to simulate the button click
        # This would require analyzing the JavaScript and making the appropriate POST request
        print("Direct download not available, would need to analyze JavaScript")
        return False
        
    except Exception as e:
        print(f"Error in fallback download: {str(e)}")
        return False

def get_sample_data():
    """
    Create sample data for testing when real data is not available
    """
    sample_data = {
        'RUC': ['12345678-9', '87654321-0', '11111111-1'],
        'Razón Social': ['Empresa A S.A.', 'Empresa B Ltda.', 'Empresa C S.A.'],
        'Tipo Procedimiento': ['Reorganización', 'Liquidación', 'Reorganización'],
        'Estado': ['En Curso', 'Finalizado', 'En Curso'],
        'Fecha Inicio': ['2024-01-15', '2024-02-20', '2024-03-10']
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv("data/boletin_concursal.csv", index=False)
    print("Sample data created for testing")
    return True

if __name__ == "__main__":
    # Test the fallback method
    if not download_csv_direct():
        print("Fallback method failed, creating sample data")
        get_sample_data() 