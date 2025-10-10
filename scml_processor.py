import xml.etree.ElementTree as ET
import os
import argparse
import re

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
    name = re.sub(r'[<>:"/\\\\|?*&]', '_', name)
    name = name.replace(' ', '_')
    name = re.sub(r'_+', '_', name) # Replace multiple underscores with one
    name = name.strip('_')
    return name if name else "Unknown"

def write_xml_content(elements_list, filepath, root_tag_name):
    """
    Writes a list of XML elements to a file under a new root element.
    If elements_list is empty, does not create the file.
    """
    if not elements_list:
        # print(f"No content for {root_tag_name}. Skipping file: {filepath}")
        return

    new_root = ET.Element(root_tag_name)
    for el in elements_list:
        new_root.append(el)
    
    tree = ET.ElementTree(new_root)
    
    # ET.indent for pretty printing is available in Python 3.9+
    try:
        ET.indent(tree, space="  ", level=0)
    except AttributeError:
        # ET.indent not available, output will be less readable
        pass

    try:
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        print(f"Written: {filepath}")
    except Exception as e:
        print(f"Error writing XML file {filepath}: {e}")

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


def process_scml(input_file, output_dir_base):
    if not os.path.exists(output_dir_base):
        os.makedirs(output_dir_base)

    try:
        tree = ET.parse(input_file)
        scml_root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing SCML file '{input_file}': {e}")
        return
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    # Find all <book> elements, or use root if it's a single <book>
    books = scml_root.findall('.//book')
    if not books and scml_root.tag.lower() == 'book':
        books = [scml_root]
    
    if not books:
        print(f"No <book> elements found in '{input_file}'.")
        return

    for book_element in books:
        raw_book_semantic_name = book_element.get('semantic')
        book_id_attr = book_element.get('id')

        # Determine the primary name for the book (used for folder name)
        # Prefer semantic, then child <bk> tag's text, then id attribute.
        book_name_for_folder = raw_book_semantic_name
        if not book_name_for_folder:
            bk_tag = book_element.find('bk') # Check for <bk>Book Name</bk>
            if bk_tag is not None and bk_tag.text:
                book_name_for_folder = bk_tag.text.strip()
            elif book_id_attr:
                book_name_for_folder = book_id_attr # Fallback to ID
            else:
                book_name_for_folder = "UnknownBook"
                print(f"Warning: Could not determine a name for a book element. Using default '{book_name_for_folder}'.")
        
        # Sanitize this name for folder creation
        book_folder_sanitized = sanitize_name(book_name_for_folder)
        
        # Get a clean book name for semantic comparisons (e.g. "Exodus" from "Study notes for Exodus")
        # Use the raw semantic name if available, otherwise the determined book_name_for_folder
        name_to_compare_chapters_against = get_book_name_for_comparison(raw_book_semantic_name if raw_book_semantic_name else book_name_for_folder)

        book_output_dir = os.path.join(output_dir_base, book_folder_sanitized)
        if not os.path.exists(book_output_dir):
            os.makedirs(book_output_dir)
        
        print(f"\nProcessing Book: '{book_name_for_folder}' (Comparison Name: '{name_to_compare_chapters_against}') -> Folder: '{book_folder_sanitized}'")

        bible_text_elements = []
        study_notes_elements = []
        other_resources_elements = []
        
        # Process direct children of <book> that are not <chapter> (e.g., global intro figures)
        for child_element in book_element:
            if child_element.tag.lower() != 'chapter':
                other_resources_elements.append(child_element)

        for chapter in book_element.findall('chapter'):
            chapter_id = chapter.get('id', '').lower()
            chapter_semantic = chapter.get('semantic', '')

            is_study_notes_chapter = chapter_semantic.lower().startswith("study notes and features for") and \
                                     name_to_compare_chapters_against.lower() in chapter_semantic.lower()
            
            is_bible_text_chapter = False
            if chapter_id.startswith("ch"): 
                # Bible text chapter pattern: "[BookName] [ChapterNumber]"
                # e.g., "Leviticus 1", "1 Samuel 10"
                # Make book name comparison case-insensitive and allow for flexible spacing
                bible_pattern = rf"^{re.escape(name_to_compare_chapters_against)}\s+\d+$"
                if re.match(bible_pattern, chapter_semantic, re.IGNORECASE):
                    is_bible_text_chapter = True
            
            # Introduction chapter can be id="intro..." or semantic="[BookName]" (and not already matched)
            is_introduction_chapter = chapter_id.startswith("intro") or \
                                     (chapter_semantic.lower() == name_to_compare_chapters_against.lower() and \
                                      not is_bible_text_chapter and not is_study_notes_chapter)


            is_translators_notes_chapter = "translator's notes" in chapter_semantic.lower() or \
                                           "cross-references" in chapter_semantic.lower()

            if is_study_notes_chapter:
                study_notes_elements.append(chapter)
            elif is_bible_text_chapter:
                bible_text_elements.append(chapter)
            elif is_introduction_chapter or is_translators_notes_chapter:
                other_resources_elements.append(chapter)
            else:
                # Default for other chapter types (e.g., articles, specific outlines)
                other_resources_elements.append(chapter)
        
        write_xml_content(bible_text_elements, os.path.join(book_output_dir, 'bible_text.xml'), f"{book_folder_sanitized}_BibleText")
        write_xml_content(study_notes_elements, os.path.join(book_output_dir, 'study_notes.xml'), f"{book_folder_sanitized}_StudyNotes")
        write_xml_content(other_resources_elements, os.path.join(book_output_dir, 'other_resources.xml'), f"{book_folder_sanitized}_OtherResources")

def main():
    parser = argparse.ArgumentParser(description="Separate SCML file into Bible books, study notes, and other resources.")
    parser.add_argument("input_scml_file", help="Path to the input SCML file.")
    parser.add_argument("output_directory", help="Path to the directory where output folders and files will be created.")
    
    args = parser.parse_args()
    
    process_scml(args.input_scml_file, args.output_directory)

if __name__ == "__main__":
    main() 