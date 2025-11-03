#!/usr/bin/env python3
"""
Study Notes CLI Tool

Processes SCML files for Bible translations and extracts study notes and resources.
Outputs JSON files per translation in the format specified in PLAN.md.

Usage:
    python3 study_notes_cli.py --translation ESV
    python3 study_notes_cli.py --all
    python3 study_notes_cli.py --translation ESV --inputs-dir ./inputs --output-dir ./output
"""

import xml.etree.ElementTree as ET
import json
import re
import os
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Set

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

# Decorative images to ignore
DECORATIVE_IMAGES = {
    'hcp-rule.jpg', 'ctorntop.jpg', 'ctornbottom.jpg', 'csorn.jpg',
    'hcp-logo.jpg', 'hcp-esvlogo.jpg'
}


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


def slugify(text):
    """Generate a URL-friendly slug from text."""
    if not text:
        return "unknown"
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


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
        if tag == 'b' or tag == 'bi':
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
        elif tag in ['p', 'para', 'pf', 'pcon']:
            # Paragraphs - serialize content and add newline equivalent
            para_content = serialize_element_content(child)
            if para_content:
                chunks.append(para_content)
        elif tag in ['list', 'ul', 'ol']:
            # Lists - serialize items
            for item in child.findall('.//bl') + child.findall('.//blf') + child.findall('.//bll') + child.findall('.//li'):
                item_content = serialize_element_content(item)
                if item_content:
                    chunks.append(f"• {item_content}")
        elif tag == 'table':
            # Tables - serialize rows and cells
            for row in child.findall('.//tr') + child.findall('.//row'):
                row_chunks = []
                for cell in row.findall('.//cell') + row.findall('.//td') + row.findall('.//tdnl') + row.findall('.//tdul'):
                    cell_content = serialize_element_content(cell)
                    if cell_content:
                        row_chunks.append(cell_content)
                if row_chunks:
                    chunks.append(" | ".join(row_chunks))
        elif tag in ['h1', 'h2', 'h3', 'ah', 'inh', 'ctfm']:
            # Headings - serialize and include
            heading_content = serialize_element_content(child)
            if heading_content:
                chunks.append(heading_content)
        else:
            # For unrecognized tags, recursively process their content
            chunks.append(serialize_element_content(child))

        if child.tail:
            chunks.append(child.tail.strip())
            
    return " ".join(s for s in chunks if s and s.strip())


def process_translation(translation: str, inputs_dir: str, output_dir: str, 
                       copy_all_images: bool, strict_images: bool, show_progress: bool) -> bool:
    """Process a single translation's SCML file."""
    scml_path = os.path.join(inputs_dir, translation, f"{translation}.scml")
    images_src_dir = os.path.join(inputs_dir, translation, f"{translation}_images")
    out_dir = os.path.join(output_dir, translation)
    out_images_dir = os.path.join(out_dir, "images")
    
    if not os.path.exists(scml_path):
        print(f"Error: SCML file not found: {scml_path}")
        return False
    
    if show_progress:
        print(f"\nProcessing {translation}...")
        print(f"  SCML: {scml_path}")
        print(f"  Images source: {images_src_dir}")
        print(f"  Output: {out_dir}")
    
    # Create output directories
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(out_images_dir, exist_ok=True)
    
    # Collections for notes and resources
    notes = []
    resources = []
    referenced_images: Set[str] = set()
    
    # Track parent context for chapters
    current_division_id = None
    
    # Stream parse the SCML file
    try:
        context = ET.iterparse(scml_path, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'division':
                    current_division_id = elem.get('id', '').lower()
            
            elif event == 'end':
                if elem.tag == 'com':
                    note = process_study_note(elem)
                    if note:
                        notes.append(note)
                    elem.clear()
                
                elif elem.tag == 'sidebar':
                    sidebar_resources = process_sidebar(elem, referenced_images)
                    resources.extend(sidebar_resources)
                    elem.clear()
                
                elif elem.tag == 'chapter':
                    chapter_resource = process_chapter_resource(elem, current_division_id)
                    if chapter_resource:
                        resources.append(chapter_resource)
                    elem.clear()
                
                # Clear root and other large elements to save memory
                if elem.tag == 'division':
                    elem.clear()
                    current_division_id = None
                elif elem.tag == 'book':
                    elem.clear()
    
    except ET.ParseError as e:
        print(f"Error parsing SCML file: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error processing {translation}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Sort notes by start
    notes.sort(key=lambda x: x.get('start', 0))
    
    # Write JSON files
    notes_file = os.path.join(out_dir, 'notes.json')
    resources_file = os.path.join(out_dir, 'resources.json')
    
    try:
        with open(notes_file, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        
        with open(resources_file, 'w', encoding='utf-8') as f:
            json.dump(resources, f, ensure_ascii=False, indent=2)
        
        if show_progress:
            print(f"  ✓ Notes: {len(notes)} entries")
            print(f"  ✓ Resources: {len(resources)} entries")
    
    except IOError as e:
        print(f"Error writing JSON files: {e}")
        return False
    
    # Copy images
    if copy_all_images:
        if os.path.exists(images_src_dir):
            try:
                # Copy entire directory
                if os.path.exists(out_images_dir):
                    shutil.rmtree(out_images_dir)
                shutil.copytree(images_src_dir, out_images_dir)
                image_count = len(list(Path(out_images_dir).glob('*.jpg')))
                if show_progress:
                    print(f"  ✓ Images copied: {image_count} files")
            except Exception as e:
                print(f"Error copying images: {e}")
                return False
        else:
            if strict_images:
                print(f"Error: Images directory not found: {images_src_dir}")
                return False
            elif show_progress:
                print(f"  Warning: Images directory not found: {images_src_dir}")
    else:
        # Copy only referenced images
        if os.path.exists(images_src_dir):
            copied_count = 0
            missing_count = 0
            for img_filename in referenced_images:
                src_path = os.path.join(images_src_dir, img_filename)
                dst_path = os.path.join(out_images_dir, img_filename)
                if os.path.exists(src_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        copied_count += 1
                    except Exception as e:
                        print(f"Error copying {img_filename}: {e}")
                else:
                    missing_count += 1
                    if strict_images:
                        print(f"Error: Referenced image not found: {src_path}")
                        return False
                    elif show_progress:
                        print(f"  Warning: Referenced image not found: {src_path}")
            
            if show_progress:
                print(f"  ✓ Images copied: {copied_count} files")
                if missing_count > 0:
                    print(f"  Warning: {missing_count} referenced images not found")
        else:
            if strict_images:
                print(f"Error: Images directory not found: {images_src_dir}")
                return False
    
    if show_progress:
        print(f"  ✓ Complete: {out_dir}")
    
    return True


def process_study_note(com_element) -> Optional[Dict]:
    """Process a <com> element into a study note."""
    com_id_full = com_element.get('id')
    
    if not com_id_full:
        return None
    
    # Extract start ID from com_id (e.g., "com01001001" or "com01001004a")
    match_id = re.match(r"com(\d+)", com_id_full)
    if not match_id:
        return None
    
    start_id = int(match_id.group(1))
    end_id = None
    
    header_html = ""
    # Process initial <bcv><xbr> for header and potential end_id
    bcv_tag = com_element.find('bcv')
    if bcv_tag is not None:
        xbr_in_bcv = bcv_tag.find('xbr')
        if xbr_in_bcv is not None:
            t_attr = xbr_in_bcv.get('t')
            display_text = xbr_in_bcv.text.strip() if xbr_in_bcv.text else None
            
            if t_attr:
                _, parsed_end_id, display_ref_str = parse_ref_string(t_attr)
                
                # Prefer display text from xbr, fallback to parsed display
                if display_text:
                    header_html = f"<b><a>{display_text}</a></b>"
                elif display_ref_str:
                    header_html = f"<b><a>{display_ref_str}</a></b>"
                
                if parsed_end_id and parsed_end_id != start_id:
                    end_id = parsed_end_id
    
    # Process the rest of the content (excluding bcv)
    main_body_html = serialize_element_content(com_element, is_top_com_element=True)
    
    full_content = header_html
    if main_body_html:
        if full_content:
            full_content += " "
        full_content += main_body_html
    
    # Clean up whitespace
    content = re.sub(r'\s+', ' ', full_content).strip()
    
    if not content:
        return None
    
    note_entry = {'start': start_id}
    if end_id:
        note_entry['end'] = end_id
    note_entry['content'] = content
    
    return note_entry


def process_sidebar(sidebar_element, referenced_images: Set[str]) -> List[Dict]:
    """Process a <sidebar> element into resource entries."""
    sidebar_id = sidebar_element.get('id', '')
    
    if not sidebar_id:
        return []
    
    # Determine type from id prefix
    resource_type = None
    if sidebar_id.startswith('sbc'):
        resource_type = 'chart'
    elif sidebar_id.startswith('sbm'):
        resource_type = 'figure'
    else:
        # Not a recognized sidebar type
        return []
    
    # Extract title
    title = None
    figh_elem = sidebar_element.find('.//figh')
    if figh_elem is not None:
        xref_elem = figh_elem.find('.//xref')
        if xref_elem is not None and xref_elem.text:
            title = xref_elem.text.strip()
    
    if not title:
        th_elem = sidebar_element.find('.//th')
        if th_elem is not None:
            xref_elem = th_elem.find('.//xref')
            if xref_elem is not None and xref_elem.text:
                title = xref_elem.text.strip()
    
    if not title:
        title = sidebar_id
    
    # Find content images
    content_images = []
    for figure in sidebar_element.findall('.//figure'):
        for fig in figure.findall('.//fig'):
            for img in fig.findall('.//img'):
                src = img.get('src', '')
                if src.startswith('images/'):
                    img_filename = os.path.basename(src)
                    # Check if it's a decorative image
                    if img_filename not in DECORATIVE_IMAGES:
                        # Include all non-decorative images
                        # Prefer those with fig/map in name, but don't exclude others
                        content_images.append(img_filename)
                        referenced_images.add(img_filename)
    
    # Build content (excluding decorative images)
    content = serialize_element_content(sidebar_element)
    content = re.sub(r'\s+', ' ', content).strip()
    
    if not content:
        content = title  # Fallback to title if no content
    
    # Emit one resource per image, or one text-only resource if no images
    resources = []
    if content_images:
        for img_filename in content_images:
            resources.append({
                'id': img_filename,
                'title': title,
                'content': content,
                'type': resource_type
            })
    else:
        # Text-only resource - generate ID from title
        resource_id = slugify(title)
        resources.append({
            'id': resource_id,
            'title': title,
            'content': content,
            'type': resource_type
        })
    
    return resources


def process_chapter_resource(chapter_element, division_id: Optional[str] = None) -> Optional[Dict]:
    """Process a <chapter> element that might be a resource (introduction/article)."""
    chapter_semantic = chapter_element.get('semantic', '').lower()
    chapter_id = chapter_element.get('id', '').lower()
    
    # Check if this is a Bible text chapter (exclude)
    if chapter_id.startswith('ch') and re.match(r'^[a-z0-9\s]+\s+\d+$', chapter_semantic):
        return None
    
    # Check if this is a study resource chapter
    resource_keywords = ['introduction', 'article', 'how to', 'overview', 'chronology']
    is_resource = any(keyword in chapter_semantic for keyword in resource_keywords)
    
    # Also check if it's in front/back matter divisions
    if division_id and division_id in ['fm', 'bm']:  # front matter or back matter
        is_resource = True
    
    if not is_resource:
        return None
    
    # Extract title
    title = None
    for title_tag in ['ctfm', 'ah', 'inh']:
        title_elem = chapter_element.find(f'.//{title_tag}')
        if title_elem is not None and title_elem.text:
            title = title_elem.text.strip()
            break
    
    if not title:
        h1_elem = chapter_element.find('.//h1')
        if h1_elem is not None and h1_elem.text:
            title = h1_elem.text.strip()
    
    if not title:
        h2_elem = chapter_element.find('.//h2')
        if h2_elem is not None and h2_elem.text:
            title = h2_elem.text.strip()
    
    if not title:
        title = chapter_element.get('semantic', '')
    
    if not title:
        return None
    
    # Build content
    content = serialize_element_content(chapter_element)
    content = re.sub(r'\s+', ' ', content).strip()
    
    if not content or len(content) < 50:
        return None
    
    # Determine type
    if 'introduction' in chapter_semantic:
        resource_type = 'introduction'
    else:
        resource_type = 'article'
    
    # Generate ID from title
    resource_id = slugify(title)
    
    return {
        'id': resource_id,
        'title': title,
        'content': content,
        'type': resource_type
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract study notes and resources from Bible SCML files",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--inputs-dir',
        default='./inputs',
        help='Directory containing translation subdirectories (default: ./inputs)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Directory for output files (default: ./output)'
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--translation',
        help='Process a single translation (e.g., ESV, LSB, NASB, NKJV)'
    )
    group.add_argument(
        '--all',
        action='store_true',
        help='Process all translations found in inputs directory'
    )
    
    parser.add_argument(
        '--copy-all-images',
        action='store_true',
        default=True,
        help='Copy entire images folder (default: enabled)'
    )
    
    parser.add_argument(
        '--only-referenced-images',
        action='store_true',
        help='Copy only images referenced by resources (overrides --copy-all-images)'
    )
    
    parser.add_argument(
        '--strict-images',
        action='store_true',
        help='Fail if referenced images are missing'
    )
    
    parser.add_argument(
        '--progress',
        action='store_true',
        default=True,
        help='Show progress messages (default: enabled)'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress messages'
    )
    
    args = parser.parse_args()
    
    show_progress = args.progress and not args.no_progress
    copy_all_images = args.copy_all_images and not args.only_referenced_images
    
    # Determine which translations to process
    translations_to_process = []
    
    if args.translation:
        translations_to_process = [args.translation]
    elif args.all:
        # Find all SCML files in inputs directory
        inputs_path = Path(args.inputs_dir)
        if not inputs_path.exists():
            print(f"Error: Inputs directory not found: {args.inputs_dir}")
            return 1
        
        for subdir in inputs_path.iterdir():
            if subdir.is_dir():
                scml_file = subdir / f"{subdir.name}.scml"
                if scml_file.exists():
                    translations_to_process.append(subdir.name)
        
        if not translations_to_process:
            print(f"Error: No SCML files found in {args.inputs_dir}")
            return 1
    
    if show_progress:
        print(f"Processing {len(translations_to_process)} translation(s): {', '.join(translations_to_process)}")
    
    # Process each translation
    success_count = 0
    for translation in translations_to_process:
        success = process_translation(
            translation, args.inputs_dir, args.output_dir,
            copy_all_images, args.strict_images, show_progress
        )
        if success:
            success_count += 1
    
    if show_progress:
        print(f"\n✓ Processed {success_count}/{len(translations_to_process)} translation(s) successfully")
    
    return 0 if success_count == len(translations_to_process) else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

