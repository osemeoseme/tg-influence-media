# Feature Recreation Guide - Telegram Influence Media Analysis

## Overview
This document contains a complete specification for recreating all new features added to the Telegram Influence Media analysis project. Use this to recreate the features from scratch.

---

## Table of Contents
1. [New Files to Create](#new-files-to-create)
2. [Files to Modify](#files-to-modify)
3. [Configuration Changes](#configuration-changes)
4. [Feature Specifications](#feature-specifications)
5. [Integration Points](#integration-points)
6. [Testing and Validation](#testing-and-validation)

---

## New Files to Create

### 1. Content Type Detector
**File**: `src/analyzers/content_type_detector.py`

**Purpose**: Detect different types of content in Telegram messages (news, memes, government sources, official channels, social media).

**Key Components**:
- Government domain detection (gov.ua, president.gov.ua, kmu.gov.ua, mil.gov.ua, mvs.gov.ua, mfa.gov.ua, dpsu.gov.ua, ssu.gov.ua)
- Official channel keyword patterns (голова.*ОВА, ОВА, ДСНС, ЗСУ, Генштаб, Міноборони, МВС, СБУ, ДПСУ, офіційн, прес-служб)
- Social media domain detection (twitter.com, x.com, facebook.com, instagram.com, youtube.com)
- Telegram channel mention detection (@channel, t.me/)

**Methods**:
1. `extract_urls(text: str) -> List[str]` - Extract all URLs from text using regex
2. `is_gov_url(url: str) -> bool` - Check if URL is from government source
3. `detect_telegram_channel_mention(text: str) -> bool` - Detect @channel or t.me/ mentions
4. `detect_content_type(message: Dict) -> Dict` - Main detection method returning:
   - `content_types`: List of detected types
   - `has_gov_source`: Boolean
   - `gov_urls`: List of government URLs
   - `has_official_channel`: Boolean
   - `has_meme_content`: Boolean
   - `has_social_media`: Boolean
   - `social_urls`: List of social media URLs
   - `has_tg_channel_mention`: Boolean
5. `analyze_messages(messages: List[Dict]) -> List[Dict]` - Batch process messages
6. `get_statistics(analyzed_messages: List[Dict]) -> Dict` - Calculate statistics with:
   - `total_messages`
   - `content_type_counts` (dict)
   - `content_type_percentages` (dict)

**Logic**: If no specific type detected, default to "news".

---

### 2. Reference Detector
**File**: `src/analyzers/reference_detector.py`

**Purpose**: Detect what Telegram posts reference when they don't reference traditional media.

**Key Components**:
- Social media domain mapping (twitter.com, x.com, facebook.com, instagram.com, youtube.com, tiktok.com)
- Official domain mapping (gov.ua, president.gov.ua, kmu.gov.ua, mil.gov.ua)
- Telegram channel extraction (@username and t.me/username patterns)
- URL categorization by domain

**Methods**:
1. `extract_urls(text: str) -> List[str]` - Extract URLs from text
2. `extract_telegram_channels(text: str) -> List[str]` - Extract @mentions and t.me/ links
3. `categorize_url(url: str) -> str` - Categorize URL by domain, return category name or "Other (domain)"
4. `detect_references(message: Dict, has_media_reference: bool) -> Dict` - Return:
   - `has_non_media_reference`: Boolean
   - `reference_categories`: Dict mapping category to count
   - `telegram_channels`: List of channel names
   - `urls_by_category`: Dict mapping category to URL list
5. `analyze_messages(messages: List[Dict]) -> List[Dict]` - Batch process, check if message has media reference first
6. `get_statistics(analyzed_messages: List[Dict]) -> Dict` - Calculate:
   - `total_messages`
   - `messages_with_non_media_references`
   - `percentage_with_non_media_references`
   - `reference_category_counts`
   - `unique_telegram_channels_mentioned`
   - `telegram_channels_list` (sorted)
   - `messages_without_media`
   - `without_media_but_with_other_refs`
   - `without_media_percentage_with_refs`

---

### 3. Bidirectional Influence Analyzer
**File**: `src/analyzers/bidirectional_influence.py`

**Purpose**: Analyze content reproduction in both directions - Media → Telegram and Telegram → Media.

**Key Components**:
- Time window for content reproduction analysis (default 48 hours)
- Media domain to name mapping (suspilne.media → "Суспільне", espreso.tv → "Еспресо", etc.)
- Content reproduction tracking in both directions

**Methods**:
1. `analyze_media_to_telegram(telegram_messages, media_articles) -> Dict` - Returns:
   - `media_influence_ranking`: Sorted list of (media_name, stats) tuples
   - `total_media_sources`: Count
   - Stats include: mentions, links, similarity_matches, total_references, influenced_channels_count, influenced_channels list

2. `analyze_telegram_to_media(telegram_messages, media_articles) -> Dict` - Returns:
   - `channel_influence_ranking`: Sorted list of (channel_name, stats) tuples
   - `total_channels_influencing_media`: Count
   - Stats include: cited_in_media, unique_media_influenced, media_list

3. `compare_influence_directions(media_to_tg, tg_to_media, total_tg_messages) -> Dict` - Returns:
   - `media_to_telegram`: total_references, average_references_per_message, top_influencers (top 5)
   - `telegram_to_media`: total_citations, channels_cited, top_influencers (top 5)
   - `dominant_influence_direction`: String ("Media -> Telegram" or "Telegram -> Media")
   - `influence_ratio`: media_to_telegram_strength, telegram_to_media_strength

4. `generate_full_analysis(telegram_messages, media_articles) -> Dict` - Main method combining all analyses

**Domain Mapping** (in `_extract_media_from_url`):
```python
{
    "suspilne.media": "Суспільне",
    "espreso.tv": "Еспресо",
    "babel.ua": "Бабель",
    "pravda.com.ua": "Українська правда",
    "radiosvoboda.org": "Радіо Свобода",
    "hromadske.ua": "hromadske",
    "zn.ua": "ZN.UA",
    "texty.org.ua": "Тексти",
    "lb.ua": "LB.ua",
    "ukrinform.ua": "Укрінформ",
    "graty.me": "Ґрати",
    "tyzhden.ua": "Український тиждень",
    "rubryka.com": "Рубрика",
    "slovoidilo.ua": "Слово і Діло",
    "novynarnia.com": "Новинарня",
    "frontliner.ua": "Frontliner"
}
```

---

### 4. Interactive Visualizer
**File**: `src/processors/interactive_visualizations.py`

**Purpose**: Create interactive Plotly visualizations for content reproduction analysis.

**Dependencies**: `plotly`, `networkx`

**Key Components**:
- Color scheme: media (blue #1f77b4), telegram (orange #ff7f0e), link (green #2ca02c), mention (red #d62728), similarity (purple #9467bd)
- Output directory: `RESULTS_DIR / "interactive"`

**Methods**:
1. `create_influence_network(all_results, bidirectional_analysis) -> go.Figure`
   - Creates directed graph using NetworkX
   - Media nodes as squares (blue), Telegram as circles (orange)
   - Node size based on influence strength
   - Force-directed layout using spring_layout
   - Interactive hover with details
   - Saves to: `influence_network.html`

2. `create_media_influence_ranking(all_results) -> go.Figure`
   - Horizontal bar chart of media mentions
   - Color scale based on mention count
   - Sorted by total mentions
   - Dynamic height based on number of media sources
   - Saves to: `media_ranking.html`

3. `create_channel_comparison(all_results) -> go.Figure`
   - Side-by-side subplots
   - Left: Total messages bar chart
   - Right: Content reproduction percentage with color scale
   - Saves to: `channel_comparison.html`

4. `create_content_type_distribution(all_results) -> go.Figure`
   - Pie chart with hole (donut chart, hole=0.3)
   - Shows distribution of content types
   - Interactive hover with count and percentage
   - Saves to: `content_types.html`

5. `save_all_visualizations(all_results, bidirectional_analysis)` - Generate and save all four visualizations

---

## Files to Modify

### 1. Enhanced Mention Detector
**File**: `src/analyzers/mention_detector.py`

**Changes**: Enhance the `_create_patterns()` method for better name matching.

**Modifications**:
- Add case-insensitive pattern matching using `re.IGNORECASE`
- Support partial name matching (e.g., "Труха" matches "Труха Україна")
- Word-level matching for multi-word media names
- Create regex patterns that handle variants: `re.escape(name)` with word boundaries

**Pattern Logic**:
```python
# For each media name, create patterns like:
patterns = []
for name in media_names:
    # Exact match (case-insensitive)
    patterns.append(re.compile(rf'\b{re.escape(name)}\b', re.IGNORECASE))
    # For compound names, also match first part
    if ' ' in name:
        first_part = name.split()[0]
        patterns.append(re.compile(rf'\b{re.escape(first_part)}\b', re.IGNORECASE))
```

---

### 2. Combined Analyzer Integration
**File**: `src/analyzers/combined_analyzer.py`

**Changes**: Integrate new analyzers into the pipeline.

**Additions**:
1. Import new analyzers:
```python
from src.analyzers.content_type_detector import ContentTypeDetector
from src.analyzers.reference_detector import ReferenceDetector
```

2. Initialize in `__init__`:
```python
self.content_type_detector = ContentTypeDetector()
self.reference_detector = ReferenceDetector()
```

3. Add Step 4 in `analyze_channel` after similarity detection:
```python
# Step 4: Detect content types
print("\n4. Detecting content types (news, memes, official sources)...")
messages_with_content_types = self.content_type_detector.analyze_messages(messages_with_mentions)
content_type_stats = self.content_type_detector.get_statistics(messages_with_content_types)
print(f"   Content type distribution:")
for ct, pct in content_type_stats['content_type_percentages'].items():
    if pct > 0:
        print(f"     - {ct}: {pct:.1f}%")
```

4. Add Step 5 for reference detection:
```python
# Step 5: Detect non-media references
print("\n5. Detecting non-media references...")
messages_with_references = self.reference_detector.analyze_messages(messages_with_content_types)
reference_stats = self.reference_detector.get_statistics(messages_with_references)
print(f"   Found {reference_stats['messages_with_non_media_references']} messages with non-media references")
if reference_stats['unique_telegram_channels_mentioned'] > 0:
    print(f"   Mentioned {reference_stats['unique_telegram_channels_mentioned']} unique Telegram channels")
```

5. Update `_combine_results` call to use `messages_with_references`

6. Update `_calculate_overall_stats` signature:
```python
def _calculate_overall_stats(
    self, all_messages, link_stats, mention_stats, similarity_stats,
    content_type_stats=None, reference_stats=None
) -> Dict:
```

7. Add stats to return dictionary:
```python
# Add content type stats if available
if content_type_stats:
    stats["content_types"] = content_type_stats

# Add reference stats if available
if reference_stats:
    stats["references"] = reference_stats

return stats
```

---

### 3. Main Application Updates
**File**: `main.py`

**Changes**: Add bidirectional analysis and interactive visualizations.

**Additions**:
1. Import new components:
```python
from src.analyzers.bidirectional_influence import BidirectionalInfluenceAnalyzer
from src.processors.interactive_visualizations import InteractiveVisualizer
```

2. In `analyze_data()` function, add channel name to messages:
```python
# Add channel name to each message for later analysis
for msg in messages:
    msg['channel_name'] = name
```

3. After analyzing all channels, add bidirectional analysis:
```python
# Perform bidirectional influence analysis
print("\n" + "=" * 80)
print("BIDIRECTIONAL INFLUENCE ANALYSIS")
print("=" * 80)

# Collect all analyzed messages
all_analyzed_messages = []
for results in all_results.values():
    all_analyzed_messages.extend(results['messages'])

bidirectional_analyzer = BidirectionalInfluenceAnalyzer()
bidirectional_results = bidirectional_analyzer.generate_full_analysis(
    all_analyzed_messages, media_articles
)

# Save bidirectional analysis results
bidirectional_file = RESULTS_DIR / "bidirectional_influence.json"
with open(bidirectional_file, "w", encoding="utf-8") as f:
    json.dump(bidirectional_results, f, ensure_ascii=False, indent=2, default=str)
print(f"\nBidirectional analysis saved to: {bidirectional_file}")
```

4. Update combined results save structure:
```python
# Save combined results with bidirectional data
combined_data = {
    "channel_results": all_results,
    "bidirectional_influence": bidirectional_results
}
combined_file = RESULTS_DIR / "analysis_all_channels.json"
with open(combined_file, "w", encoding="utf-8") as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=2, default=str)
```

5. Return bidirectional results:
```python
return all_results, bidirectional_results
```

6. In `generate_report()` function, handle new data format:
```python
with open(results_file, "r", encoding="utf-8") as f:
    combined_data = json.load(f)

# Handle both old and new format
if "channel_results" in combined_data:
    all_results = combined_data["channel_results"]
    bidirectional_results = combined_data.get("bidirectional_influence")
else:
    all_results = combined_data
    bidirectional_results = None
```

7. Add interactive visualization generation:
```python
# Generate interactive visualizations
print("\n" + "=" * 80)
print("INTERACTIVE VISUALIZATIONS")
print("=" * 80)

visualizer = InteractiveVisualizer()
visualizer.save_all_visualizations(all_results, bidirectional_results)
```

8. Update `all` command to capture return values:
```python
elif args.command == "all":
    scrape_data()
    all_results, bidirectional_results = analyze_data()
    generate_report()
```

---

### 4. Report Generator Enhancement
**File**: `src/processors/report_generator.py`

**Changes**: Add content type and reference statistics to text reports.

**Modifications** (approximately 20 lines):
- In the report generation, add section for content types
- Add section for non-media references
- Display content type distribution percentages
- Show reference category breakdown
- Handle gracefully if new fields are missing (backward compatibility)

**Example additions to report**:
```python
# Content Type Distribution
if 'content_types' in stats:
    report.append("\n## Content Type Distribution")
    for ct, pct in stats['content_types']['content_type_percentages'].items():
        count = stats['content_types']['content_type_counts'][ct]
        report.append(f"  - {ct}: {count} ({pct:.1f}%)")

# Non-Media References
if 'references' in stats:
    ref_stats = stats['references']
    report.append("\n## Non-Media References")
    report.append(f"Messages with non-media references: {ref_stats['messages_with_non_media_references']}")
    report.append(f"Unique Telegram channels mentioned: {ref_stats['unique_telegram_channels_mentioned']}")
```

---

### 5. Configuration Updates
**File**: `src/utils/config.py`

**Changes**: Add date configuration support.

**Additions**:
1. Add new config variable:
```python
START_DATE_STR = os.getenv("START_DATE", "")  # Format: YYYY-MM-DD
```

2. Add helper function:
```python
def get_start_date():
    """
    Get the start date for data collection.

    Returns:
        datetime: Start date (timezone-aware UTC)
    """
    from datetime import datetime, timedelta, timezone

    # If START_DATE is set, use it
    if START_DATE_STR:
        try:
            # Parse the date string and make it timezone-aware (UTC, start of day)
            start_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
            return start_date.replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Warning: Invalid START_DATE format '{START_DATE_STR}', using DATA_MONTHS_BACK instead")

    # Otherwise, calculate from months back
    return datetime.now(timezone.utc) - timedelta(days=30 * DATA_MONTHS_BACK)
```

---

### 8. Dependencies
**File**: `requirements.txt`

**Changes**: Add networkx for network graph visualization.

**Add**:
```
networkx>=3.0
```

---

## Feature Specifications

### Feature 1: Case-Insensitive Media Name Matching
**Requirement**: Detect variations like "Труха", "труха", "Труха Україна" as the same source.

**Implementation**:
- Use `re.IGNORECASE` flag in regex patterns
- Create patterns with word boundaries `\b`
- For multi-word names, also match first significant word
- Example: "Українська правда" matches "Українська", "правда", "УКРАЇНСЬКА ПРАВДА"

**Test Cases**:
- "Труха" → should match "труха україна", "ТРУХА"
- "Українська правда" → should match "Українська Правда", "УКРАЇНСЬКА ПРАВДА"

---

### Feature 2: Content Type Detection
**Categories**:
1. **news** (default) - Traditional news content
2. **government_source** - Links to gov.ua domains
3. **official_channel** - Mentions of official Telegram channels (OVA heads, ministries)
5. **social_media** - Links to Twitter/X, Facebook, Instagram, YouTube, TikTok
6. **telegram_channel** - Mentions other Telegram channels

**Detection Logic**:
- A message can have multiple content types
- Check in order: government, official, meme, social, telegram
- Default to "news" if no specific type detected

**Output Format**:
```json
{
  "content_type_detection": {
    "content_types": ["government_source", "news"],
    "has_gov_source": true,
    "gov_urls": ["https://president.gov.ua/..."],
    "has_official_channel": false,
    "has_meme_content": false,
    "has_social_media": false,
    "social_urls": [],
    "has_tg_channel_mention": false
  }
}
```

---

### Feature 3: Non-Media Reference Detection
**Purpose**: Understand what Telegram posts reference when they don't cite traditional media.

**Categories Tracked**:
- Telegram Channels (@mentions, t.me/ links)
- Twitter/X, Facebook, Instagram, YouTube, TikTok
- Government sources (gov.ua domains)
- Other domains

**Output Format**:
```json
{
  "reference_detection": {
    "has_non_media_reference": true,
    "reference_categories": {
      "Telegram Channels": 3,
      "Twitter/X": 2,
      "Government": 1
    },
    "telegram_channels": ["channel1", "channel2", "channel3"],
    "urls_by_category": {
      "Twitter/X": ["https://twitter.com/..."],
      "Government": ["https://gov.ua/..."]
    }
  }
}
```

**Statistics**:
- Total messages with non-media references
- Percentage with non-media references
- Category breakdown
- Unique Telegram channels mentioned
- Messages without media but with other refs

---

### Feature 4: Bidirectional Content Reproduction Analysis
**Two Directions**:

**Media → Telegram** (traditional):
- Count how many times each media is referenced in Telegram
- Track: mentions, links, similarity matches
- Show which media content is reproduced in which channels
- Rank by total references

**Telegram → Media** (reverse):
- Detect when media articles cite Telegram channels
- Look for channel names, @mentions, t.me/ in article text
- Track which channels are cited and in which media
- Rank by citation count

**Comparison**:
- Calculate strength of content reproduction in each direction
- Determine dominant direction
- Provide top 5 influencers in each direction

**Output Files**:
- `bidirectional_influence.json` - Complete analysis
- Integrated into `analysis_all_channels.json`

---

### Feature 5: Interactive Visualizations
**Four Visualizations**:

1. **Influence Network** (`influence_network.html`)
   - Force-directed graph
   - Media (blue squares) → Telegram (orange circles)
   - Edge weight = reference count
   - Node size = influence strength
   - Interactive: hover for details, zoom, pan

2. **Media Ranking** (`media_ranking.html`)
   - Horizontal bar chart
   - Sorted by mention count
   - Color scale: Blues
   - Shows total mentions per media

3. **Channel Comparison** (`channel_comparison.html`)
   - Two subplots side-by-side
   - Left: Total messages (bar chart)
   - Right: Content reproduction percentage (colored bar chart)
   - Shows all channels

4. **Content Types** (`content_types.html`)
   - Donut chart (pie with hole)
   - Shows distribution of all content types
   - Interactive: hover for count and percentage

**Output Location**: `data/results/interactive/`

**Technology**: Plotly (generates standalone HTML files)

---

### Feature 6: Date Configuration
**Two Options**:

**Option 1 - Specific Start Date** (recommended):
```bash
START_DATE=2020-01-01
```
- Format: YYYY-MM-DD
- Takes precedence over months back
- Scrapes from this date onwards

**Option 2 - Relative Date**:
```bash
DATA_MONTHS_BACK=3
```
- Only used if START_DATE not set
- Calculates date from now

**Implementation**:
- Add to `.env` and `.env.template`
- Create `get_start_date()` helper in config.py
- Update both scrapers to use this function
- Display start date when scraping begins

---

## Integration Points

### Data Flow:
```
1. Scraping (telegram_scraper, media_scraper)
   ↓ Raw data with URLs and text

2. Link Detection (link_detector)
   ↓ Media URLs identified

3. Mention Detection (mention_detector - ENHANCED)
   ↓ Media mentions identified (case-insensitive)

4. Similarity Detection (similarity_detector)
   ↓ Similar content identified

5. Content Type Detection (content_type_detector - NEW)
   ↓ Content categorized

6. Reference Detection (reference_detector - NEW)
   ↓ Non-media references tracked

7. Combined Analysis (combined_analyzer)
   ↓ All detections combined, statistics calculated

8. Bidirectional Analysis (bidirectional_influence - NEW)
   ↓ Media↔Telegram influence analyzed

9. Report Generation (report_generator)
   ↓ Text reports with new stats

10. Interactive Visualizations (interactive_visualizations - NEW)
    ↓ HTML charts created
```

### Message Structure Evolution:
```json
{
  "id": "...",
  "text": "...",
  "channel_name": "...",  // Added in main.py
  "link_detection": {...},
  "mention_detection": {...},
  "similarity_detection": {...},
  "content_type_detection": {...},  // NEW
  "reference_detection": {...}       // NEW
}
```

### Statistics Structure Enhancement:
```json
{
  "statistics": {
    "total_messages": 1000,
    "influenced_by_media": 450,
    "percentage_influenced": 45.0,
    "detection_breakdown": {...},
    "by_method": {
      "links": {...},
      "mentions": {...},
      "similarity": {...}
    },
    "content_types": {           // NEW
      "content_type_counts": {...},
      "content_type_percentages": {...}
    },
    "references": {              // NEW
      "messages_with_non_media_references": 300,
      "reference_category_counts": {...},
      "unique_telegram_channels_mentioned": 15,
      ...
    }
  }
}
```

---

## Testing and Validation

### Test Plan:

1. **Content Type Detection Test**:
   - Create message with gov.ua link → should detect "government_source"
   - Create message with @channel → should detect "telegram_channel"
   - Create message with Facebook link → should detect "social_media"
   - Create plain news message → should detect "news"

2. **Reference Detection Test**:
   - Message with @channel mention → should extract channel name
   - Message with t.me/channel link → should extract channel name
   - Message without media but with Twitter link → should categorize as "Twitter/X"
   - Count unique Telegram channels across all messages

3. **Case-Insensitive Matching Test**:
   - "Труха" should match "труха україна"
   - "УКРАЇНСЬКА ПРАВДА" should match "Українська правда"
   - "Суспільне" should match "СУСПІЛЬНЕ"

4. **Bidirectional Analysis Test**:
   - Media mentioned in Telegram → should appear in media_to_telegram
   - Telegram channel name in media article → should appear in telegram_to_media
   - Verify top 5 influencers in each direction
   - Check dominant direction calculation

5. **Interactive Visualizations Test**:
   - All 4 HTML files should be created
   - Open each in browser - should be interactive
   - Network graph should show connections
   - Hover should display information

6. **Date Configuration Test**:
   - Set START_DATE=2020-01-01 → scraper should start from this date
   - Comment out START_DATE, set DATA_MONTHS_BACK=3 → should use relative date
   - Invalid date format → should fall back to DATA_MONTHS_BACK

### Validation Checklist:

- [ ] Content type detection works for all categories
- [ ] Reference detection extracts Telegram channels correctly
- [ ] Bidirectional analysis produces both directions
- [ ] Interactive visualizations create 4 HTML files
- [ ] Case-insensitive matching works for variants
- [ ] No errors when running `python main.py all`
- [ ] All output files generated successfully

### Expected Outputs:

After running `python main.py all`, you should have:

**Text Reports**:
- `data/results/report.txt` (enhanced with content types and references)

**JSON Data**:
- `data/results/analysis_all_channels.json` (new structure with bidirectional data)
- `data/results/bidirectional_influence.json` (new file)

**Static Visualizations**:
- `data/results/analysis_visualizations.png`

**Interactive Visualizations** (NEW):
- `data/results/interactive/influence_network.html`
- `data/results/interactive/media_ranking.html`
- `data/results/interactive/channel_comparison.html`
- `data/results/interactive/content_types.html`

**CSV Files**:
- `data/results/summary.csv`
- `data/results/detailed_messages.csv`

---

## Summary Statistics

**Code Changes**:
- New files: 4 Python modules (950+ lines)
- Modified files: 7 files (145+ lines modified)
- New dependencies: 1 (networkx)
- Configuration changes: 2 (.env.template, .env)

**New Capabilities**:
1. ✅ Content type detection (6 categories)
2. ✅ Non-media reference tracking
3. ✅ Official government source detection
4. ✅ Case-insensitive name matching with variants
5. ✅ Bidirectional content reproduction analysis (Media↔Telegram)
6. ✅ 4 interactive HTML visualizations
7. ✅ Configurable start date for data collection

**Research Questions Answered**:
1. What fills Telegram feeds besides news? → Content type detector
2. Official government influence? → Government source tracking
3. Non-media references? → Reference detector
4. All media sources included? → Already present, verified
5. Case variations? → Enhanced mention detector
6. Who reproduces content from whom more? → Bidirectional analysis
7. Interactive visualization? → 4 Plotly charts

---

## Implementation Order

Recommended order to minimize errors:

1. **First**: Add networkx to requirements.txt and install it
2. **Second**: Update configuration (config.py, .env, .env.template)
3. **Third**: Create content_type_detector.py
4. **Fourth**: Create reference_detector.py
5. **Fifth**: Update mention_detector.py (enhanced matching)
6. **Sixth**: Update combined_analyzer.py (integrate new detectors)
7. **Seventh**: Create bidirectional_influence.py
8. **Eighth**: Create interactive_visualizations.py
9. **Ninth**: Update main.py (bidirectional analysis integration)
10. **Tenth**: Update report_generator.py (new stats sections)
11. **Eleventh**: Update scrapers (date configuration)
12. **Finally**: Test complete pipeline with `python main.py all`

---

## Notes

- New features gracefully handle missing data
- Performance impact is minimal (all detections are O(n))
- Interactive visualizations are generated once, no runtime overhead
- No breaking changes to existing APIs

---

## End of Guide

This document contains everything needed to recreate all features from scratch. Feed this entire document to Claude with the instruction: "Please implement all features described in this guide."
