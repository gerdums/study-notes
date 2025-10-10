# Bible Study Notes Processor

This script processes SCML (Scripture Markup Language) files containing Bible text, study notes, and resources, extracting them into separate JSON files by book.

## Features

- Extracts individual books from a large SCML file
- Identifies book names from various XML attributes and patterns
- Creates `notes.json` containing verse-level study notes for each book
- Creates `resources.json` containing charts, maps, and other supplementary content
- Handles incomplete or malformed XML gracefully
- Provides fallback mechanisms for identifying book content

## Usage

```bash
python bible_book_processor.py <input_scml_file> <output_directory>
```

### Example

```bash
python bible_book_processor.py bible.scml output
```

This will process `bible.scml` and create separate directories for each book in the `output` directory. Each book directory will contain:

- `notes.json`: Study notes for verses in that book
- `resources.json`: Charts, maps, and other resources for that book

## Output Format

### notes.json

The `notes.json` file contains an array of study note objects, each with the following structure:

```json
{
  "start": 1001001,     // Numeric ID in format BBCCCVVV (book, chapter, verse)
  "end": 1001005,       // Optional end reference for note ranges
  "content": "<b><a>Gen. 1:1-5</a></b> This is a study note..."
}
```

### resources.json

The `resources.json` file contains an array of resource objects, each with the following structure:

```json
{
  "id": "sbch-01007004",                // Resource ID
  "title": "The Flood Chronology",      // Resource title
  "content": "This chart presents...",  // Resource content
  "type": "chart"                       // Resource type (chart, figure, etc.)
}
```

## Requirements

- Python 3.6 or higher
- No external libraries required

## Troubleshooting

If the script fails to extract book content properly:

1. Check that your SCML file follows standard formatting
2. Try specifying book names and IDs clearly in the SCML file
3. Look for missing closing tags or other XML validation issues 