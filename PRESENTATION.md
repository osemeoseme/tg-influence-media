# Presentation Guide

This document explains how to use and share the research presentation files.

## Available Presentations

### presentation.html (Recommended for local use)
- **Size**: ~41KB
- **Dependencies**: Requires `data/results/` folder with all visualization images
- **Best for**: Local viewing and development
- **How to open**: Double-click the file or open in any modern browser

### presentation_standalone.html (Recommended for sharing)
- **Size**: ~3.2MB
- **Dependencies**: None - all images embedded as Base64
- **Best for**: Sharing via email, cloud storage, or presentations
- **How to open**: Double-click the file or open in any modern browser
- **Advantage**: Works offline, no external files needed

## Navigation

### Keyboard Shortcuts
- **Arrow Keys** or **Space**: Next slide
- **Arrow Left** or **Shift+Space**: Previous slide
- **F**: Enter fullscreen mode
- **Esc**: Exit fullscreen
- **O** or **Esc**: Overview mode (see all slides)
- **?**: Show help with all keyboard shortcuts

### Mouse Navigation
- Click right/left sides of screen to navigate
- Use on-screen arrows if available

## Presentation Structure

### 1. Title & Introduction
- Project overview
- Dataset size (1M+ messages)

### 2. Methodology
- Three detection methods explained:
  - Direct link detection
  - Media mention detection
  - Semantic similarity detection

### 3. Data Sources
- 142 media outlets (national + regional)
- 13 Telegram channels
- Time window and data collection details

### 4. Key Findings
- **Important**: Understanding the 40% vs 22.3% distinction:
  - **40% of messages** contain at least one traditional media reference
  - **22.3% of all URLs** point to traditional media (messages often cite multiple sources)
  
  **Example**: A message citing "Українська правда + BBC + YouTube" counts as:
  - 1 message with traditional media content reproduction (→ included in 40%)
  - 3 citations, only 1 to traditional media (→ 33% of citations)

### 5. Visualizations

#### Reference Categories (Pie Chart)
- Shows distribution of ALL citations across all source types
- Traditional media = ~25% (22.3% + 2.8% via Telegram)
- "Other domains" (53.4%) include government, international news, misc sites
- Telegram channels themselves are a major source (11.5%)

#### Detection Methods Breakdown (Bar Chart)
- **Two sections separated by dashed line**:
  - **Independent Channels** (bottom): 20-53% content reproduced from traditional media
  - **Traditional Media Channels** (top): 77-79% cite their own content (expected)
- Color coding:
  - Blue: Links only
  - Orange: Mentions only
  - Green: Similarity only
  - Red: Multiple methods

#### Temporal Visualizations
- Message volume over time
- Activity heatmaps showing posting patterns

### 6. Conclusions
- Traditional media competes with many other sources
- Independent channels show significant content reproduction from media
- Most content reproduction detected through mentions and semantic similarity, not direct links

## Key Insights to Highlight

### 1. Messages vs Citations Distinction
This is the most important clarification:
- **Messages** = Telegram posts (the unit being analyzed)
- **Citations** = Individual URLs within those messages
- One message can contain multiple citations to different sources
- That's why percentages differ

### 2. Channel Type Separation
- **Independent channels** (9): Труха Україна, Батальон "Монако", etc.
  - 20-53% content reproduced from traditional media
- **Traditional media channels** (4): Українська правда, Суспільне, ТСН, УНИАН
  - 77-79% cite their own content (this is expected behavior)

### 3. Detection Method Effectiveness
- **Mentions** and **semantic similarity** detect most content reproduction
- **Direct links** are less common
- This suggests much content is rephrased or attributed verbally rather than linked

## Sharing the Presentation

### For Email/Cloud Sharing
Use `presentation_standalone.html`:
1. Upload to Google Drive, Dropbox, OneDrive, etc.
2. Share the link
3. Recipients can download and open directly in their browser

### For Presentations/Meetings
1. Use `presentation_standalone.html` for portability
2. Press **F** for fullscreen mode
3. Navigate with arrow keys or remote clicker
4. Press **Esc** to exit fullscreen

### For Embedding in Websites
- `presentation.html` is smaller and recommended
- Ensure `data/results/` folder is accessible via relative path
- Or use `presentation_standalone.html` for guaranteed compatibility

## Customization

To modify the presentations:
1. Edit `presentation.html` (source file)
2. Regenerate standalone version if needed:
   ```bash
   python3 /tmp/embed_images.py
   ```

## Technical Details

### Built With
- **Reveal.js 4.5.0**: HTML presentation framework
- **Chart.js**: For some interactive charts (if added)
- **Matplotlib/Seaborn**: For generated PNG visualizations

### Browser Compatibility
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Internet Explorer: Not supported (use modern browser)

### Image Formats
- All visualizations are PNG format
- Embedded images use Base64 encoding in standalone version
- DPI: 300 for print quality

## Troubleshooting

### Presentation shows broken images
- Using `presentation.html`: Ensure `data/results/` folder exists in the same directory
- Using `presentation_standalone.html`: Should never happen (images embedded)

### Navigation doesn't work
- Try different browser
- Ensure JavaScript is enabled
- Check browser console for errors (F12)

### Fullscreen doesn't work
- Use **F** key, not browser's native fullscreen
- Some browsers may require permission for fullscreen

### File is too large to email
- `presentation_standalone.html` is 3.2MB
- Most email providers allow up to 25MB attachments
- If needed, use cloud sharing instead

## Support

For issues or questions:
- Check the main [README.md](README.md) for project documentation
- Review [METHODOLOGY.md](METHODOLOGY.md) for technical details
- Contact project supervisor: Andrii Ianitskyi (a.ianitskyi@gmail.com)
