# Boletín Concursal Data Scraper

A Streamlit web application that automatically scrapes data from the [Boletín Concursal](https://www.boletinconcursal.cl/boletin/procedimientos) website and displays it in an interactive dashboard.

## Features

- 🔄 **Automated Data Updates**: Click a button to scrape the latest CSV data from Boletín Concursal
- 📊 **Interactive Dashboard**: View and filter the scraped data in a user-friendly interface
- 🔍 **Search & Filter**: Search through data and select specific columns to display
- 📈 **Summary Statistics**: Automatic calculation of statistics for numeric columns
- 💾 **Data Export**: Download filtered data as CSV files
- ☁️ **Cloud Ready**: Designed for deployment on Vercel

## Project Structure

```
automation-flow-app/
├── streamlit_app.py          # Main Streamlit application
├── src/
│   ├── scraper/
│   │   ├── main.py          # Primary scraper using Selenium
│   │   └── fallback.py      # Fallback scraper using requests
│   └── reports/             # Reports directory (if needed)
├── data/                    # Directory for downloaded CSV files
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel deployment configuration
└── README.md               # This file
```

## Installation & Setup

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd automation-flow-app
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   streamlit run streamlit_app.py
   ```

### Vercel Deployment

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy to Vercel**:
   ```bash
   vercel
   ```

   Follow the prompts to configure your deployment.

## How It Works

### Data Scraping Process

1. **Primary Method (Selenium)**:
   - Uses Chrome WebDriver to navigate to the Boletín Concursal website
   - Clicks the "Publicaciones Formato CSV" button (ID: `btnRegistroCsv`)
   - Downloads the CSV file to the `data/` directory

2. **Fallback Method (Requests)**:
   - If Selenium fails (common in cloud environments), uses HTTP requests
   - Attempts to find direct download links
   - Falls back to sample data for demonstration if needed

### Application Features

- **Home Page**: Clean interface with update button and data display
- **Progress Tracking**: Visual progress bar during data updates
- **Data Validation**: Automatic checking of downloaded files
- **Error Handling**: Graceful fallback mechanisms for robust operation

## Dependencies

- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **selenium**: Web browser automation
- **webdriver-manager**: Automatic Chrome driver management
- **requests**: HTTP library for fallback method
- **beautifulsoup4**: HTML parsing for fallback method

## Configuration

### Environment Variables (Optional)

You can set these environment variables for additional configuration:

- `CHROME_DRIVER_PATH`: Custom path to Chrome driver (if not using webdriver-manager)
- `DOWNLOAD_TIMEOUT`: Timeout for download operations (default: 10 seconds)

### Vercel Configuration

The `vercel.json` file is configured to:
- Use the Python runtime for `streamlit_app.py`
- Route all requests to the Streamlit application

## Usage

1. **Open the application** in your web browser
2. **Click "Update Data"** to scrape the latest data from Boletín Concursal
3. **View the data** in the interactive table below
4. **Use search and filters** to find specific information
5. **Download filtered data** using the download button

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**:
   - The app uses `webdriver-manager` to automatically download Chrome driver
   - In cloud environments, Selenium might not work; the app will fall back to the requests method

2. **Download Failures**:
   - If the website structure changes, the scraper might need updates
   - The app includes fallback mechanisms and sample data for testing

3. **Deployment Issues**:
   - Ensure all dependencies are listed in `requirements.txt`
   - Vercel has limitations on package sizes; some packages might not work

### Logs and Debugging

The application includes comprehensive logging:
- Progress updates during scraping
- Error messages for troubleshooting
- Success confirmations for completed operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Disclaimer

This tool is for educational and informational purposes. Please ensure compliance with the website's terms of service and robots.txt file when scraping data. # boletin_automation_rpa
