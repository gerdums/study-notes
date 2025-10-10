# Bible SCML Processor CLI Tool

A powerful command-line tool for processing complete Bible SCML files and extracting study notes and resources into consolidated JSON files.

## Overview

This tool processes large SCML files (like LSB.scml) containing an entire Bible with study notes, introductions, charts, maps, and other resources. It outputs two consolidated JSON files:

1. **`notes.json`** - All study notes for specific verses across the entire Bible
2. **`resources.json`** - All other resources (introductions, articles, charts, maps, etc.)

## Features

- ✅ **Memory efficient** - Uses streaming XML parsing for large files (29MB+)
- ✅ **Progress tracking** - Real-time progress with ETA estimates
- ✅ **Comprehensive coverage** - Processes all 66 Bible books
- ✅ **Rich metadata** - Includes book names, IDs, and verse references
- ✅ **Error handling** - Graceful error handling and reporting
- ✅ **Cross-references** - Preserves and formats Bible cross-references

## Performance

**Tested with LSB.scml (29MB file):**
- **Processing time:** ~1 second
- **Study notes extracted:** 16,535 notes
- **Study resources extracted:** 202 resources (filtered from 20,897+ structural elements)
- **Books processed:** 66 books

## Installation

No additional dependencies required beyond Python 3.6+. The tool uses only standard library modules.

## Usage

### Basic Usage
```bash
python3 bible_processor_cli.py LSB.scml
```

### Specify Output Directory
```bash
python3 bible_processor_cli.py LSB.scml --output-dir ./my_output
```

### Disable Progress Display
```bash
python3 bible_processor_cli.py LSB.scml --no-progress
```

### Full Example
```bash
python3 bible_processor_cli.py LSB.scml --output-dir ./biblical_data --progress
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `input_file` | Path to the SCML file (required) | - |
| `--output-dir` | Output directory for JSON files | `./output` |
| `--progress` | Show progress during processing | Enabled |
| `--no-progress` | Disable progress display | - |
| `--help` | Show help message | - |

## Output Structure

### notes.json
Each study note contains:
```json
{
  "start": 1001001,           // Numeric verse ID (BBCCCVVV format)
  "book": "Genesis",          // Human-readable book name
  "book_id": "bk01",         // Book ID from SCML
  "end": 1001005,            // End verse ID (for ranges)
  "content": "Formatted HTML content with cross-references"
}
```

### resources.json
Each resource contains:
```json
{
  "id": "resource_id",        // Unique resource identifier
  "book": "Genesis",          // Associated book
  "book_id": "bk01",         // Book ID from SCML
  "title": "Resource Title", // Human-readable title
  "content": "Formatted content",
  "type": "introduction"      // Resource type (introduction, chart, figure, etc.)
}
```

## Resource Types

The tool intelligently categorizes genuine study resources into these types:
- `introduction` - Book and section introductions (e.g., "Introduction to the Pentateuch")
- `article` - Study articles and supplementary content (e.g., user guides, theological articles)
- `notes` - Study notes and features not tied to specific verses
- `chart` - Study Bible charts and maps indexes
- `outline` - Book outlines and chronological timelines
- `background` - Historical and cultural background information

**Example resource counts for LSB.scml:**
- Articles: 71
- Notes: 121  
- Introductions: 5
- Charts: 2
- Outlines: 3

## Progress Tracking

When enabled, progress tracking shows:
- Current book being processed
- Percentage complete
- Books processed (current/total)
- Study notes found so far
- Resources found so far
- Estimated time remaining

Example output:
```
[45.5%] Processing: Amos
  📖 Books: 30/66
  📝 Notes found: 9,674
  📚 Resources found: 1,285
  ⏱️  ETA: 0:00:00
```

## Cross-Reference Format

Cross-references in the content are formatted as HTML-like tags:
```html
<a ref='Genesis 1:1'>Gen. 1:1</a>
```

Where:
- `ref` attribute contains the full book name and reference
- Display text uses abbreviated book names

## Error Handling

The tool provides clear error messages for common issues:
- File not found
- XML parsing errors
- Permission errors
- Unexpected content structure

## File Size Information

Output file sizes for LSB.scml:
- **notes.json:** ~8.5MB (16,535 notes)
- **resources.json:** ~5.1MB (202 study resources)

**Note:** The tool intelligently filters out Bible text, chapter headings, and structural elements, keeping only genuine study resources like introductions, charts, maps, articles, and study features. This reduces the resource count by 99% while preserving all meaningful study content.

## Memory Usage

The tool uses streaming XML parsing (`iterparse`) to handle large files efficiently without loading the entire file into memory at once. Memory usage remains low even for very large SCML files.

## Comparison with Previous Tools

| Feature | Previous Tools | New CLI Tool |
|---------|---------------|-------------|
| Scope | Single book processing | Entire Bible processing |
| Output | Per-book JSON files | Consolidated JSON files |
| Progress | Minimal feedback | Real-time progress tracking |
| Memory | Loads entire books | Streaming processing |
| Speed | Varies by book | ~1 second for entire Bible |

## Tips for Large Files

1. **Use SSD storage** for faster I/O
2. **Sufficient disk space** - Output can be ~25MB total
3. **Terminal with Unicode support** for progress emojis
4. **Redirect output** if processing in scripts:
   ```bash
   python3 bible_processor_cli.py LSB.scml --no-progress > processing.log 2>&1
   ```

## Integration Examples

### Python Script Integration
```python
import subprocess
import json

# Run the processor
result = subprocess.run([
    'python3', 'bible_processor_cli.py', 
    'LSB.scml', 
    '--output-dir', './data',
    '--no-progress'
], capture_output=True, text=True)

if result.returncode == 0:
    # Load the results
    with open('./data/notes.json', 'r') as f:
        notes = json.load(f)
    
    with open('./data/resources.json', 'r') as f:
        resources = json.load(f)
    
    print(f"Loaded {len(notes)} notes and {len(resources)} resources")
```

### Makefile Integration
```make
biblical-data: LSB.scml
	python3 bible_processor_cli.py LSB.scml --output-dir ./biblical-data
	@echo "Biblical data processing complete"

clean:
	rm -rf ./biblical-data
```

## Troubleshooting

### Common Issues

**"zsh: command not found: python"**
- Use `python3` instead of `python`

**"Input file not found"**
- Check the file path and ensure LSB.scml exists
- Use absolute paths if needed

**"Permission denied"**
- Check write permissions for the output directory
- Try a different output directory

**"Memory error" (rare)**
- Close other applications
- Use a machine with more RAM
- Try processing smaller files first

### Debug Mode
To see more detailed error information, run with Python's verbose mode:
```bash
python3 -v bible_processor_cli.py LSB.scml
```

## License

This tool is part of the Bible SCML Processing project. Refer to the main project documentation for licensing information.

## Support

For issues or questions:
1. Check this README for common solutions
2. Review error messages carefully
3. Test with smaller SCML files if possible
4. Create an issue with your specific error message and system information 