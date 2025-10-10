#!/usr/bin/env python3
"""
Bible SCML Processor CLI Tool

This tool processes a complete Bible SCML file and outputs:
1. notes.json - All study notes for verses across the entire Bible
2. resources.json - All other resources (introductions, articles, charts, maps, etc.)

Usage:
    python bible_processor_cli.py LSB.scml --output-dir ./output --progress
"""

import xml.etree.ElementTree as ET
import json
import re
import os
import argparse
import time
from datetime import datetime, timedelta
from io import StringIO
import sys

# Comprehensive mapping of book abbreviations to names and numbers
BOOK_INFO = {
    # Pentateuch
    "Ge": {"name": "Gen.", "num": "01", "full_name": "Genesis"}, "Gen": {"name": "Gen.", "num": "01", "full_name": "Genesis"},
    "Ex": {"name": "Ex.", "num": "02", "full_name": "Exodus"}, "Exo": {"name": "Ex.", "num": "02", "full_name": "Exodus"},
    "Le": {"name": "Lev.", "num": "03", "full_name": "Leviticus"}, "Lev": {"name": "Lev.", "num": "03", "full_name": "Leviticus"},
    "Nu": {"name": "Num.", "num": "04", "full_name": "Numbers"}, "Num": {"name": "Num.", "num": "04", "full_name": "Numbers"},
    "De": {"name": "Deut.", "num": "05", "full_name": "Deuteronomy"}, "Dt": {"name": "Deut.", "num": "05", "full_name": "Deuteronomy"}, "Deut": {"name": "Deut.", "num": "05", "full_name": "Deuteronomy"},
    # History
    "Jos": {"name": "Josh.", "num": "06", "full_name": "Joshua"}, "Josh": {"name": "Josh.", "num": "06", "full_name": "Joshua"},
    "Jdg": {"name": "Judg.", "num": "07", "full_name": "Judges"}, "Judg": {"name": "Judg.", "num": "07", "full_name": "Judges"},
    "Ru": {"name": "Ruth", "num": "08", "full_name": "Ruth"}, "Ruth": {"name": "Ruth", "num": "08", "full_name": "Ruth"},
    "1Sa": {"name": "1 Sam.", "num": "09", "full_name": "1 Samuel"}, "1 Sam": {"name": "1 Sam.", "num": "09", "full_name": "1 Samuel"},
    "2Sa": {"name": "2 Sam.", "num": "10", "full_name": "2 Samuel"}, "2 Sam": {"name": "2 Sam.", "num": "10", "full_name": "2 Samuel"},
    "1Ki": {"name": "1 Kings", "num": "11", "full_name": "1 Kings"}, "1 Kin": {"name": "1 Kings", "num": "11", "full_name": "1 Kings"}, "1Kgs": {"name": "1 Kings", "num": "11", "full_name": "1 Kings"},
    "2Ki": {"name": "2 Kings", "num": "12", "full_name": "2 Kings"}, "2 Kin": {"name": "2 Kings", "num": "12", "full_name": "2 Kings"}, "2Kgs": {"name": "2 Kings", "num": "12", "full_name": "2 Kings"},
    "1Ch": {"name": "1 Chron.", "num": "13", "full_name": "1 Chronicles"}, "1 Chr": {"name": "1 Chron.", "num": "13", "full_name": "1 Chronicles"},
    "2Ch": {"name": "2 Chron.", "num": "14", "full_name": "2 Chronicles"}, "2 Chr": {"name": "2 Chron.", "num": "14", "full_name": "2 Chronicles"},
    "Ezr": {"name": "Ezra", "num": "15", "full_name": "Ezra"},
    "Ne": {"name": "Neh.", "num": "16", "full_name": "Nehemiah"}, "Neh": {"name": "Neh.", "num": "16", "full_name": "Nehemiah"},
    "Est": {"name": "Est.", "num": "17", "full_name": "Esther"},
    # Wisdom
    "Job": {"name": "Job", "num": "18", "full_name": "Job"},
    "Ps": {"name": "Ps.", "num": "19", "full_name": "Psalms"}, "Psa": {"name": "Ps.", "num": "19", "full_name": "Psalms"}, "Pss": {"name": "Ps.", "num": "19", "full_name": "Psalms"},
    "Pr": {"name": "Prov.", "num": "20", "full_name": "Proverbs"}, "Prov": {"name": "Prov.", "num": "20", "full_name": "Proverbs"},
    "Ec": {"name": "Eccl.", "num": "21", "full_name": "Ecclesiastes"}, "Eccl": {"name": "Eccl.", "num": "21", "full_name": "Ecclesiastes"},
    "So": {"name": "Song", "num": "22", "full_name": "Song of Solomon"}, "Song": {"name": "Song of Sol.", "num": "22", "full_name": "Song of Solomon"}, "SOS": {"name": "Song of Sol.", "num": "22", "full_name": "Song of Solomon"},
    # Major Prophets
    "Is": {"name": "Isa.", "num": "23", "full_name": "Isaiah"}, "Isa": {"name": "Isa.", "num": "23", "full_name": "Isaiah"},
    "Je": {"name": "Jer.", "num": "24", "full_name": "Jeremiah"}, "Jer": {"name": "Jer.", "num": "24", "full_name": "Jeremiah"},
    "La": {"name": "Lam.", "num": "25", "full_name": "Lamentations"},
    "Eze": {"name": "Ezek.", "num": "26", "full_name": "Ezekiel"}, "Ezek": {"name": "Ezek.", "num": "26", "full_name": "Ezekiel"},
    "Da": {"name": "Dan.", "num": "27", "full_name": "Daniel"}, "Dan": {"name": "Dan.", "num": "27", "full_name": "Daniel"},
    # Minor Prophets
    "Ho": {"name": "Hos.", "num": "28", "full_name": "Hosea"}, "Hos": {"name": "Hos.", "num": "28", "full_name": "Hosea"},
    "Joe": {"name": "Joel", "num": "29", "full_name": "Joel"},
    "Am": {"name": "Amos", "num": "30", "full_name": "Amos"},
    "Ob": {"name": "Obad.", "num": "31", "full_name": "Obadiah"},
    "Jon": {"name": "Jonah", "num": "32", "full_name": "Jonah"},
    "Mic": {"name": "Mic.", "num": "33", "full_name": "Micah"},
    "Na": {"name": "Nah.", "num": "34", "full_name": "Nahum"},
    "Hab": {"name": "Hab.", "num": "35", "full_name": "Habakkuk"},
    "Zep": {"name": "Zeph.", "num": "36", "full_name": "Zephaniah"}, "Zeph": {"name": "Zeph.", "num": "36", "full_name": "Zephaniah"},
    "Hag": {"name": "Hag.", "num": "37", "full_name": "Haggai"},
    "Zec": {"name": "Zech.", "num": "38", "full_name": "Zechariah"}, "Zech": {"name": "Zech.", "num": "38", "full_name": "Zechariah"},
    "Mal": {"name": "Mal.", "num": "39", "full_name": "Malachi"},
    # Gospels
    "Mt": {"name": "Matt.", "num": "40", "full_name": "Matthew"}, "Matt": {"name": "Matt.", "num": "40", "full_name": "Matthew"},
    "Mk": {"name": "Mark", "num": "41", "full_name": "Mark"},
    "Lu": {"name": "Luke", "num": "42", "full_name": "Luke"}, "Lk": {"name": "Luke", "num": "42", "full_name": "Luke"},
    "Jn": {"name": "John", "num": "43", "full_name": "John"},
    # Acts
    "Ac": {"name": "Acts", "num": "44", "full_name": "Acts"},
    # Pauline Epistles
    "Ro": {"name": "Rom.", "num": "45", "full_name": "Romans"}, "Rom": {"name": "Rom.", "num": "45", "full_name": "Romans"},
    "1Co": {"name": "1 Cor.", "num": "46", "full_name": "1 Corinthians"}, "1Cor": {"name": "1 Cor.", "num": "46", "full_name": "1 Corinthians"},
    "2Co": {"name": "2 Cor.", "num": "47", "full_name": "2 Corinthians"}, "2Cor": {"name": "2 Cor.", "num": "47", "full_name": "2 Corinthians"},
    "Ga": {"name": "Gal.", "num": "48", "full_name": "Galatians"}, "Gal": {"name": "Gal.", "num": "48", "full_name": "Galatians"},
    "Eph": {"name": "Eph.", "num": "49", "full_name": "Ephesians"},
    "Php": {"name": "Phil.", "num": "50", "full_name": "Philippians"}, "Phil": {"name": "Phil.", "num": "50", "full_name": "Philippians"},
    "Col": {"name": "Col.", "num": "51", "full_name": "Colossians"},
    "1Th": {"name": "1 Thess.", "num": "52", "full_name": "1 Thessalonians"}, "1Thess": {"name": "1 Thess.", "num": "52", "full_name": "1 Thessalonians"},
    "2Th": {"name": "2 Thess.", "num": "53", "full_name": "2 Thessalonians"}, "2Thess": {"name": "2 Thess.", "num": "53", "full_name": "2 Thessalonians"},
    "1Ti": {"name": "1 Tim.", "num": "54", "full_name": "1 Timothy"}, "1Tim": {"name": "1 Tim.", "num": "54", "full_name": "1 Timothy"},
    "2Ti": {"name": "2 Tim.", "num": "55", "full_name": "2 Timothy"}, "2Tim": {"name": "2 Tim.", "num": "55", "full_name": "2 Timothy"},
    "Tit": {"name": "Titus", "num": "56", "full_name": "Titus"},
    "Phm": {"name": "Philem.", "num": "57", "full_name": "Philemon"}, "Philemon": {"name": "Philem.", "num": "57", "full_name": "Philemon"},
    # General Epistles
    "Heb": {"name": "Heb.", "num": "58", "full_name": "Hebrews"},
    "Jam": {"name": "Jas.", "num": "59", "full_name": "James"}, "Jas": {"name": "Jas.", "num": "59", "full_name": "James"},
    "1Pe": {"name": "1 Pet.", "num": "60", "full_name": "1 Peter"}, "1Pet": {"name": "1 Pet.", "num": "60", "full_name": "1 Peter"},
    "2Pe": {"name": "2 Pet.", "num": "61", "full_name": "2 Peter"}, "2Pet": {"name": "2 Pet.", "num": "61", "full_name": "2 Peter"},
    "1Jn": {"name": "1 John", "num": "62", "full_name": "1 John"},
    "2Jn": {"name": "2 John", "num": "63", "full_name": "2 John"},
    "3Jn": {"name": "3 John", "num": "64", "full_name": "3 John"},
    "Jude": {"name": "Jude", "num": "65", "full_name": "Jude"}, "Jud": {"name": "Jude", "num": "65", "full_name": "Jude"}, "Jd": {"name": "Jude", "num": "65", "full_name": "Jude"},
    # Revelation
    "Rev": {"name": "Rev.", "num": "66", "full_name": "Revelation"}
}

# Regex pattern for Bible references
REF_PATTERN = re.compile(
    r"([1-3]?[A-Za-z]+)\s*(\d+):(\d+)"  # Book C:V (Group 1,2,3)
    r"(?:(?:–|-)(\d+):(\d+)|(?:–|-)(\d+))?"  # Optional -C:V (Group 4,5) or -V (Group 6)
)

class ProgressTracker:
    """Tracks and displays progress for the Bible processing"""
    
    def __init__(self, total_books=66, show_progress=True):
        self.total_books = total_books
        self.show_progress = show_progress
        self.start_time = time.time()
        self.books_processed = 0
        self.notes_found = 0
        self.resources_found = 0
        self.current_book = ""
        
    def update_book(self, book_name):
        """Update the current book being processed"""
        self.current_book = book_name
        self.books_processed += 1
        if self.show_progress:
            elapsed = time.time() - self.start_time
            if self.books_processed > 0:
                avg_time_per_book = elapsed / self.books_processed
                remaining_books = self.total_books - self.books_processed
                eta_seconds = avg_time_per_book * remaining_books
                eta = timedelta(seconds=int(eta_seconds))
            else:
                eta = "calculating..."
            
            progress_pct = (self.books_processed / self.total_books) * 100
            print(f"\n[{progress_pct:.1f}%] Processing: {book_name}")
            print(f"  📖 Books: {self.books_processed}/{self.total_books}")
            print(f"  📝 Notes found: {self.notes_found}")
            print(f"  📚 Resources found: {self.resources_found}")
            print(f"  ⏱️  ETA: {eta}")
            
    def add_notes(self, count):
        """Add to the notes counter"""
        self.notes_found += count
        
    def add_resources(self, count):
        """Add to the resources counter"""
        self.resources_found += count
        
    def finish(self):
        """Display final summary"""
        elapsed = time.time() - self.start_time
        elapsed_time = timedelta(seconds=int(elapsed))
        
        if self.show_progress:
            print(f"\n✅ Processing Complete!")
            print(f"  📖 Books processed: {self.books_processed}")
            print(f"  📝 Total notes: {self.notes_found}")
            print(f"  📚 Total resources: {self.resources_found}")
            print(f"  ⏱️  Total time: {elapsed_time}")

def get_book_details(book_abbr_input):
    """Get standardized book details from abbreviation."""
    book_abbr_norm = book_abbr_input.title()
    if book_abbr_norm in BOOK_INFO:
        return BOOK_INFO[book_abbr_norm]
    if book_abbr_norm.endswith('s') and book_abbr_norm[:-1] in BOOK_INFO:
        return BOOK_INFO[book_abbr_norm[:-1]]
    if book_abbr_input in BOOK_INFO:
        return BOOK_INFO[book_abbr_input]
        
    return {"name": book_abbr_input, "num": "00", "full_name": book_abbr_input}

def ref_to_id_val(book_abbr, chap, verse):
    """Convert a book reference to a numeric ID."""
    details = get_book_details(book_abbr)
    try:
        return int(f"{details['num']}{int(chap):03d}{int(verse):03d}")
    except ValueError:
        return 0

def format_ref_for_display(book_abbr, chap_start, verse_start, chap_end=None, verse_end_or_range_end=None):
    """Format a reference for display."""
    details = get_book_details(book_abbr)
    book_name_disp = details['name']

    if chap_end and verse_end_or_range_end:
        return f"{book_name_disp} {chap_start}:{verse_start}–{chap_end}:{verse_end_or_range_end}"
    elif verse_end_or_range_end:
        return f"{book_name_disp} {chap_start}:{verse_start}–{verse_end_or_range_end}"
    else:
        return f"{book_name_disp} {chap_start}:{verse_start}"

def format_ref_for_ref_attribute(book_abbr, chap_start, verse_start, chap_end=None, verse_end_or_range_end=None):
    """Format a reference for use in the ref attribute."""
    details = get_book_details(book_abbr)
    book_name_full = details.get('full_name', details['name'])

    if chap_end and verse_end_or_range_end:
        return f"{book_name_full} {chap_start}:{verse_start}–{chap_end}:{verse_end_or_range_end}"
    elif verse_end_or_range_end:
        return f"{book_name_full} {chap_start}:{verse_start}–{verse_end_or_range_end}"
    else:
        return f"{book_name_full} {chap_start}:{verse_start}"

def parse_ref_string(ref_str):
    """Parse a Bible reference string into components."""
    if not ref_str: 
        return None, None, ref_str
    match = REF_PATTERN.match(ref_str.strip())
    if not match:
        return None, None, ref_str

    book_abbr = match.group(1)
    chap_start = match.group(2)
    verse_start = match.group(3)
    
    end_chap_specific = match.group(4)
    end_verse_specific = match.group(5)
    end_verse_range_same_chap = match.group(6)
    
    display_ref = format_ref_for_display(book_abbr, chap_start, verse_start,
                                         end_chap_specific,
                                         end_verse_specific if end_verse_specific else end_verse_range_same_chap)
    
    end_id = None
    if end_chap_specific and end_verse_specific:
        end_id = ref_to_id_val(book_abbr, end_chap_specific, end_verse_specific)
    elif end_verse_range_same_chap:
        end_id = ref_to_id_val(book_abbr, chap_start, end_verse_range_same_chap)
    
    return None, end_id, display_ref

def serialize_element_content(element, is_top_com_element=False):
    """Convert XML element content to structured HTML-like string."""
    chunks = []
    
    if element.text:
        if not is_top_com_element or (is_top_com_element and not list(element)):
             chunks.append(element.text.strip())

    bcv_skipped_for_top_node = False
    for child in element:
        if is_top_com_element and not bcv_skipped_for_top_node and child.tag == 'bcv':
            bcv_skipped_for_top_node = True
            if child.tail:
                chunks.append(child.tail.strip())
            continue

        tag = child.tag
        if tag == 'b':
            chunks.append(f"<b>{serialize_element_content(child)}</b>")
        elif tag == 'i':
            chunks.append(f"<i>{serialize_element_content(child)}</i>")
        elif tag == 'xbr':
            t_attr = child.get('t')
            scml_text_content = child.text.strip() if child.text and child.text.strip() else None

            ref_attribute_string = ""
            if t_attr:
                match_for_ref = REF_PATTERN.match(t_attr.strip())
                if match_for_ref:
                    b_abbr, c_start, v_start, e_chap, e_verse_cv, e_verse_v = match_for_ref.groups()
                    ref_attribute_string = format_ref_for_ref_attribute(b_abbr, c_start, v_start, e_chap, e_verse_cv if e_verse_cv else e_verse_v)
                else:
                    ref_attribute_string = t_attr
            
            link_display_text_final = ""
            if scml_text_content:
                link_display_text_final = scml_text_content
            elif t_attr:
                _, _, display_ref_for_empty_xbr = parse_ref_string(t_attr) 
                link_display_text_final = display_ref_for_empty_xbr if display_ref_for_empty_xbr else t_attr
            
            if t_attr:
                escaped_ref_attr = ref_attribute_string.replace("'", "&apos;").replace('"', "&quot;")
                chunks.append(f"<a ref=\'{escaped_ref_attr}\'>{link_display_text_final}</a>")
            else:
                chunks.append(f"<a>{link_display_text_final}</a>")
        else:
            chunks.append(serialize_element_content(child))

        if child.tail:
            chunks.append(child.tail.strip())
            
    return " ".join(s for s in chunks if s and s.strip())

def get_book_name_from_id(book_id):
    """Extract book name from book ID like 'bk01' -> 'Genesis'"""
    if not book_id:
        return "Unknown"
    
    # Extract number from book ID (e.g., 'bk01' -> '01')
    match = re.match(r'bk(\d+)', book_id)
    if match:
        book_num = match.group(1)
        # Find the book by number
        for abbr, details in BOOK_INFO.items():
            if details.get('num') == book_num:
                return details.get('full_name', abbr)
    
    return book_id

def process_bible_scml(input_file, output_dir, show_progress=True):
    """Process the entire Bible SCML file and create consolidated JSON files."""
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize collections
    all_notes = []
    all_resources = []
    
    # Initialize progress tracker
    progress = ProgressTracker(show_progress=show_progress)
    
    if show_progress:
        print(f"🚀 Starting Bible SCML processing...")
        print(f"📁 Input file: {input_file}")
        print(f"📁 Output directory: {output_dir}")
        file_size = os.path.getsize(input_file) / (1024*1024)
        print(f"📊 File size: {file_size:.1f} MB")
    
    try:
        # Use iterparse for memory efficiency with large files
        context = ET.iterparse(input_file, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        current_book_name = "Unknown"
        current_book_id = None
        
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'book':
                    book_id = elem.get('id')
                    book_semantic = elem.get('semantic')
                    
                    if book_id and book_id.startswith('bk'):
                        # This is a Bible book
                        current_book_id = book_id
                        current_book_name = book_semantic or get_book_name_from_id(book_id)
                        progress.update_book(current_book_name)
                    elif book_semantic and not book_id:
                        # Front matter book
                        current_book_name = book_semantic
                        current_book_id = None
            
            elif event == 'end':
                if elem.tag == 'com':
                    # Process study note
                    note_entry = process_study_note(elem, current_book_name, current_book_id)
                    if note_entry:
                        all_notes.append(note_entry)
                        progress.add_notes(1)
                    elem.clear()
                
                elif elem.tag in ['sbch', 'sbfig', 'figure', 'chapter']:
                    # Process potential resource (will filter out Bible text and structural elements)
                    resource_entry = process_resource(elem, current_book_name, current_book_id)
                    if resource_entry:
                        all_resources.append(resource_entry)
                        progress.add_resources(1)
                    elem.clear()
                
                # Clear processed elements to save memory
                if elem.tag == 'book':
                    elem.clear()
    
    except ET.ParseError as e:
        print(f"❌ Error parsing SCML file: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Sort notes by start ID for better organization
    all_notes.sort(key=lambda x: x.get('start', 0))
    
    # Write output files
    notes_file = os.path.join(output_dir, 'notes.json')
    resources_file = os.path.join(output_dir, 'resources.json')
    
    try:
        if show_progress:
            print(f"\n💾 Writing notes.json...")
        with open(notes_file, 'w', encoding='utf-8') as f:
            json.dump(all_notes, f, ensure_ascii=False, indent=2)
        
        if show_progress:
            print(f"💾 Writing resources.json...")
        with open(resources_file, 'w', encoding='utf-8') as f:
            json.dump(all_resources, f, ensure_ascii=False, indent=2)
        
        progress.finish()
        
        if show_progress:
            print(f"📝 Notes written to: {notes_file}")
            print(f"📚 Resources written to: {resources_file}")
        
        return True
        
    except IOError as e:
        print(f"❌ Error writing output files: {e}")
        return False

def process_study_note(com_element, book_name, book_id):
    """Process a single study note (com element)."""
    note_entry = {}
    com_id_full = com_element.get('id')
    
    if not com_id_full:
        return None
    
    # Derive start_id from com_id
    match_id = re.match(r"com(\d+)", com_id_full)
    if not match_id:
        return None
    
    note_entry['start'] = int(match_id.group(1))
    note_entry['book'] = book_name
    if book_id:
        note_entry['book_id'] = book_id
    
    header_html = ""
    # Process initial <bcv><xbr> for header and potential end_id
    bcv_tag = com_element.find('bcv')
    if bcv_tag is not None:
        xbr_in_bcv = bcv_tag.find('xbr')
        if xbr_in_bcv is not None:
            t_attr = xbr_in_bcv.get('t')
            if t_attr:
                _, parsed_end_id, display_ref_str = parse_ref_string(t_attr)
                if display_ref_str:
                    header_html = f"<b><a>{display_ref_str}</a></b>"
                if parsed_end_id and parsed_end_id != note_entry['start']:
                    note_entry['end'] = parsed_end_id
    
    # Process the rest of the content
    main_body_html = serialize_element_content(com_element, is_top_com_element=True)
    
    full_content = header_html
    if main_body_html:
        if full_content:
            full_content += " "
        full_content += main_body_html
    
    note_entry['content'] = re.sub(r'\s+', ' ', full_content).strip()
    
    return note_entry if note_entry['content'] else None

def process_resource(elem, book_name, book_id):
    """Process a resource element, filtering out Bible text and structural elements."""
    resource_id = elem.get('id', '')
    semantic = elem.get('semantic', '').lower()
    
    # Filter out Bible text chapters and basic structural elements
    if elem.tag == 'chapter':
        # Only include genuine study resources, not Bible text
        if not any(keyword in semantic for keyword in [
            'introduction', 'outline', 'notes', 'features', 'translator', 'cross-references', 
            'article', 'timeline', 'map', 'chart', 'background', 'setting', 'theme', 'purpose'
        ]):
            # Skip Bible text chapters (e.g., "Genesis 1", "Matthew 5")
            if re.match(r'^[a-z0-9\s]+\s+\d+$', semantic):
                return None
            # Skip basic titles and headings
            if len(semantic.split()) <= 3 and not any(word in semantic for word in ['introduction', 'outline', 'notes']):
                return None
    
    # Study Bible charts and figures are always resources
    if elem.tag in ['sbch', 'sbfig']:
        pass  # Always include these
    
    # Regular figures - be selective
    elif elem.tag == 'figure':
        # Skip if it's just a basic structural figure
        if not resource_id or resource_id.startswith('fig') and len(resource_id) < 10:
            return None
    
    # Generate resource entry
    resource_entry = {}
    
    if not resource_id and elem.tag == 'chapter':
        original_semantic = elem.get('semantic', '')
        if original_semantic:
            resource_id = f"ch_{original_semantic.replace(' ', '_')}"
        else:
            return None
    
    resource_entry['id'] = resource_id or f"resource_{elem.tag}"
    resource_entry['book'] = book_name
    if book_id:
        resource_entry['book_id'] = book_id
    
    # Process title - be more selective about title sources
    title = None
    
    # Look for meaningful titles in order of preference
    for title_tag in ['ctfm', 'ct', 'ah', 'inh', 'h1', 'h2']:
        title_elem = elem.find(f'.//{title_tag}')
        if title_elem is not None and title_elem.text and title_elem.text.strip():
            title = title_elem.text.strip()
            break
    
    # Use semantic as fallback, but filter out basic ones
    if not title and semantic:
        # Skip very basic semantics
        if not re.match(r'^[a-z0-9\s]+\s+\d+$', semantic) and len(semantic.split()) > 1:
            title = elem.get('semantic')  # Use original case for title
    
    if not title:
        title = f"Resource {resource_entry['id']}"
    
    resource_entry['title'] = title
    
    # Process content and filter out minimal content
    try:
        content_html = serialize_element_content(elem)
        content_clean = re.sub(r'\s+', ' ', content_html).strip()
        
        # Filter out resources with minimal or meaningless content
        if len(content_clean) < 50:  # Very short content
            return None
        
        # Filter out content that's just titles or headings
        if content_clean.lower() == title.lower():
            return None
            
        resource_entry['content'] = content_clean
        
    except Exception as e:
        return None  # Skip resources with processing errors
    
    # Determine resource type and be more selective
    if elem.tag == 'sbfig':
        resource_entry['type'] = 'figure'
    elif elem.tag == 'sbch':
        resource_entry['type'] = 'chart'
    elif elem.tag == 'figure':
        resource_entry['type'] = 'figure'
    elif elem.tag == 'chapter':
        if 'introduction' in semantic:
            resource_entry['type'] = 'introduction'
        elif any(keyword in semantic for keyword in ['notes', 'features', 'translator']):
            resource_entry['type'] = 'notes'
        elif any(keyword in semantic for keyword in ['outline', 'timeline', 'chronology']):
            resource_entry['type'] = 'outline'
        elif any(keyword in semantic for keyword in ['background', 'setting', 'context']):
            resource_entry['type'] = 'background'
        elif any(keyword in semantic for keyword in ['map', 'chart', 'table']):
            resource_entry['type'] = 'chart'
        else:
            # For other chapter content, be very selective
            if len(resource_entry['content']) < 200:  # Short content probably not a real resource
                return None
            resource_entry['type'] = 'article'
    else:
        resource_entry['type'] = 'other'
    
    # Final check - ensure we have meaningful content
    if not resource_entry.get('content', '').strip() or len(resource_entry['content']) < 50:
        return None
    
    return resource_entry

def main():
    parser = argparse.ArgumentParser(
        description="Extract all study notes and resources from a Bible SCML file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bible_processor_cli.py LSB.scml
  python bible_processor_cli.py LSB.scml --output-dir ./output --progress
  python bible_processor_cli.py LSB.scml --no-progress --output-dir /path/to/output
        """
    )
    
    parser.add_argument(
        "input_file", 
        help="Path to the input SCML file (e.g., LSB.scml)"
    )
    
    parser.add_argument(
        "--output-dir", 
        default="./output",
        help="Directory where output files will be created (default: ./output)"
    )
    
    parser.add_argument(
        "--progress", 
        action="store_true", 
        default=True,
        help="Show progress during processing (default: enabled)"
    )
    
    parser.add_argument(
        "--no-progress", 
        action="store_true",
        help="Disable progress display"
    )
    
    args = parser.parse_args()
    
    # Handle progress flag logic
    show_progress = args.progress and not args.no_progress
    
    try:
        success = process_bible_scml(args.input_file, args.output_dir, show_progress)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 