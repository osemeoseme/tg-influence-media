# Quick Start Guide

## Prerequisites
- Python 3.8 or higher
- Telegram account
- Telegram API credentials (get from https://my.telegram.org/apps)

## Installation

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy the environment template and fill in your credentials:
```bash
cp .env.template .env
```

Edit `.env` and add your Telegram API credentials:
```
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+380xxxxxxxxx
```

To get Telegram API credentials:
1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy the API ID and API Hash

## Usage

### Option 1: Run Everything at Once
```bash
python main.py all
```
This will:
1. Scrape data from Telegram channels and media sources
2. Analyze the data using three detection methods
3. Generate reports and visualizations

### Option 2: Run Step by Step

#### Step 1: Scrape Data
```bash
python main.py scrape
```
This will collect messages from Telegram channels and articles from media sources for the last 3 months.

**Note**: First time running Telegram scraper, you'll need to authenticate with your phone number.

#### Step 2: Analyze Data
```bash
python main.py analyze
```
This will analyze the scraped data using three methods:
- **Direct links**: Detect links to media sources in Telegram messages
- **Media mentions**: Detect mentions of media names in messages
- **Semantic similarity**: Find rephrased content using NLP

#### Step 3: Generate Report
```bash
python main.py report
```
This will generate:
- Text summary report (`data/results/report.txt`)
- Visualizations (`data/results/analysis_visualizations.png`)
- CSV files for further analysis

## Output Files

All output files are saved in the `data/` directory:

### Raw Data (`data/raw/`)
- `telegram_*.json`: Individual channel messages
- `telegram_all_messages.json`: All Telegram messages combined
- `media_*.json`: Individual media source articles
- `media_all_articles.json`: All media articles combined

### Results (`data/results/`)
- `analysis_*.json`: Individual channel analysis results
- `analysis_all_channels.json`: Combined analysis results
- `report.txt`: Text summary report
- `analysis_visualizations.png`: Charts and graphs
- `summary.csv`: Summary statistics per channel
- `detailed_messages.csv`: Detailed message-level data

## Understanding the Results

The analysis provides three key metrics:

1. **Percentage Influenced**: What percentage of Telegram messages are influenced by traditional media?

2. **Detection Method Breakdown**: How was the influence detected?
   - Direct links to media articles
   - Mentions of media names
   - Semantic similarity (rephrased content)

3. **Per-Channel Statistics**: Which channels rely more heavily on traditional media?

## Customization

### Adjust Time Range
Edit `.env`:
```
DATA_MONTHS_BACK=6  # Collect data from last 6 months instead of 3
```

### Adjust Similarity Threshold
Edit `.env`:
```
SIMILARITY_THRESHOLD=0.80  # Require 80% similarity instead of 75%
```

### Add More Channels or Media Sources
Edit the configuration files:
- `config/telegram_channels.json`: Add more Telegram channels
- `config/media_sources.json`: Add more media sources

## Troubleshooting

### Telegram Authentication Issues
- Make sure your phone number includes country code (e.g., +380)
- Check that API ID and API Hash are correct
- You'll receive a code via Telegram, enter it when prompted

### Memory Issues with Large Datasets
- Reduce `MAX_MESSAGES_PER_CHANNEL` in `.env`
- Process channels individually instead of all at once

### Slow Similarity Analysis
- The semantic similarity detection uses deep learning models and can be slow
- Consider reducing the dataset size or using a GPU
- You can skip similarity analysis by commenting out that step in the code

## Next Steps

1. Review the generated reports and visualizations
2. Examine the detailed CSV files for specific examples
3. Adjust parameters and re-run analysis
4. Use Jupyter notebooks for custom analysis (coming soon)

## Support

For issues or questions:
- Check the main README.md for detailed documentation
- Review the code comments for implementation details
- Contact the project supervisor for guidance
