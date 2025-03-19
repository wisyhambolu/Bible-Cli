# Bible CLI

A command-line interface for reading and searching the Bible, built with Python and Rich.

## Features

- Look up specific verses by book, chapter, and verse
- Search for keywords or phrases across all books
- Advanced search with filters (testament, word count, regex)
- Daily verse feature
- Bookmark favorite verses with notes
- Beautiful terminal interface with Rich
- Fuzzy matching for book names
- Pagination for long chapters and search results
- Context view for verses

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wisyhambolu/Bible-Cli.git
cd Bible-Cli
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode
```bash
python bible_cli.py
```

### Command Line Arguments
```bash
# Look up a specific verse
python bible_cli.py "John 3:16"

# Search for a keyword
python bible_cli.py -s "love"

# Advanced search with options
python bible_cli.py -s "faith" --testament new --min-words 10 --max-words 20 --regex
```

## Examples

1. Look up a specific verse:
```
Enter scripture (e.g., 'John 3:16'): John 3:16
```

2. Search for a keyword:
```
Enter keyword to search: love
Enable regex search? (yes/no): no
```

3. Get a daily verse:
```
Today's Verse:
[Verse display]
```

## Features in Detail

### Scripture Lookup
- Look up by book only (e.g., "Genesis")
- Look up by book and chapter (e.g., "Genesis 1")
- Look up by book, chapter, and verse (e.g., "John 3:16")
- Look up verse ranges (e.g., "John 3:16-18")

### Search Features
- Case-insensitive search
- Regular expression support
- Filter by testament (Old/New)
- Filter by word count
- Paginated results

### Bookmarks
- Save favorite verses
- Add notes to bookmarks
- View all bookmarks with timestamps

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support the Project

If you find this project helpful, consider buying me a coffee! Your support helps me maintain and improve this project.

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg)](https://buymeacoffee.com/wisyhambolu)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created by Wisdom Hambolu

## Acknowledgments

- Bible dataset from [source]
- Rich library for beautiful terminal output
- RapidFuzz for fuzzy matching
