#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import re
import os
import argparse
from io import StringIO

# Comprehensive mapping of book abbreviations to names and numbers
# (Same as in scml_to_json_converter.py)
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

def sanitize_name(name_raw):
    """Removes or replaces characters not suitable for filenames/directories."""
    if not name_raw:
        return "Unknown"
    
    name = name_raw
    # Specific prefixes to strip for cleaner folder/file names
    prefixes_to_strip = [
        "Study Notes and Features for ",
        "Translator's Notes and Cross-References for ",
        "Introduction to ",
        "The Book of "
    ]
    for prefix in prefixes_to_strip:
        if name.lower().startswith(prefix.lower()):
            name = name[len(prefix):].strip()
            break 
            
    # General sanitization for file system compatibility
    name = re.sub(r'[<>:"/\\|?*&]', '_', name)
    name = name.replace(' ', '_')
    name = re.sub(r'_+', '_', name) # Replace multiple underscores with one
    name = name.strip('_')
    return name if name else "Unknown"

def get_book_name_for_comparison(book_display_name_raw):
    """
    Extracts a comparable book name (e.g., "Exodus", "1 Samuel")
    from a display name which might include prefixes or chapter numbers.
    This name is used for matching against chapter semantics.
    """
    if not book_display_name_raw:
        return "UnknownBook"

    name = book_display_name_raw.strip()
    
    # Strip common prefixes first
    prefixes_to_strip = [
        "Study Notes and Features for ",
        "Translator's Notes and Cross-References for ",
        "Introduction to ",
        "The Book of "
    ]
    for prefix in prefixes_to_strip:
        if name.lower().startswith(prefix.lower()):
            name = name[len(prefix):].strip()
            break 

    # Try to extract the core book name (e.g., "Genesis" from "Genesis 1", "1 Samuel" from "1 Samuel 10")
    # This regex attempts to capture multi-word book names like "Song of Solomon" or "1 Samuel"
    # and ignore trailing chapter numbers or other details.
    match = re.match(r"([1-3]?\s*[A-Za-z]+(?: [A-Za-z]+)*)", name)
    if match:
        return match.group(1).strip()
    
    return name if name else "UnknownBook"

def get_book_details(book_abbr_input):
    """Get standardized book details from abbreviation."""
    # Normalize common variations like "Ps" vs "Pss"
    book_abbr_norm = book_abbr_input.title() # Capitalize first letter e.g. "ge" -> "Ge"
    if book_abbr_norm in BOOK_INFO:
        return BOOK_INFO[book_abbr_norm]
    # Try removing trailing 's' for plurals like Pss -> Ps
    if book_abbr_norm.endswith('s') and book_abbr_norm[:-1] in BOOK_INFO:
        return BOOK_INFO[book_abbr_norm[:-1]]
    # Try direct key match if title casing didn't work
    if book_abbr_input in BOOK_INFO:
        return BOOK_INFO[book_abbr_input]
        
    print(f"Warning: Book abbreviation '{book_abbr_input}' not found. Using it as is.")
    return {"name": book_abbr_input, "num": "00", "full_name": book_abbr_input} # Default/error

def ref_to_id_val(book_abbr, chap, verse):
    """Convert a book reference to a numeric ID."""
    details = get_book_details(book_abbr)
    try:
        return int(f"{details['num']}{int(chap):03d}{int(verse):03d}")
    except ValueError:
        print(f"Warning: Could not convert {book_abbr} {chap}:{verse} to ID.")
        return 0 # Or some other error indicator

def format_ref_for_display(book_abbr, chap_start, verse_start, chap_end=None, verse_end_or_range_end=None):
    """Format a reference for display."""
    details = get_book_details(book_abbr)
    book_name_disp = details['name']

    if chap_end and verse_end_or_range_end: # Book C1:V1–C2:V2
        return f"{book_name_disp} {chap_start}:{verse_start}–{chap_end}:{verse_end_or_range_end}"
    elif verse_end_or_range_end: # Book C1:V1–V2 (same chapter range)
        return f"{book_name_disp} {chap_start}:{verse_start}–{verse_end_or_range_end}"
    else: # Book C1:V1
        return f"{book_name_disp} {chap_start}:{verse_start}"

def format_ref_for_ref_attribute(book_abbr, chap_start, verse_start, chap_end=None, verse_end_or_range_end=None):
    """Format a reference for use in the ref attribute."""
    details = get_book_details(book_abbr)
    book_name_full = details.get('full_name', details['name']) # Use full_name, fallback to display name

    if chap_end and verse_end_or_range_end: # Book C1:V1–C2:V2
        return f"{book_name_full} {chap_start}:{verse_start}–{chap_end}:{verse_end_or_range_end}"
    elif verse_end_or_range_end: # Book C1:V1–V2 (same chapter range)
        return f"{book_name_full} {chap_start}:{verse_start}–{verse_end_or_range_end}"
    else: # Book C1:V1
        return f"{book_name_full} {chap_start}:{verse_start}"

def parse_ref_string(ref_str):
    """Parse a Bible reference string into components."""
    if not ref_str: return None, None, ref_str
    match = REF_PATTERN.match(ref_str.strip())
    if not match:
        # Fallback to using the string as is for display if it's not a standard ref.
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
    
    # Return value structure: (numeric_start_id_from_ref, numeric_end_id, display_string)
    # We return None for numeric_start_id_from_ref as the primary start ID comes from com_id.
    return None, end_id, display_ref

def serialize_element_content(element, is_top_com_element=False):
    """Convert XML element content to structured HTML-like string."""
    chunks = []
    
    # Text before the first child (element.text)
    if element.text:
        # For the top <com> element, its .text is usually None or whitespace if <bcv> is the first child.
        # We only add it if it's not the top element, or if it is the top and this text is not part of bcv handling.
        if not is_top_com_element or (is_top_com_element and not list(element)):
             chunks.append(element.text.strip())

    # Iterate over children
    bcv_skipped_for_top_node = False
    for child in element:
        # If this is the top <com> element, skip the first <bcv> tag's direct content processing here.
        # Its <xbr> is handled for the header. Its .tail is crucial for the body.
        if is_top_com_element and not bcv_skipped_for_top_node and child.tag == 'bcv':
            bcv_skipped_for_top_node = True
            if child.tail: # Text immediately after the skipped <bcv>
                chunks.append(child.tail.strip())
            continue # Move to the next child of <com> (if any)

        # Process the child element itself
        tag = child.tag
        if tag == 'b': # Handles <b type="b_blue"> and regular <b>
            chunks.append(f"<b>{serialize_element_content(child)}</b>") # is_top_com_element is False
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
                    # Use the function for the ref attribute string
                    ref_attribute_string = format_ref_for_ref_attribute(b_abbr, c_start, v_start, e_chap, e_verse_cv if e_verse_cv else e_verse_v)
                else: # t_attr is not a standard reference, use as is for ref
                    ref_attribute_string = t_attr
            
            link_display_text_final = ""
            if scml_text_content:
                link_display_text_final = scml_text_content
            elif t_attr: # Fallback if <xbr> tag was empty (e.g. <xbr t="..."/>)
                # parse_ref_string returns display_ref with abbreviated book names
                _, _, display_ref_for_empty_xbr = parse_ref_string(t_attr) 
                link_display_text_final = display_ref_for_empty_xbr if display_ref_for_empty_xbr else t_attr
            
            if t_attr: # If there was a t_attr, always include ref attribute
                # Basic escaping for attribute value if it ever contains quotes
                escaped_ref_attr = ref_attribute_string.replace("'", "&apos;").replace('"', "&quot;")
                chunks.append(f"<a ref=\'{escaped_ref_attr}\'>{link_display_text_final}</a>")
            else: # If no t_attr (unusual for xbr)
                chunks.append(f"<a>{link_display_text_final}</a>")
        # Add other specific tag handlers as needed
        else:
            # For unrecognized tags, recursively process their content
            chunks.append(serialize_element_content(child))

        # Text after the current child element (child.tail)
        if child.tail:
            chunks.append(child.tail.strip())
            
    # Filter out empty strings and join with spaces
    return " ".join(s for s in chunks if s and s.strip())

def convert_scml_notes_to_json(scml_content, json_file_path):
    """
    Convert study notes from SCML format to JSON.
    Takes in-memory SCML content and writes to specified JSON file.
    """
    notes = []
    try:
        # Wrap content with a root element for parsing
        scml_file_like_object = StringIO(f"<root>\n{scml_content}\n</root>")
        
        context = ET.iterparse(scml_file_like_object, events=('end',))
        
        for event, elem in context:
            if elem.tag == 'com':
                note_entry = {}
                com_id_full = elem.get('id')

                # Derive start_id from com_id (e.g., "com01001001" or "com01001004a")
                match_id = re.match(r"com(\d+)", com_id_full)
                if not match_id:
                    print(f"Warning: com_id format unexpected: {com_id_full}. Skipping this entry.")
                    elem.clear()
                    continue
                
                note_entry['start'] = int(match_id.group(1))

                header_html = ""
                # Process initial <bcv><xbr> for header and potential end_id
                bcv_tag = elem.find('bcv')
                if bcv_tag is not None:
                    xbr_in_bcv = bcv_tag.find('xbr')
                    if xbr_in_bcv is not None:
                        t_attr = xbr_in_bcv.get('t')
                        if t_attr:
                            _, parsed_end_id, display_ref_str = parse_ref_string(t_attr)
                            if display_ref_str:
                                header_html = f"<b><a>{display_ref_str}</a></b>"
                            if parsed_end_id and parsed_end_id != note_entry['start']: # Only add end if it's different
                                note_entry['end'] = parsed_end_id
                
                # Process the rest of the content of <com> tag
                main_body_html = serialize_element_content(elem, is_top_com_element=True)
                
                full_content = header_html
                if main_body_html:
                    if full_content: # Add a space if header exists and body exists
                        full_content += " "
                    full_content += main_body_html
                
                # Clean up whitespace
                note_entry['content'] = re.sub(r'\s+', ' ', full_content).strip()
                
                notes.append(note_entry)
                elem.clear() # Free memory

    except ET.ParseError as e:
        print(f"Error parsing SCML content: {e}")
        return False

    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        print(f"Conversion complete. Output at {json_file_path}")
        return True
    except IOError as e:
        print(f"Error writing JSON file: {e}")
        return False

def extract_resources(scml_content, json_file_path):
    """Extract resources like charts, maps, and other content from SCML."""
    resources = []
    
    try:
        # Wrap content with a root element for parsing
        scml_file_like_object = StringIO(f"<root>\n{scml_content}\n</root>")
        
        context = ET.iterparse(scml_file_like_object, events=('end',))
        
        # Resource-type elements to look for
        resource_tags = [
            'sbch',    # Study Bible chart
            'sbfig',   # Study Bible figure
            'inh',     # Introductory heading
            'chapter', # Chapter with semantic attributes (intros, etc.)
            'figure',  # Figure
            'toc1',    # Table of contents entries
            'in',      # Index entries
            'div'      # Division
        ]
        
        for event, elem in context:
            if elem.tag in resource_tags:
                resource_entry = {}
                resource_id = elem.get('id', '')
                
                if not resource_id and elem.tag == 'chapter':
                    # For chapters without IDs, generate one based on semantic
                    semantic = elem.get('semantic', '')
                    if semantic:
                        resource_id = f"ch_{sanitize_name(semantic)}"
                    else:
                        # Skip chapters without ID or semantic
                        elem.clear()
                        continue
                
                resource_entry['id'] = resource_id or f"resource_{len(resources)}"
                
                # Process title - check several possible title elements
                title_elem = (
                    elem.find('.//ctfm') or 
                    elem.find('.//ct') or 
                    elem.find('.//ah') or
                    elem.find('.//inh')
                )
                
                if title_elem is not None and title_elem.text:
                    resource_entry['title'] = title_elem.text.strip()
                elif elem.get('semantic'):
                    resource_entry['title'] = elem.get('semantic')
                else:
                    resource_entry['title'] = f"Resource {resource_entry['id']}"
                
                # Process content
                try:
                    content_html = serialize_element_content(elem)
                    resource_entry['content'] = re.sub(r'\s+', ' ', content_html).strip()
                except Exception as e:
                    print(f"Warning: Error processing content for resource {resource_entry['id']}: {e}")
                    resource_entry['content'] = f"Error processing content: {str(e)}"
                
                # Determine resource type based on tag and attributes
                if elem.tag == 'sbfig':
                    resource_entry['type'] = 'figure'
                elif elem.tag == 'sbch':
                    resource_entry['type'] = 'chart'
                elif elem.tag == 'chapter':
                    semantic = elem.get('semantic', '').lower()
                    if 'introduction' in semantic:
                        resource_entry['type'] = 'introduction'
                    elif 'notes' in semantic:
                        resource_entry['type'] = 'notes'
                    else:
                        resource_entry['type'] = 'chapter_content'
                elif elem.tag == 'figure':
                    resource_entry['type'] = 'figure'
                elif elem.tag == 'toc1':
                    resource_entry['type'] = 'toc_entry'
                elif elem.tag == 'in':
                    resource_entry['type'] = 'index_entry'
                elif elem.tag == 'inh':
                    resource_entry['type'] = 'heading'
                else:
                    resource_entry['type'] = 'other'
                
                # Only add resources with content
                if resource_entry.get('content') and resource_entry['content'].strip():
                    resources.append(resource_entry)
                
                elem.clear()  # Free memory
    
    except ET.ParseError as e:
        print(f"Error parsing SCML content for resources: {e}")
        return False
    
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(resources, f, ensure_ascii=False, indent=2)
        print(f"Resources extraction complete. Output at {json_file_path}")
        print(f"  - Extracted {len(resources)} resources")
        return True
    except IOError as e:
        print(f"Error writing resources JSON file: {e}")
        return False

def process_scml(input_file, output_dir_base):
    """Process an SCML file containing multiple Bible books."""
    if not os.path.exists(output_dir_base):
        os.makedirs(output_dir_base)

    print(f"Reading SCML file: {input_file}")

    # First, let's check for study notes across the entire file
    study_notes_by_book = {}  # Store study notes by book number
    
    try:
        # Read the file in chunks to avoid memory issues with large files
        with open(input_file, 'r', encoding='utf-8') as f:
            # First look for <com> elements across the entire file
            print("Scanning for study notes...")
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            total_notes = 0
            
            # Read the first chunk to get XML declaration
            first_chunk = f.read(chunk_size)
            xml_declaration = ""
            if first_chunk.startswith('<?xml'):
                xml_decl_end = first_chunk.find('?>')
                if xml_decl_end > 0:
                    xml_declaration = first_chunk[:xml_decl_end+2]
            
            # Reset file pointer
            f.seek(0)
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                # Find all <com> elements in this chunk
                com_matches = re.finditer(r'<com\s+id="(com\d+)"[^>]*>(.*?)(?=<com\s+id=|</com>)', chunk, re.DOTALL)
                for match in com_matches:
                    com_id = match.group(1)
                    partial_content = match.group(2)
                    
                    # Check if this is a complete <com> element or if it's cut off
                    if '</com>' in chunk[match.start():match.end() + 100]:  # Look a bit ahead for closing tag
                        # Extract the full content including the closing tag
                        end_pos = chunk.find('</com>', match.end())
                        if end_pos > 0:
                            full_content = chunk[match.start():end_pos + 6]  # +6 for '</com>'
                        else:
                            # Shouldn't happen given the check above, but just in case
                            full_content = f"<{com_id}>{partial_content}</com>"
                    else:
                        # It's cut off, so we'll use what we have
                        full_content = f"<{com_id}>{partial_content}</com>"
                    
                    # Extract book number from com_id
                    book_num_match = re.match(r'com(\d{2})\d+', com_id)
                    if book_num_match:
                        book_num = book_num_match.group(1)
                        if book_num not in study_notes_by_book:
                            study_notes_by_book[book_num] = []
                        study_notes_by_book[book_num].append((com_id, full_content))
                        total_notes += 1
            
            print(f"Found {total_notes} study notes across {len(study_notes_by_book)} books.")
            
            # Now process the file for book elements
            f.seek(0)
            content = f.read()
    
        # Extract book elements using regex
        print("Extracting book elements...")
        book_pattern = re.compile(r'<book[^>]*>.*?</book>', re.DOTALL)
        book_matches = book_pattern.findall(content)
        
        if not book_matches:
            # Try a more relaxed pattern for incomplete books
            print("No complete book elements found. Trying alternative extraction...")
            book_start_pattern = re.compile(r'<book[^>]*>.*?(?=<book|$)', re.DOTALL)
            book_matches = book_start_pattern.findall(content)
            
            if not book_matches:
                raise Exception("Could not extract any book content from the file.")
        
        print(f"Found {len(book_matches)} potential book sections.")
        
        # For each book match, try to extract the book name and process it
        processed_books = []
        for i, book_xml in enumerate(book_matches):
            try:
                # Wrap the book XML in a root element for parsing
                wrapped_xml = f"<root>{book_xml}</root>"
                book_element = ET.fromstring(wrapped_xml).find('book')
                
                if book_element is not None:
                    # Get the book's name and number
                    book_folder = process_bible_book(book_element, output_dir_base, study_notes_by_book)
                    processed_books.append(book_folder)
                else:
                    print(f"Warning: Could not parse book element {i+1}. Skipping.")
            except ET.ParseError as e:
                print(f"Warning: Parse error in book {i+1}: {e}")
                # Try a more manual approach for this book
                try:
                    # Extract potential book name using regex
                    book_name_match = re.search(r'<book[^>]*semantic="([^"]+)"', book_xml)
                    book_name = book_name_match.group(1) if book_name_match else f"UnknownBook_{i+1}"
                    
                    # Create a directory for this book
                    book_folder_sanitized = sanitize_name(book_name)
                    book_output_dir = os.path.join(output_dir_base, book_folder_sanitized)
                    if not os.path.exists(book_output_dir):
                        os.makedirs(book_output_dir)
                        
                    print(f"\nProcessing Book: '{book_name}' (using fallback method) -> Folder: '{book_folder_sanitized}'")
                    
                    # Try to determine book number for study notes
                    book_num = None
                    for abbr, details in BOOK_INFO.items():
                        if details.get('full_name', '').lower() == book_name.lower():
                            book_num = details.get('num')
                            break
                    
                    # If we found study notes for this book, process them
                    if book_num and book_num in study_notes_by_book:
                        notes = []
                        for com_id, com_content in study_notes_by_book[book_num]:
                            try:
                                # Simplistic note extraction
                                note_id_match = re.match(r'com(\d+)', com_id)
                                if note_id_match:
                                    note_id = int(note_id_match.group(1))
                                    
                                    # Extract reference and content
                                    ref_match = re.search(r'<bcv[^>]*>.*?<xbr[^>]*>(.*?)</xbr>', com_content, re.DOTALL)
                                    ref_display = ref_match.group(1).strip() if ref_match else f"Reference {note_id}"
                                    
                                    # Create a simple note
                                    note_entry = {
                                        "start": note_id,
                                        "content": f"<b><a>{ref_display}</a></b> {com_content}"
                                    }
                                    notes.append(note_entry)
                            except Exception as e:
                                print(f"Error processing study note {com_id}: {e}")
                        
                        # Write notes to JSON file
                        if notes:
                            notes_json_path = os.path.join(book_output_dir, 'notes.json')
                            with open(notes_json_path, 'w', encoding='utf-8') as f:
                                json.dump(notes, f, ensure_ascii=False, indent=2)
                            print(f"Study notes extraction complete. {len(notes)} notes written to {notes_json_path}")
                    else:
                        # Create empty notes file
                        notes_json_path = os.path.join(book_output_dir, 'notes.json')
                        with open(notes_json_path, 'w', encoding='utf-8') as f:
                            json.dump([], f, ensure_ascii=False, indent=2)
                        print(f"No study notes found. Created empty notes.json file at {notes_json_path}")
                    
                    # Create empty resources file
                    resources_json_path = os.path.join(book_output_dir, 'resources.json')
                    with open(resources_json_path, 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=2)
                    print(f"Created empty resources.json file at {resources_json_path}")
                    
                    processed_books.append(book_folder_sanitized)
                except Exception as e:
                    print(f"Error in fallback processing for book {i+1}: {e}")
        
        if not processed_books:
            raise Exception("No books could be processed.")
            
        print(f"\nProcessing complete. Processed {len(processed_books)} book(s):")
        for book in processed_books:
            print(f"  - {book}")
    
    except Exception as e:
        print(f"Error: Failed to process SCML file '{input_file}': {e}")
        return

def process_bible_book(book_element, output_dir_base, study_notes_by_book=None):
    """Process a single Bible book, extracting notes and resources."""
    raw_book_semantic_name = book_element.get('semantic')
    book_id_attr = book_element.get('id')

    # Determine the primary name for the book (used for folder name)
    book_name_for_folder = raw_book_semantic_name
    if not book_name_for_folder:
        # Try finding <bk> tag
        bk_tag = book_element.find('bk')
        if bk_tag is not None and bk_tag.text:
            book_name_for_folder = bk_tag.text.strip()
        # Try finding book name from chapter IDs (e.g., "ch01001" -> Genesis)
        elif not book_name_for_folder:
            for chapter in book_element.findall('.//chapter'):
                chapter_id = chapter.get('id', '')
                if chapter_id.startswith('ch'):
                    # Extract the book number from chapter ID if it follows the pattern chXX...
                    match = re.match(r'ch(\d{2})\d+', chapter_id)
                    if match:
                        book_num = match.group(1)
                        # Find book by number
                        for abbr, details in BOOK_INFO.items():
                            if details.get('num') == book_num:
                                book_name_for_folder = details.get('full_name', abbr)
                                print(f"Identified book as '{book_name_for_folder}' from chapter ID pattern.")
                                break
                        if book_name_for_folder:
                            break
        
        # Try checking toc1 entries which often contain book names
        if not book_name_for_folder:
            toc1_elem = book_element.find('.//toc1')
            if toc1_elem is not None:
                toc1_id = toc1_elem.get('id', '')
                # toc1 IDs often follow pattern like "rbk01" where 01 is the book number
                match = re.match(r'rbk(\d{2})', toc1_id)
                if match:
                    book_num = match.group(1)
                    for abbr, details in BOOK_INFO.items():
                        if details.get('num') == book_num:
                            book_name_for_folder = details.get('full_name', abbr)
                            print(f"Identified book as '{book_name_for_folder}' from toc1 ID.")
                            break
        
        # Try looking for book reference in chapter semantic attributes
        if not book_name_for_folder:
            for chapter in book_element.findall('.//chapter'):
                chapter_semantic = chapter.get('semantic', '')
                # Try to extract book name from chapter semantic
                for abbr, details in BOOK_INFO.items():
                    full_name = details.get('full_name', '')
                    if full_name and full_name.lower() in chapter_semantic.lower():
                        book_name_for_folder = full_name
                        print(f"Identified book as '{book_name_for_folder}' from chapter semantic attribute.")
                        break
                if book_name_for_folder:
                    break
        
        # Fallback to ID or default
        if not book_name_for_folder and book_id_attr:
            book_name_for_folder = book_id_attr
        else:
            book_name_for_folder = book_name_for_folder or "UnknownBook"
            if book_name_for_folder == "UnknownBook":
                print(f"Warning: Could not determine a name for a book element. Using default '{book_name_for_folder}'.")
    
    # Sanitize name for folder creation
    book_folder_sanitized = sanitize_name(book_name_for_folder)
    
    # Get clean book name for semantic comparisons
    name_to_compare_chapters_against = get_book_name_for_comparison(
        raw_book_semantic_name if raw_book_semantic_name else book_name_for_folder
    )

    # Create book directory
    book_output_dir = os.path.join(output_dir_base, book_folder_sanitized)
    if not os.path.exists(book_output_dir):
        os.makedirs(book_output_dir)
    
    print(f"\nProcessing Book: '{book_name_for_folder}' (Comparison Name: '{name_to_compare_chapters_against}') -> Folder: '{book_folder_sanitized}'")

    # Collect resources (we'll do this regardless of how notes are processed)
    other_resources_elements = []
    
    # Process direct children of <book> that are not <chapter>
    for child_element in book_element:
        if child_element.tag.lower() != 'chapter':
            other_resources_elements.append(child_element)

    # Process chapters to find resources
    for chapter in book_element.findall('chapter'):
        chapter_id = chapter.get('id', '').lower()
        chapter_semantic = chapter.get('semantic', '')

        is_bible_text_chapter = False
        if chapter_id.startswith("ch"):
            bible_pattern = rf"^{re.escape(name_to_compare_chapters_against)}\s+\d+$"
            if re.match(bible_pattern, chapter_semantic, re.IGNORECASE):
                is_bible_text_chapter = True
        
        # Skip Bible text chapters, add others as resources
        if not is_bible_text_chapter:
            other_resources_elements.append(chapter)

    # Get book number from our mapping
    book_num = None
    for abbr, details in BOOK_INFO.items():
        if details.get('full_name', '').lower() == book_name_for_folder.lower():
            book_num = details.get('num')
            break
    
    # Process study notes if we have them pre-extracted
    notes_found = False
    if study_notes_by_book and book_num and book_num in study_notes_by_book:
        print(f"Processing {len(study_notes_by_book[book_num])} pre-extracted study notes for {book_name_for_folder}.")
        
        notes = []
        for com_id, com_content in study_notes_by_book[book_num]:
            try:
                # Create note entry
                note_entry = {}
                match_id = re.match(r'com(\d+)', com_id)
                if match_id:
                    note_entry['start'] = int(match_id.group(1))
                    
                    # Try to parse content and extract reference
                    bcv_match = re.search(r'<bcv[^>]*>.*?<xbr\s+t="([^"]+)"[^>]*>(.*?)</xbr>', com_content, re.DOTALL)
                    
                    header_html = ""
                    if bcv_match:
                        ref_str = bcv_match.group(1)
                        ref_display = bcv_match.group(2) if bcv_match.group(2).strip() else None
                        
                        _, parsed_end_id, display_ref_str = parse_ref_string(ref_str)
                        
                        if ref_display:
                            header_html = f"<b><a>{ref_display}</a></b>"
                        elif display_ref_str:
                            header_html = f"<b><a>{display_ref_str}</a></b>"
                            
                        if parsed_end_id and parsed_end_id != note_entry['start']:
                            note_entry['end'] = parsed_end_id
                    
                    # Process the rest of the content, looking for <b> tags and other formatted content
                    # First remove the <bcv> part since we've already processed it
                    main_content = re.sub(r'<bcv>.*?</bcv>', '', com_content, flags=re.DOTALL).strip()
                    
                    # Extract bold sections
                    bold_sections = []
                    for b_match in re.finditer(r'<b(?:\s+type="[^"]*")?\s*>(.*?)</b>', main_content, re.DOTALL):
                        bold_text = b_match.group(1).strip()
                        if bold_text:
                            bold_sections.append(f"<b>{bold_text}</b>")
                    
                    # Get all text and preserve specific formatting
                    text_content = re.sub(r'<[^>]+>', ' ', main_content)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    
                    # Add bold sections back if found
                    if bold_sections:
                        bold_content = " ".join(bold_sections)
                        text_content = f"{bold_content} {text_content}"
                    
                    # Combine header and content
                    if header_html:
                        if text_content:
                            full_content = f"{header_html} {text_content}"
                        else:
                            full_content = header_html
                    else:
                        full_content = text_content
                    
                    note_entry['content'] = full_content.strip()
                    
                    if note_entry['content'].strip():
                        notes.append(note_entry)
            except Exception as e:
                print(f"Error processing study note {com_id}: {e}")
        
        if notes:
            notes_json_path = os.path.join(book_output_dir, 'notes.json')
            with open(notes_json_path, 'w', encoding='utf-8') as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)
            print(f"Study notes extraction complete. {len(notes)} notes written to {notes_json_path}")
            notes_found = True
    
    # If no notes found through pre-extraction, try to extract from the book element
    if not notes_found:
        # Collect study notes
        study_notes_elements = []
        study_notes_chapters = []
        
        # Re-evaluate chapters specifically for notes
        for chapter in book_element.findall('chapter'):
            chapter_semantic = chapter.get('semantic', '')

            is_study_notes_chapter = chapter_semantic.lower().startswith("study notes and features for") and \
                                   name_to_compare_chapters_against.lower() in chapter_semantic.lower()
            
            # Identify potential note-like chapters
            is_note_like = False
            if not is_study_notes_chapter:
                if chapter_semantic.lower().startswith(name_to_compare_chapters_against.lower()):
                    if "notes" in chapter_semantic.lower() or "commentary" in chapter_semantic.lower():
                        is_note_like = True
                elif "notes" in chapter_semantic.lower() and name_to_compare_chapters_against.lower() in chapter_semantic.lower():
                    is_note_like = True
            
            # Add to appropriate collection
            if is_study_notes_chapter:
                study_notes_elements.append(chapter)
            elif is_note_like:
                study_notes_chapters.append(chapter)
        
        # Process study notes chapters
        if study_notes_elements:
            notes_content = "\n".join(ET.tostring(elem, encoding='unicode') for elem in study_notes_elements)
            notes_json_path = os.path.join(book_output_dir, 'notes.json')
            if convert_scml_notes_to_json(notes_content, notes_json_path):
                notes_found = True
        
        # If no study notes found yet, try to extract from note-like chapters
        if not notes_found and study_notes_chapters:
            print(f"No standard study notes found. Extracting notes from {len(study_notes_chapters)} note-like chapters...")
            
            notes = []
            for i, chapter in enumerate(study_notes_chapters):
                try:
                    chapter_id = chapter.get('id', f"note_chapter_{i+1}")
                    chapter_semantic = chapter.get('semantic', 'Note')
                    
                    # Get chapter content as text
                    chapter_content = ET.tostring(chapter, encoding='unicode')
                    
                    # Try to find verse references in the content
                    ref_pattern = re.compile(r'<xbr\s+t="([^"]+)"[^>]*>(.*?)</xbr>', re.DOTALL)
                    ref_matches = ref_pattern.findall(chapter_content)
                    
                    if ref_matches:
                        # Process each reference found
                        for ref_t_attr, ref_content in ref_matches:
                            try:
                                # Parse the reference
                                _, parsed_end_id, display_ref_str = parse_ref_string(ref_t_attr)
                                
                                # Create a note ID based on the book number and a sequence
                                note_id = 0
                                if book_num:
                                    # Create a simple ID in format XXYYYZZZZ where XX is book number
                                    # and the rest is just to make it unique
                                    note_id = int(f"{book_num}9{i+1:02d}{len(notes)+1:03d}")
                                else:
                                    # Fallback ID
                                    note_id = 999000000 + (i+1)*1000 + len(notes)+1
                                
                                # Create note entry
                                note_entry = {
                                    "start": note_id,
                                    "content": f"<b><a>{display_ref_str}</a></b> {ref_content}"
                                }
                                
                                # Add end ID if applicable
                                if parsed_end_id and parsed_end_id != note_id:
                                    note_entry['end'] = parsed_end_id
                                
                                notes.append(note_entry)
                            except Exception as e:
                                print(f"Error processing reference: {e}")
                    else:
                        # No references found, create a single note for the whole chapter
                        note_id = 0
                        if book_num:
                            note_id = int(f"{book_num}9{i+1:02d}001")
                        else:
                            note_id = 999000000 + (i+1)*1000 + 1
                        
                        # Extract text content
                        text_content = re.sub(r'<[^>]+>', ' ', chapter_content)
                        text_content = re.sub(r'\s+', ' ', text_content).strip()
                        
                        # Create note entry
                        note_entry = {
                            "start": note_id,
                            "content": f"<b>{chapter_semantic}</b> {text_content}"
                        }
                        
                        notes.append(note_entry)
                except Exception as e:
                    print(f"Error processing note-like chapter: {e}")
            
            if notes:
                notes_json_path = os.path.join(book_output_dir, 'notes.json')
                with open(notes_json_path, 'w', encoding='utf-8') as f:
                    json.dump(notes, f, ensure_ascii=False, indent=2)
                print(f"Alternative notes extraction complete. {len(notes)} notes written to {notes_json_path}")
                notes_found = True
    
    # If still no notes found, create an empty notes file
    if not notes_found:
        notes_json_path = os.path.join(book_output_dir, 'notes.json')
        with open(notes_json_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print(f"No study notes found. Created empty notes.json file at {notes_json_path}")
    
    # Extract resources to JSON
    if other_resources_elements:
        resources_content = "\n".join(ET.tostring(elem, encoding='unicode') for elem in other_resources_elements)
        resources_json_path = os.path.join(book_output_dir, 'resources.json')
        extract_resources(resources_content, resources_json_path)
    else:
        # Create empty resources file
        resources_json_path = os.path.join(book_output_dir, 'resources.json')
        with open(resources_json_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print(f"No resources found. Created empty resources.json file at {resources_json_path}")
    
    return book_folder_sanitized

def main():
    parser = argparse.ArgumentParser(description="Extract Bible books from SCML and convert to notes.json and resources.json files.")
    parser.add_argument("input_scml_file", help="Path to the input SCML file.")
    parser.add_argument("output_directory", help="Path to the directory where output folders and files will be created.")
    
    args = parser.parse_args()
    
    process_scml(args.input_scml_file, args.output_directory)

if __name__ == "__main__":
    main() 