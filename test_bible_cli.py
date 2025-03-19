import unittest
import os
import pickle
from datetime import datetime
from bible_cli import (
    lookup, confirm_best_match, search_keyword, advanced_search,
    get_verse_context, get_daily_verse, load_bookmarks, save_bookmark,
    format_text, book_lookup
)
import json

# Load the dataset
with open("dataset.json") as f:
    dataset = json.load(f)

class TestBibleCli(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_book = "Genesis"
        self.test_chapter = 1
        self.test_verse = 1
        self.test_verse_range = "1-3"
        self.test_keyword = "God"
        self.test_regex = r"light.*darkness"
        # Create a temporary bookmarks file for testing
        self.test_bookmarks_file = "test_bookmarks.pkl"
        self.original_bookmarks = {}
        if os.path.exists(self.test_bookmarks_file):
            with open(self.test_bookmarks_file, "rb") as f:
                self.original_bookmarks = pickle.load(f)
            os.remove(self.test_bookmarks_file)

    def tearDown(self):
        # Restore original bookmarks file
        if os.path.exists(self.test_bookmarks_file):
            os.remove(self.test_bookmarks_file)
        if self.original_bookmarks:
            with open(self.test_bookmarks_file, "wb") as f:
                pickle.dump(self.original_bookmarks, f)

    def test_valid_lookup(self):
        """Test valid scripture lookup"""
        result = lookup(self.test_book, self.test_chapter, self.test_verse, non_interactive=True)
        self.assertIsNotNone(result)
        book_name, chapter, start_verse, verses = result
        self.assertEqual(book_name, self.test_book)
        self.assertEqual(chapter, self.test_chapter)
        self.assertEqual(start_verse, self.test_verse)
        self.assertEqual(len(verses), 1)
        self.assertEqual(verses[0], "In the beginning God created the heaven and the earth.")

    def test_invalid_book_name(self):
        # Test with an invalid book name
        result = lookup("FakeBook", 1, 1, 1, non_interactive=True)
        self.assertIsNone(result)

    def test_invalid_chapter(self):
        """Test lookup with invalid chapter"""
        result = lookup(self.test_book, 100, self.test_verse, non_interactive=True)
        self.assertIsNone(result)

    def test_invalid_verse(self):
        """Test lookup with invalid verse"""
        result = lookup(self.test_book, self.test_chapter, 100, non_interactive=True)
        self.assertIsNone(result)

    def test_invalid_verse_range(self):
        """Test lookup with invalid verse range"""
        result = lookup(self.test_book, self.test_chapter, 1, 100, non_interactive=True)
        self.assertIsNone(result)

    def test_verse_range_validation(self):
        """Test verse range validation"""
        # Test invalid verse numbers
        self.assertIsNone(lookup(self.test_book, self.test_chapter, 0, non_interactive=True))
        self.assertIsNone(lookup(self.test_book, self.test_chapter, 1, 0, non_interactive=True))
        self.assertIsNone(lookup(self.test_book, self.test_chapter, 2, 1, non_interactive=True))
        
        # Test invalid chapter numbers
        self.assertIsNone(lookup(self.test_book, 0, 1, non_interactive=True))
        self.assertIsNone(lookup(self.test_book, 51, 1, non_interactive=True))

    def test_exact_book_match(self):
        """Test exact book name matching"""
        result = confirm_best_match("Genesis", non_interactive=True)
        self.assertEqual(result, "Genesis")

    def test_fuzzy_book_match(self):
        """Test fuzzy book name matching"""
        result = confirm_best_match("Genesys", non_interactive=True)
        self.assertEqual(result, "Genesis")

    def test_no_book_match(self):
        """Test no book match"""
        result = confirm_best_match("NonExistentBook", non_interactive=True)
        self.assertIsNone(result)

    def test_fuzzy_match_threshold(self):
        """Test fuzzy match threshold"""
        # Should match
        result = confirm_best_match("Genesys", non_interactive=True)
        self.assertEqual(result, "Genesis")
        
        # Should not match
        result = confirm_best_match("Xyzabc", non_interactive=True)
        self.assertIsNone(result)

    def test_search_keyword(self):
        """Test basic keyword search"""
        results = search_keyword(self.test_keyword, False)
        self.assertIsNotNone(results)
        self.assertTrue(len(results) > 0)
        self.assertTrue(any(self.test_keyword.lower() in result[3].lower() for result in results))

    def test_regex_search(self):
        """Test regex search"""
        results = search_keyword(self.test_regex, True)
        self.assertIsNotNone(results)
        self.assertTrue(len(results) > 0)
        self.assertTrue(any("light" in result[3].lower() and "darkness" in result[3].lower() for result in results))

    def test_advanced_search(self):
        """Test advanced search functionality"""
        results = advanced_search(self.test_keyword, {})
        self.assertIsNotNone(results)
        # Test advanced search with filters
        options = {
            "testament": "new",
            "min_words": 5,
            "max_words": 20
        }
        results = advanced_search("love", options)
        self.assertTrue(len(results) > 0)
        for result in results:
            verse_text = result[3]
            word_count = len(verse_text.split())
            self.assertTrue(5 <= word_count <= 20)

    def test_verse_context(self):
        # Test getting verse context
        context = get_verse_context("Genesis", 1, 1)
        self.assertIsNotNone(context)
        self.assertTrue(len(context) > 1)  # Should include the verse and surrounding verses
        self.assertEqual(context[0][0], 1)  # First verse number should be 1

    def test_daily_verse(self):
        # Test daily verse feature
        verse = get_daily_verse()
        self.assertIsNotNone(verse)
        self.assertEqual(len(verse), 4)  # Should return (book, chapter, verse, text)
        self.assertTrue(isinstance(verse[0], str))  # Book name
        self.assertTrue(isinstance(verse[1], int))  # Chapter
        self.assertTrue(isinstance(verse[2], int))  # Verse
        self.assertTrue(isinstance(verse[3], str))  # Text

    def test_bookmark_system(self):
        # Test saving and loading bookmarks
        reference = "John 3:16"
        note = "Test note"
        save_bookmark(reference, note)
        bookmarks = load_bookmarks()
        self.assertIn(reference, bookmarks)
        self.assertEqual(bookmarks[reference]["note"], note)
        self.assertIn("timestamp", bookmarks[reference])

    def test_format_text(self):
        # Test text formatting with a fixed width
        long_text = "This is a very long text that should be formatted to fit the terminal width. " * 3
        # Temporarily override terminal_length for testing
        import bible_cli
        original_length = bible_cli.terminal_length
        bible_cli.terminal_length = 80
        formatted = format_text(long_text)
        bible_cli.terminal_length = original_length  # Restore original
        self.assertTrue(len(formatted.split('\n')) > 1)
        for line in formatted.split('\n'):
            self.assertLessEqual(len(line), 80)  # Fixed width of 80 for testing

    def test_advanced_search_filters(self):
        # Test various advanced search filters
        test_cases = [
            ({"testament": "old"}, "Testament filter"),
            ({"min_words": 10}, "Minimum words filter"),
            ({"max_words": 5}, "Maximum words filter"),
            ({"regex": True}, "Regex search")
        ]
        
        for options, description in test_cases:
            with self.subTest(description):
                results = advanced_search("the", options)
                self.assertIsNotNone(results)
                if "testament" in options:
                    for result in results:
                        book_name = result[0]
                        # Check if book is in the correct testament
                        is_new_testament = book_name in [
                            "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
                            "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
                            "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus",
                            "Philemon", "Hebrews", "James", "1 Peter", "2 Peter", "1 John",
                            "2 John", "3 John", "Jude", "Revelation"
                        ]
                        self.assertEqual(
                            options["testament"] == "new",
                            is_new_testament,
                            f"Book {book_name} is in wrong testament"
                        )

    def test_book_only_lookup(self):
        # Test lookup with just a book name
        result = lookup("Genesis", 1, 1, non_interactive=True)  # Genesis
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Genesis")  # Book name
        self.assertEqual(result[1], 1)         # Chapter
        self.assertEqual(result[2], 1)         # Start verse
        self.assertIn("In the beginning God created the heaven and the earth.", result[3])

    def test_invalid_book_only_lookup(self):
        # Test lookup with invalid book name
        result = lookup("FakeBook", 1, 1, non_interactive=True)
        self.assertIsNone(result)

    def test_book_only_with_fuzzy_match(self):
        # Test book-only lookup with fuzzy matching
        result = lookup("Genesys", 1, 1, non_interactive=True)  # Should match "Genesis"
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Genesis")

    def test_book_only_pagination(self):
        """Test that book-only lookup returns all verses from first chapter"""
        # Test with Genesis chapter 1
        result = lookup("Genesis", 1, 1, end_verse=31, non_interactive=True)
        self.assertIsNotNone(result)
        book_name, chapter, start_verse, verses = result
        chapter_data = book_lookup[book_name.lower()]["chapters"][0]
        
        # Verify that all verses are returned
        self.assertEqual(len(verses), len(chapter_data))
        
        # Verify verse content
        for i, (verse, chapter_verse) in enumerate(zip(verses, chapter_data)):
            self.assertEqual(verse, chapter_verse, f"Verse {i+1} content mismatch")
        
        # Verify verse numbering
        for i, verse in enumerate(verses, start=1):
            self.assertEqual(verse, chapter_data[i-1], f"Verse {i} numbering mismatch")
            
        # Test with John chapter 3
        result = lookup("John", 3, 1, end_verse=36, non_interactive=True)
        self.assertIsNotNone(result)
        book_name, chapter, start_verse, verses = result
        chapter_data = book_lookup[book_name.lower()]["chapters"][2]  # John 3 is at index 2
        
        # Verify that all verses are returned
        self.assertEqual(len(verses), len(chapter_data))
        
        # Verify verse content
        for i, (verse, chapter_verse) in enumerate(zip(verses, chapter_data)):
            self.assertEqual(verse, chapter_verse, f"Verse {i+1} content mismatch")
        
        # Verify verse numbering
        for i, verse in enumerate(verses, start=1):
            self.assertEqual(verse, chapter_data[i-1], f"Verse {i} numbering mismatch")

    def test_book_chapter_lookup(self):
        # Test lookup with book and chapter
        result = lookup("Genesis", 1, 1, non_interactive=True)  # Genesis chapter 1
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Genesis")  # Book name
        self.assertEqual(result[1], 1)         # Chapter
        self.assertEqual(result[2], 1)         # Start verse
        self.assertIn("In the beginning God created the heaven and the earth.", result[3])

    def test_invalid_book_chapter_lookup(self):
        # Test lookup with invalid chapter
        result = lookup("Genesis", 100, 1, non_interactive=True)  # Genesis has 50 chapters
        self.assertIsNone(result)

    def test_book_chapter_with_fuzzy_match(self):
        # Test book and chapter lookup with fuzzy matching
        result = lookup("Genesys", 1, 1, non_interactive=True)  # Should match "Genesis"
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Genesis")

    def test_book_chapter_verse_count(self):
        """Test that book and chapter lookup returns all verses from the chapter"""
        # Test with Genesis chapter 1
        result = lookup("Genesis", 1, 1, end_verse=31, non_interactive=True)
        self.assertIsNotNone(result)
        book_name, chapter, start_verse, verses = result
        chapter_data = book_lookup[book_name.lower()]["chapters"][int(chapter) - 1]
        self.assertEqual(len(verses), len(chapter_data))  # Should return all verses
        
        # Test with John chapter 3
        result = lookup("John", 3, 1, end_verse=36, non_interactive=True)
        self.assertIsNotNone(result)
        book_name, chapter, start_verse, verses = result
        chapter_data = book_lookup[book_name.lower()]["chapters"][int(chapter) - 1]
        self.assertEqual(len(verses), len(chapter_data))  # Should return all verses

if __name__ == '__main__':
    unittest.main()
