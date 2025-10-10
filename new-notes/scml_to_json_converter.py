import xml.etree.ElementTree as ET
import json
import re
import os
from io import StringIO # Added for wrapping content

# Comprehensive mapping of book abbreviations to names and numbers
# (Commonly used abbreviations as keys, mapping to a canonical name and standard 2-digit number)
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

# Regex to capture book, chapter, verse, and optional end chapter/verse
REF_PATTERN = re.compile(
    r"([1-3]?[A-Za-z]+)\s*(\d+):(\d+)"  # Book C:V (Group 1,2,3)
    r"(?:(?:–|-)(\d+):(\d+)|(?:–|-)(\d+))?"  # Optional -C:V (Group 4,5) or -V (Group 6)
)

def get_book_details(book_abbr_input):
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
    return {"name": book_abbr_input, "num": "00"} # Default/error

def ref_to_id_val(book_abbr, chap, verse):
    details = get_book_details(book_abbr)
    try:
        return int(f"{details['num']}{int(chap):03d}{int(verse):03d}")
    except ValueError:
        print(f"Warning: Could not convert {book_abbr} {chap}:{verse} to ID.")
        return 0 # Or some other error indicator

def format_ref_for_display(book_abbr, chap_start, verse_start, chap_end=None, verse_end_or_range_end=None):
    details = get_book_details(book_abbr)
    book_name_disp = details['name']

    if chap_end and verse_end_or_range_end: # Book C1:V1–C2:V2
        return f"{book_name_disp} {chap_start}:{verse_start}–{chap_end}:{verse_end_or_range_end}"
    elif verse_end_or_range_end: # Book C1:V1–V2 (same chapter range)
        return f"{book_name_disp} {chap_start}:{verse_start}–{verse_end_or_range_end}"
    else: # Book C1:V1
        return f"{book_name_disp} {chap_start}:{verse_start}"

def format_ref_for_ref_attribute(book_abbr, chap_start, verse_start, chap_end=None, verse_end_or_range_end=None):
    details = get_book_details(book_abbr)
    book_name_full = details.get('full_name', details['name']) # Use full_name, fallback to display name

    if chap_end and verse_end_or_range_end: # Book C1:V1–C2:V2
        return f"{book_name_full} {chap_start}:{verse_start}–{chap_end}:{verse_end_or_range_end}"
    elif verse_end_or_range_end: # Book C1:V1–V2 (same chapter range)
        return f"{book_name_full} {chap_start}:{verse_start}–{verse_end_or_range_end}"
    else: # Book C1:V1
        return f"{book_name_full} {chap_start}:{verse_start}"

def parse_ref_string(ref_str):
    if not ref_str: return None, None, ref_str
    match = REF_PATTERN.match(ref_str.strip())
    if not match:
        # print(f"Warning: Could not parse reference string: '{ref_str}'")
        # Fallback to using the string as is for display if it's not a standard ref.
        return None, None, ref_str

    book_abbr = match.group(1)
    chap_start = match.group(2)
    verse_start = match.group(3)
    
    end_chap_specific = match.group(4)
    end_verse_specific = match.group(5)
    end_verse_range_same_chap = match.group(6)

    # Calculate numeric start_id (not strictly needed here as com_id provides it, but good for validation)
    # parsed_start_id = ref_to_id_val(book_abbr, chap_start, verse_start)
    
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
    chunks = []
    
    # Text before the first child (element.text)
    if element.text:
        # For the top <com> element, its .text is usually None or whitespace if <bcv> is the first child.
        # We only add it if it's not the top element, or if it is the top and this text is not part of bcv handling.
        # This logic is tricky; simpler to let child.tail and iteration handle most text.
        # Let's only add .text for non-top elements, or for top elements if it's the *only* content.
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
        
        # If we are at the top <com> node, and this is the first child *after* any <bcv> handling,
        # we might need to capture `element.text` if it wasn't captured yet and applies here.
        # This can be complex. For now, rely on child.tail for inter-element text.
        # If this is the first child element (child_idx == 0) for a non-top element, its parent's .text was added.


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
                    # Use the new function for the ref attribute string
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
        # Add other specific tag handlers here if needed (e.g., <p>, <br>)
        # elif tag == 'br':
        #    chunks.append("<br/>")
        else:
            # For unrecognized tags, recursively call to process their content.
            # This effectively flattens unknown tags, keeping their text and any known nested tags.
            chunks.append(serialize_element_content(child))

        # Text after the current child element (child.tail)
        if child.tail:
            chunks.append(child.tail.strip())
            
    # Filter out empty strings and join with spaces.
    return " ".join(s for s in chunks if s and s.strip())


def convert_scml_to_json(scml_file_path, json_file_path):
    notes = []
    try:
        # Read the SCML file content
        with open(scml_file_path, 'r', encoding='utf-8') as f:
            scml_content_lines = f.readlines()

        # Wrap content with a single <root> element to handle multiple top-level elements
        # and preserve XML declaration if present.
        processed_lines = []
        xml_declaration = None
        if scml_content_lines and scml_content_lines[0].strip().startswith("<?xml"):
            xml_declaration = scml_content_lines[0]
            scml_content_lines = scml_content_lines[1:]

        if xml_declaration:
            processed_lines.append(xml_declaration)
        
        processed_lines.append("<root>\\n") # Start root tag
        processed_lines.extend(scml_content_lines)
        processed_lines.append("\\n</root>") # End root tag
        
        scml_file_like_object = StringIO("".join(processed_lines))
        
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
                            if parsed_end_id and parsed_end_id != note_entry['start']: # Only add end if it's different (a true range)
                                note_entry['end'] = parsed_end_id
                
                # Process the rest of the content of <com> tag
                main_body_html = serialize_element_content(elem, is_top_com_element=True)
                
                full_content = header_html
                if main_body_html:
                    if full_content: # Add a space if header exists and body exists
                        full_content += " "
                    full_content += main_body_html
                
                # Clean up whitespace: replace multiple spaces with one, strip leading/trailing.
                note_entry['content'] = re.sub(r'\s+', ' ', full_content).strip()
                
                notes.append(note_entry)
                elem.clear() # Crucial for iterparse to free memory

    except ET.ParseError as e:
        print(f"Error parsing SCML file: {e}")
        return
    except FileNotFoundError:
        print(f"Error: SCML file not found at {scml_file_path}")
        return

    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        print(f"Conversion complete. Output at {json_file_path}")
    except IOError as e:
        print(f"Error writing JSON file: {e}")

if __name__ == '__main__':
    # Determine paths relative to the script or use absolute paths
    # SCML file path from user
    # Defaulting to the user's provided path, ensure it's correct for your setup
    scml_input_file = "/Users/gmatson/Developer/GTY/study notes/new-notes/Exodus/ex-notes.scml"
    
    # Output JSON file path (in the same directory as SCML file)
    output_dir = os.path.dirname(scml_input_file)
    json_output_file = os.path.join(output_dir, "converted_notes.json")

    if not os.path.exists(scml_input_file):
        print(f"Input SCML file not found: {scml_input_file}")
        # Try a relative path if an absolute one was not found (e.g. if script is in 'new-notes')
        # For this tool, we'll assume the absolute path provided by user is the one to use.
    else:
        print(f"Starting conversion for: {scml_input_file}")
        print(f"Output will be saved to: {json_output_file}")
        convert_scml_to_json(scml_input_file, json_output_file) 