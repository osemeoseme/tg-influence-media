# Methodology: Analyzing Media Influence on Telegram Channels

## Research Question

**What percentage of news content in popular Telegram channels is sourced from traditional media outlets?**

This project investigates the influence of traditional Ukrainian media on popular Telegram news channels to demonstrate the continued value of professional journalism in the social media ecosystem.

## Approach

The analysis uses three complementary detection methods to identify when Telegram content originates from or references traditional media:

### 1. Direct Link Detection

**Goal**: Identify explicit citations of media sources through hyperlinks.

**Method**:
- Extract all URLs from Telegram messages (from both message text and link entities)
- Parse each URL to extract its domain
- Match domains against a curated list of traditional media domains
- Flag messages containing links to any traditional media outlet

**Advantages**:
- High precision - direct attribution
- Easy to verify
- Captures explicit citations

**Limitations**:
- Only catches explicitly cited sources
- Misses rephrased or uncredited content

**Implementation**: `src/analyzers/link_detector.py`

### 2. Media Mention Detection

**Goal**: Identify references to media sources mentioned in text.

**Method**:
- Create regex patterns for each media outlet (name and common variations)
- Search message text for case-insensitive matches
- Track which specific media outlets are mentioned
- Flag messages mentioning any traditional media outlet

**Advantages**:
- Catches citations without links (e.g., "according to Babel...")
- Simple and fast
- Language-agnostic pattern matching

**Limitations**:
- May miss abbreviated or informal references
- Can have false positives (media names used in different contexts)

**Implementation**: `src/analyzers/mention_detector.py`

### 3. Semantic Similarity Detection

**Goal**: Identify rephrased or uncredited content from media sources.

**Method**:
- Use multilingual sentence transformers to encode text into vector embeddings
- Model: `paraphrase-multilingual-MiniLM-L12-v2` (supports Ukrainian)
- Compute cosine similarity between Telegram messages and media articles
- Apply temporal filter (Telegram message must be after media article)
- Set similarity threshold (default: 0.75) to balance precision and recall
- Flag messages with similarity above threshold

**Advantages**:
- Detects rephrased content without attribution
- Captures the actual content influence, not just citations
- Language-aware semantic understanding

**Limitations**:
- Computationally expensive
- Requires sufficient text length (skips very short messages)
- May have false positives on similar news topics

**Implementation**: `src/analyzers/similarity_detector.py`

**Technical Details**:
```python
# Cosine similarity formula
similarity = dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))

# Temporal window
telegram_date > media_date
telegram_date - media_date <= 48 hours  # configurable
```

## Data Collection

### Telegram Data
- **Source**: 13 popular Ukrainian Telegram channels
- **Tool**: Telethon API
- **Data Points**:
  - Message ID, date, text
  - View count, forward count
  - URLs and entities
- **Time Range**: Configurable (default: last 3 months)

### Media Data
- **Source**: 17 traditional Ukrainian media outlets
- **Tools**:
  - RSS feed parsing (primary)
  - newspaper3k for article extraction
- **Data Points**:
  - Article URL, title, full text
  - Publish date, authors
- **Time Range**: Same as Telegram data

### Configuration
All data sources are configurable via JSON files:
- `config/telegram_channels.json`: Telegram channels to analyze
- `config/media_sources.json`: Media outlets to track

## Analysis Pipeline

### Stage 1: Data Collection
```
Telegram API → Raw Telegram messages (JSON)
RSS/Web Scraping → Raw media articles (JSON)
```

### Stage 2: Link Detection
```
For each Telegram message:
  Extract URLs → Parse domains → Match against media domains
  Result: has_media_link (boolean), media_urls (list)
```

### Stage 3: Mention Detection
```
For each Telegram message:
  Search text for media name patterns
  Result: has_media_mention (boolean), mentioned_media (list)
```

### Stage 4: Similarity Detection
```
For messages without links or mentions:
  Encode message → Compare with media embeddings → Filter by time
  Result: has_similar_content (boolean), similar_articles (list with scores)
```

### Stage 5: Aggregation
```
Combine all detection results → Calculate statistics → Generate reports
```

## Key Metrics

### Primary Metric
**Percentage Influenced**: What portion of Telegram content can be traced to traditional media?

```
influenced_percentage = (messages_with_media_influence / total_messages) × 100
```

Where `messages_with_media_influence` = messages detected by ANY of the three methods.

### Secondary Metrics

1. **Detection Method Breakdown**:
   - Link only: Messages with only direct links
   - Mention only: Messages with only media mentions
   - Similarity only: Messages with only semantic similarity
   - Multiple methods: Messages detected by 2+ methods

2. **Media Outlet Rankings**:
   - Which media outlets are most frequently referenced?
   - Which channels rely most on which sources?

3. **Temporal Patterns**:
   - How quickly do Telegram channels pick up media stories?
   - Are there time-of-day or day-of-week patterns?

## Validation & Quality Control

### Data Quality
- Filter out very short messages (< 50 characters for similarity)
- Verify URLs are valid and accessible
- Check date parsing for temporal analysis

### Analysis Quality
- Manual inspection of high-similarity matches
- Verify domain matching is accurate
- Review mention patterns for false positives

### Statistical Significance
- Report confidence intervals where applicable
- Provide sample sizes for all statistics
- Document data collection limitations

## Limitations & Considerations

### Coverage
- Limited to configured channels and media sources
- May miss content from unlisted sources
- RSS availability varies by media outlet

### Temporal Accuracy
- Media article publish dates may be approximate
- Telegram message dates are accurate but content may be scheduled
- Time window (48 hours) is configurable but arbitrary

### Semantic Similarity
- Threshold (0.75) balances precision and recall
- Model quality depends on Ukrainian language support
- Similar news topics may yield false positives

### Bias Considerations
- Channel selection may not represent all Telegram users
- Media selection focused on mainstream outlets
- Analysis doesn't evaluate content quality or accuracy

## Future Enhancements

1. **Expand Detection Methods**:
   - Image similarity for shared graphics
   - Named entity recognition (NER) for source attribution
   - Quote extraction and matching

2. **Deeper Analysis**:
   - Topic modeling to identify news themes
   - Sentiment analysis of rephrased content
   - Network analysis of information flow

3. **Automation**:
   - Real-time monitoring
   - Automated reporting
   - Alert system for significant patterns

4. **Validation**:
   - Manual annotation of sample for precision/recall
   - Inter-rater reliability testing
   - Cross-validation with other datasources

## References

- **Sentence Transformers**: https://www.sbert.net/
- **Telethon**: https://docs.telethon.dev/
- **newspaper3k**: https://newspaper.readthedocs.io/
- **Related Research**: See project description for academic papers

## Reproducibility

All code, configurations, and documentation are provided to ensure reproducibility:
- Environment captured in `requirements.txt`
- Data sources listed in configuration files
- Parameters configurable via `.env`
- Analysis pipeline documented in code comments

To reproduce:
1. Follow QUICKSTART.md for setup
2. Run `python main.py all`
3. Results will match given the same data collection time period
