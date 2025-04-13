import json
import os
import argparse
import re
import pickle
from datetime import datetime
import random
from rich.console import Console
from rich.table import Table, box
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from rapidfuzz.process import extractOne
from rich.layout import Layout
from rich.spinner import Spinner
from rich.prompt import Prompt
from rapidfuzz import fuzz

# Version information
__version__ = "1.0.2"

# Initialize Rich console
console = Console()

# Load JSON dataset
with open("dataset.json") as f:
    dataset = json.load(f)

# Dictionary for fast book name lookup
book_lookup = {item["name"].lower(): item for item in dataset}
book_names = list(book_lookup.keys())

# Get terminal width
terminal_length = os.get_terminal_size()[0] - os.get_terminal_size()[0] // 3

def create_table():
    """Create a new Rich table with consistent styling"""
    table = Table(show_header=True, header_style="bold blue", show_lines=True, box=None)
    table.add_column("Scripture", style="cyan", width=15)
    table.add_column("Text", style="white", width=terminal_length)
    return table

def format_text(text):
    """Format text to fit terminal width"""
    return "\n".join(re.findall(r".{1," + str(terminal_length) + r"}(?:\s+|$)", text))

def convert_brackets(text):
    """Convert curly brackets to normal brackets"""
    return text.replace("{", "(").replace("}", ")")

def display_verses(verses, title=None):
    """Display verses using Rich table"""
    table = Table(show_header=True, header_style="bold blue", show_lines=True, box=box.ROUNDED)
    table.add_column("Scripture", style="cyan", width=15)
    table.add_column("Text", style="white", width=terminal_length)
    
    for reference, text in verses:
        table.add_row(reference, format_text(convert_brackets(text)))
    
    if title:
        console.print(f"\n[bold blue]{title}[/bold blue]")
    console.print(table)

def display_search_results(results, keyword):
    if not results:
        console.print(f"[red]No results found for '{keyword}'.[/red]")
        return

    console.print(f"\n[bold blue]Search Results for '{keyword}':[/bold blue]")
    table = Table(show_header=True, header_style="bold blue", show_lines=True, box=box.ROUNDED)
    table.add_column("Scripture", style="cyan", width=15)
    table.add_column("Text", style="white", width=terminal_length)
    
    for idx, (book, chapter, verse, text) in enumerate(results, start=1):
        table.add_row(f"{book} {chapter}:{verse}", format_text(convert_brackets(text)))
        if idx % 10 == 0:  # Show 10 results per page
            console.print(table)
            table = Table(show_header=True, header_style="bold blue", show_lines=True, box=box.ROUNDED)
            table.add_column("Scripture", style="cyan", width=15)
            table.add_column("Text", style="white", width=terminal_length)
            console.print(f"[yellow](Press Enter to continue or 'q' to quit pagination)[/yellow]")
            user_input = console.input("> ").strip().lower()
            if user_input == "q":
                console.print("[green]Exiting pagination...[/green]")
                return
    
    if table.row_count > 0:
        console.print(table)

def display_bookmarks():
    bookmarks = load_bookmarks()
    if not bookmarks:
        console.print(f"[yellow]No bookmarks found.[/yellow]")
        return
    
    console.print("\n[bold blue]Your Bookmarks:[/bold blue]")
    table = Table(show_header=True, header_style="bold blue", show_lines=True, box=box.ROUNDED)
    table.add_column("Scripture", style="cyan", width=15)
    table.add_column("Note", style="white", width=terminal_length)
    
    for ref, data in bookmarks.items():
        timestamp = datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d %H:%M")
        note = data["note"] if data["note"] else "No note"
        table.add_row(f"{ref} ({timestamp})", note)
    
    console.print(table)

def process_scripture(scripture_input):
    # First try to match book-only pattern (now handles I, II, III, 1, 2, 3 prefixes)
    book_only_match = re.match(r"^(?:(?:I|II|III|[123])\s+)?\D+$", scripture_input)
    if book_only_match:
        book = book_only_match.group(0)
        result = lookup(book, 1, 1)  # Start from first chapter and verse
        if result:
            book_name, chapter, start_verse, verses = result
            # Get all verses from the first chapter
            chapter_data = book_lookup[book_name.lower()]["chapters"][0]
            
            # Display verses with pagination
            console.print(f"\n[bold blue]Verses from {book_name} Chapter 1:[/bold blue]")
            console.print(f"[yellow]Total verses: {len(chapter_data)}[/yellow]")
            
            # Handle chapters with fewer than 10 verses
            if len(chapter_data) <= 10:
                verses_to_display = [(f"{book_name} 1:{idx}", text) 
                                   for idx, text in enumerate(chapter_data, start=1)]
                display_verses(verses_to_display)
                console.print("[yellow](Press 'b' to bookmark current verse or any key to exit)[/yellow]")
                user_input = console.input("> ").strip().lower()
                if user_input == "b":
                    note = console.input("[yellow]Add a note (optional): [/yellow]").strip()
                    save_bookmark(f"{book_name} 1:{len(chapter_data)}", note)
            else:
                # Handle chapters with more than 10 verses
                current_verses = []
                for idx, verse_text in enumerate(chapter_data, start=1):
                    current_verses.append((f"{book_name} 1:{idx}", verse_text))
                    if idx % 10 == 0:  # Show 10 verses per page
                        display_verses(current_verses)
                        current_verses = []
                        console.print("[yellow](Press Enter to continue, 'q' to quit, or 'b' to bookmark current verse)[/yellow]")
                        user_input = console.input("> ").strip().lower()
                        if user_input == "q":
                            console.print("[green]Exiting pagination...[/green]")
                            return
                        elif user_input == "b":
                            note = console.input("[yellow]Add a note (optional): [/yellow]").strip()
                            save_bookmark(f"{book_name} 1:{idx}", note)
                            console.print("[yellow](Press Enter to continue or 'q' to quit pagination)[/yellow]")
                            if console.input("> ").strip().lower() == "q":
                                console.print("[green]Exiting pagination...[/green]")
                                return
                
                # Display any remaining verses
                if current_verses:
                    display_verses(current_verses)
                    console.print("[yellow](Press 'b' to bookmark current verse or any key to exit)[/yellow]")
                    user_input = console.input("> ").strip().lower()
                    if user_input == "b":
                        note = console.input("[yellow]Add a note (optional): [/yellow]").strip()
                        save_bookmark(f"{book_name} 1:{len(chapter_data)}", note)
        return

    # Then try to match book and chapter pattern
    book_chapter_match = re.match(r"^((?:(?:I|II|III|[123])\s+)?\D+)\s+(\d+)$", scripture_input)
    if book_chapter_match:
        book, chapter = book_chapter_match.groups()
        result = lookup(book, chapter, 1)  # Start from first verse of the chapter
        if result:
            book_name, chapter, start_verse, verses = result
            # Get all verses from the specified chapter
            chapter_data = book_lookup[book_name.lower()]["chapters"][int(chapter) - 1]
            
            # Display verses with pagination
            console.print(f"\n[bold blue]Verses from {book_name} Chapter {chapter}:[/bold blue]")
            console.print(f"[yellow]Total verses: {len(chapter_data)}[/yellow]")
            
            # Handle chapters with fewer than 10 verses
            if len(chapter_data) <= 10:
                verses_to_display = [(f"{book_name} {chapter}:{idx}", text) 
                                   for idx, text in enumerate(chapter_data, start=1)]
                display_verses(verses_to_display)
                console.print("[yellow](Press 'b' to bookmark current verse or any key to exit)[/yellow]")
                user_input = console.input("> ").strip().lower()
                if user_input == "b":
                    note = console.input("[yellow]Add a note (optional): [/yellow]").strip()
                    save_bookmark(f"{book_name} {chapter}:{len(chapter_data)}", note)
            else:
                # Handle chapters with more than 10 verses
                current_verses = []
                for idx, verse_text in enumerate(chapter_data, start=1):
                    current_verses.append((f"{book_name} {chapter}:{idx}", verse_text))
                    if idx % 10 == 0:  # Show 10 verses per page
                        display_verses(current_verses)
                        current_verses = []
                        console.print("[yellow](Press Enter to continue, 'q' to quit, or 'b' to bookmark current verse)[/yellow]")
                        user_input = console.input("> ").strip().lower()
                        if user_input == "q":
                            console.print("[green]Exiting pagination...[/green]")
                            return
                        elif user_input == "b":
                            note = console.input("[yellow]Add a note (optional): [/yellow]").strip()
                            save_bookmark(f"{book_name} {chapter}:{idx}", note)
                            console.print("[yellow](Press Enter to continue or 'q' to quit pagination)[/yellow]")
                            if console.input("> ").strip().lower() == "q":
                                console.print("[green]Exiting pagination...[/green]")
                                return
                
                # Display any remaining verses
                if current_verses:
                    display_verses(current_verses)
                    console.print("[yellow](Press 'b' to bookmark current verse or any key to exit)[/yellow]")
                    user_input = console.input("> ").strip().lower()
                    if user_input == "b":
                        note = console.input("[yellow]Add a note (optional): [/yellow]").strip()
                        save_bookmark(f"{book_name} {chapter}:{len(chapter_data)}", note)
        return

    # Then try to match chapter:verse pattern
    match = re.match(r"^((?:(?:I|II|III|[123])\s+)?\D+)\s+(\d+):(\d+)(?:-(\d+))?", scripture_input)
    if match:
        book, chapter, verse, end_verse = match.groups()
        result = lookup(book, chapter, verse, end_verse)
        if result:
            book_name, chapter, start_verse, verses = result
            verses_to_display = [(f"{book_name} {chapter}:{idx}", text) 
                               for idx, text in enumerate(verses, start=start_verse)]
            display_verses(verses_to_display)
            
            # Add option to view context
            console.print("\n[yellow]Would you like to see the context? (yes/no): [/yellow]")
            if console.input("> ").strip().lower() in ["yes", "y"]:
                context = get_verse_context(book_name, chapter, start_verse)
                if context:
                    console.print("\n[bold blue]Context:[/bold blue]")
                    context_verses = [(f"{book_name} {chapter}:{verse_num}", text) 
                                    for verse_num, text in context]
                    display_verses(context_verses)
            
            # Add option to bookmark
            console.print("\n[yellow]Would you like to bookmark this verse? (yes/no): [/yellow]")
            if console.input("> ").strip().lower() in ["yes", "y"]:
                note = console.input("[yellow]Add a note (optional): [/yellow]").strip()
                save_bookmark(f"{book_name} {chapter}:{start_verse}", note)
    else:
        console.print("[red]Error: Invalid scripture format. Use 'Book', 'Book Chapter', or 'Book Chapter:Verse' or 'Book Chapter:Verse-Verse'[/red]")

def main_menu():
    title_ascii = r"""
 ______   _____  ______   _        _______     ______  _        _____ 
(____  \ (_____)(____  \ | |      (_______)   / _____)| |      (_____)
 ____)  )   _    ____)  )| |       _____     | /      | |         _   
|  __  (   | |  |  __  ( | |      |  ____)    | |      | |        | |  
| |__)  ) _| |_ | |__)  )| |_____ | |_____   | \_____ | |_____  _| |_ 
|______/ (_____)|______/ |_______)|_______)   \______)|_______)(_____)
    """

    while True:
        console.print(f"\n[bold blue]Welcome to[/bold blue]")
        console.print(f"[bold blue]{title_ascii}[/bold blue]")
        console.print("1. Lookup a Scripture")
        console.print("2. Search for a Keyword")
        console.print("3. Display Bookmarks")
        console.print("4. Get Daily Verse")
        console.print("5. Advanced Search")
        console.print("6. Exit")
        choice = console.input(f"\n[yellow]Enter your choice: [/yellow]").strip()

        if choice == "1":
            scripture = console.input("[yellow]Enter scripture (e.g., 'John 3:16'): [/yellow]").strip()
            process_scripture(scripture)
        elif choice == "2":
            keyword = console.input("[yellow]Enter keyword to search: [/yellow]").strip()
            use_regex = console.input("[yellow]Enable regex search? (yes/no): [/yellow]").strip().lower() in ["yes", "y"]
            results = search_keyword(keyword, use_regex)
            display_search_results(results, keyword)
        elif choice == "3":
            display_bookmarks()
        elif choice == "4":
            verse = get_daily_verse()
            console.print(f"\n[bold blue]Today's Verse:[/bold blue]")
            display_verses([(f"{verse[0]} {verse[1]}:{verse[2]}", verse[3])])
        elif choice == "5":
            console.print(f"\n[bold blue]Advanced Search Options:[/bold blue]")
            keyword = console.input("[yellow]Enter keyword to search: [/yellow]").strip()
            
            options = {}
            options["regex"] = console.input("[yellow]Enable regex search? (yes/no): [/yellow]").strip().lower() in ["yes", "y"]
            
            testament = console.input("[yellow]Filter by testament? (old/new/both): [/yellow]").strip().lower()
            if testament in ["old", "new"]:
                options["testament"] = testament
            
            min_words = console.input("[yellow]Minimum words in verse (optional): [/yellow]").strip()
            if min_words.isdigit():
                options["min_words"] = int(min_words)
            
            max_words = console.input("[yellow]Maximum words in verse (optional): [/yellow]").strip()
            if max_words.isdigit():
                options["max_words"] = int(max_words)
            
            results = advanced_search(keyword, options)
            display_search_results(results, keyword)
        elif choice == "6":
            console.print("[green]Thank you for using Bible CLI. Goodbye![/green]")
            break
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")

def load_bookmarks():
    try:
        with open("bookmarks.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}

def save_bookmark(reference, note=""):
    bookmarks = load_bookmarks()
    bookmarks[reference] = {
        "timestamp": datetime.now().isoformat(),
        "note": note
    }
    with open("bookmarks.pkl", "wb") as f:
        pickle.dump(bookmarks, f)
    console.print(f"[green]Bookmark saved successfully![/green]")

def get_daily_verse():
    today = datetime.now().date()
    seed = int(today.strftime("%Y%m%d"))
    random.seed(seed)
    book = random.choice(dataset)
    chapter = random.choice(book["chapters"])
    verse_idx = random.randint(0, len(chapter) - 1)
    return (book["name"], book["chapters"].index(chapter) + 1, 
            verse_idx + 1, chapter[verse_idx])

def search_keyword(keyword, is_regex=False):
    results = []
    pattern = re.compile(keyword, re.IGNORECASE) if is_regex else None

    for book in dataset:
        for chapter_idx, chapter in enumerate(book["chapters"], start=1):
            for verse_idx, verse_text in enumerate(chapter, start=1):
                if is_regex and pattern.search(verse_text):
                    highlighted_text = pattern.sub(f"[yellow]{pattern.pattern}[/yellow]", verse_text)
                    results.append((book["name"], chapter_idx, verse_idx, highlighted_text))
                elif not is_regex and keyword.lower() in verse_text.lower():
                    highlighted_text = re.sub(
                        re.escape(keyword), f"[yellow]{keyword}[/yellow]", verse_text, flags=re.IGNORECASE
                    )
                    results.append((book["name"], chapter_idx, verse_idx, highlighted_text))
    return results

def get_verse_context(book, chapter, verse, context_lines=2):
    """Show verses before and after the target verse"""
    try:
        book_data = book_lookup[book.lower()]
        chapter_idx = int(chapter) - 1
        verse_idx = int(verse) - 1
        verses = book_data["chapters"][chapter_idx]
        
        start = max(0, verse_idx - context_lines)
        end = min(len(verses), verse_idx + context_lines + 1)
        
        context_verses = []
        for i in range(start, end):
            verse_num = i + 1
            context_verses.append((verse_num, verses[i]))
        
        return context_verses
    except (ValueError, IndexError):
        return None

def advanced_search(keyword, options=None):
    """Enhanced search with additional filters"""
    if options is None:
        options = {}
    
    results = []
    pattern = re.compile(keyword, re.IGNORECASE) if options.get("regex", False) else None
    
    for book in dataset:
        # Apply testament filter
        if options.get("testament"):
            # Determine testament based on book name
            is_new_testament = book["name"] in [
                "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
                "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
                "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus",
                "Philemon", "Hebrews", "James", "1 Peter", "2 Peter", "1 John",
                "2 John", "3 John", "Jude", "Revelation"
            ]
            if options["testament"] == "new" and not is_new_testament:
                continue
            if options["testament"] == "old" and is_new_testament:
                continue
        
        for chapter_idx, chapter in enumerate(book["chapters"], start=1):
            for verse_idx, verse_text in enumerate(chapter, start=1):
                # Apply search
                if pattern and pattern.search(verse_text):
                    match = True
                    highlighted_text = pattern.sub(f"[yellow]{pattern.pattern}[/yellow]", verse_text)
                elif not pattern and keyword.lower() in verse_text.lower():
                    match = True
                    highlighted_text = re.sub(
                        re.escape(keyword), 
                        f"[yellow]{keyword}[/yellow]", 
                        verse_text, 
                        flags=re.IGNORECASE
                    )
                else:
                    match = False
                
                if match:
                    # Apply additional filters if specified
                    if options.get("min_words"):
                        if len(verse_text.split()) < options["min_words"]:
                            continue
                    if options.get("max_words"):
                        if len(verse_text.split()) > options["max_words"]:
                            continue
                    
                    results.append((book["name"], chapter_idx, verse_idx, highlighted_text))
    
    return results

def lookup(book_name, chapter, start_verse, end_verse=None, non_interactive=False):
    """Lookup scripture by book, chapter, and verse"""
    # Get the best match for the book name
    best_match = confirm_best_match(book_name, non_interactive=non_interactive)
    if not best_match:
        if not non_interactive:
            console.print(f"[red]No match found for '{book_name}'.[/red]")
        return None

    # Get the book data
    book = book_lookup[best_match.lower()]
    
    # Convert chapter and verse to integers
    try:
        chapter = int(chapter)
        start_verse = int(start_verse)
        if end_verse is not None:
            end_verse = int(end_verse)
    except ValueError:
        if not non_interactive:
            console.print("[red]Error: Chapter and verse must be numbers.[/red]")
        return None

    # Check if chapter exists
    if chapter < 1 or chapter > len(book["chapters"]):
        if not non_interactive:
            console.print(f"[red]Error: Chapter {chapter} is out of range. {best_match} has {len(book['chapters'])} chapters.[/red]")
        return None

    # Get the chapter
    chapter_data = book["chapters"][chapter - 1]
    
    # Check if verse exists
    if start_verse < 1 or start_verse > len(chapter_data):
        if not non_interactive:
            console.print(f"[red]Error: Verse {start_verse} is out of range. {book_name} Chapter {chapter} has {len(chapter_data)} verses.[/red]")
        return None

    # If end_verse is not specified, use start_verse for single verse lookup
    if end_verse is None:
        end_verse = start_verse
    elif end_verse < 1 or end_verse < start_verse or end_verse > len(chapter_data):
        if not non_interactive:
            console.print(f"[red]Error: Verse range {start_verse}-{end_verse} is out of range. {book_name} Chapter {chapter} has {len(chapter_data)} verses.[/red]")
        return None

    # Get the verses
    verses = chapter_data[start_verse - 1:end_verse]
    
    # Return None if no verses found
    if not verses:
        return None
        
    return (book["name"], chapter, start_verse, verses)

def confirm_best_match(book_name, non_interactive=False):
    """Confirm if the best match is correct"""
    # Convert Roman numerals to numbers
    def normalize_book_name(name):
        roman_to_num = {
            'I ': '1 ',
            'II ': '2 ',
            'III ': '3 '
        }
        for roman, num in roman_to_num.items():
            if name.upper().startswith(roman):
                return num + name[len(roman):]
        return name

    # Normalize and convert to lowercase for comparison
    book_name = normalize_book_name(book_name).lower()
    
    # Check for exact match
    if book_name in book_lookup:
        return book_name.title()
    
    # Find best match using fuzzy matching
    best_match = None
    best_ratio = 0
    
    for book in book_lookup:
        # Normalize both names for comparison
        normalized_book = normalize_book_name(book)
        ratio = fuzz.ratio(book_name, normalized_book)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = book
    
    # If no match found or ratio is too low
    if not best_match or best_ratio < 80:
        return None
    
    # In non-interactive mode, return the best match if it's good enough
    if non_interactive:
        return best_match.title()
    
    # In interactive mode, ask for confirmation
    console.print(f"\n[yellow]Did you mean {best_match.title()}? (y/n): [/yellow]", end="")
    response = console.input().lower()
    return best_match.title() if response == 'y' else None

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", help="Search for a keyword or phrase")
    parser.add_argument("--regex", action="store_true", help="Enable regex search")
    parser.add_argument("--testament", choices=["old", "new"], help="Filter by testament")
    parser.add_argument("--min-words", type=int, help="Minimum words in verse")
    parser.add_argument("--max-words", type=int, help="Maximum words in verse")
    parser.add_argument("scripture", nargs="?", help="Lookup a scripture (e.g., 'John 3:16')")
    args = parser.parse_args()

    if args.search:
        options = {"regex": args.regex}
        if args.testament:
            options["testament"] = args.testament
        if args.min_words:
            options["min_words"] = args.min_words
        if args.max_words:
            options["max_words"] = args.max_words
        results = advanced_search(args.search, options)
        display_search_results(results, args.search)
    elif args.scripture:
        process_scripture(args.scripture)
    else:
        main_menu()
