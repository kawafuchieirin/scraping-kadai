# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web scraping project that analyzes train delay patterns for the Yamanote Line in Tokyo. The project scrapes delay certificate data from JR East's website and generates comprehensive visualizations and statistical analysis of delay patterns.

## Architecture

The project is structured into two main components:

### Core Scripts
- `src/yamanote_scraper.py`: Main scraping module using requests + BeautifulSoup4
  - `YamanoteDelayScraper` class handles data collection from JR East delay certificate pages
  - Extracts delay times, time slots, and date information
  - Includes rate limiting (1 second delays) to be respectful to the server
  
- `src/analyze_data.py`: Data analysis and visualization module using pandas + matplotlib/seaborn
  - `YamanoteDelayAnalyzer` class processes CSV data and generates multiple chart types
  - Creates heatmaps, trend graphs, and statistical summaries
  - Outputs analysis reports in Markdown format

### Data Flow
1. Scraper collects monthly delay data → CSV files in `data/`
2. Analyzer processes CSV → graphs in `output/` + analysis report
3. All outputs include Japanese text and proper date formatting

## Common Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### Data Collection
```bash
# Scrape previous month's data (default behavior)
python src/yamanote_scraper.py

# The script will automatically determine the previous month and collect data
```

### Data Analysis
```bash
# Analyze collected data (replace with actual CSV filename)
python src/analyze_data.py data/yamanote_delay_data_YYYYMMDD_HHMMSS.csv
```

### Project Structure
```
data/           # Generated CSV files from scraping
output/         # Generated graphs and analysis reports
src/            # Source code modules
```

## Key Dependencies

- **requests**: HTTP client for web scraping
- **beautifulsoup4**: HTML parsing and data extraction
- **pandas**: Data manipulation and analysis
- **matplotlib/seaborn**: Data visualization
- **lxml**: XML/HTML parser backend

## Development Notes

### Scraping Considerations
- The scraper includes 1-second delays between requests to avoid overwhelming the target server
- URL patterns and HTML structure may need adjustment based on actual JR East website structure
- Error handling is implemented for network timeouts and parsing failures

### Data Processing
- All dates are handled as pandas datetime objects for proper sorting and analysis
- Japanese weekday names are properly handled and displayed
- The analyzer supports multiple chart types and automatically saves outputs

### Localization
- The project is designed to work with Japanese text and date formats
- Font configuration is included for proper Japanese character display in matplotlib charts
- All output reports include Japanese headers and labels

## Extending the Project

### Adding New Analysis Types
Add new methods to `YamanoteDelayAnalyzer` class in `src/analyze_data.py`

### Supporting Other Train Lines
Extend `YamanoteDelayScraper` class to handle different URL patterns and HTML structures

### Output Formats
The visualization system can be extended to support additional chart types or export formats by adding methods to the analyzer class.