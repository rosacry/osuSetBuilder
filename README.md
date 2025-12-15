# osu! Set Builder

<p align="center">
  <img src="logo.png" alt="osu! Set Builder Logo" width="128">
</p>

<p align="center">
  <strong>A modern tool for creating and managing osu! beatmap sets</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/PySide6-6.0+-green.svg" alt="PySide6">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License">
</p>

---

## Features

- **Combine Multiple Difficulties** - Merge multiple .osu files into a single beatmap set
- **Unified Metadata Editing** - Edit title, artist, creator, source, and tags across all difficulties at once
- **Background Management** - Set a common background image for the entire beatmap set
- **Preview Point Picker** - Interactive audio player to select the perfect preview point with variable playback speed
- **Export Options** - Save as .osz file or open directly in osu!
- **Modern Dark Theme** - Beautiful osu!-inspired pink accent dark theme

## Screenshots

The application features a clean, modern interface with:
- Intuitive toolbar for all major actions
- Metadata editing panel with clear labels
- Background preview thumbnail
- Difficulty list with editable names
- Status bar for feedback

## Getting Started

### Prerequisites

- Python 3.10 or higher
- osu! installed (for the "Open in osu!" feature)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/osuSetBuilder.git
   cd osuSetBuilder
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python osu_set_builder.py
   ```

### Building an Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller osu_set_builder.spec
```

The executable will be in the `dist` folder.

## Usage

### Quick Start

1. **Add .osu files** - Click "Add .osu Files" to add beatmap difficulties
2. **Edit metadata** - Fill in Title, Artist, Creator, Source, and Tags
3. **Choose background** - Click "Background" to select an image
4. **Set preview point** - Click "Preview Point" to pick where the song preview starts
5. **Export** - Click "Save .osz" to save, or "Open in osu!" to import directly

### Tips

- **Auto-populate metadata**: Adding a properly formatted .osu file will auto-fill metadata fields
- **Auto-number difficulties**: Use "Auto-Number" to rename difficulties as 1, 2, 3...
- **Preview playback speed**: Use 25%, 50%, or 75% speed to precisely find the preview point

## Development

### Project Structure

```
osuSetBuilder/
├── osu_set_builder.py    # Main application code
├── osu_set_builder.spec  # PyInstaller spec file
├── icon.ico              # Application icon
├── logo.png              # Logo image
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── LICENSE               # MIT License
└── .gitignore            # Git ignore rules
```

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

This project uses:
- [Ruff](https://github.com/astral-sh/ruff) for linting
- Type hints throughout
- Docstrings for public functions

```bash
ruff check osu_set_builder.py
```

## Technical Details

### .osu File Parsing

The application parses .osu files to extract:
- Metadata: Title, Artist, Creator, Source, Tags
- Difficulty name (Version field)
- Audio filename
- Background image filename

### .osz File Generation

The .osz output contains:
- Rewritten .osu files with unified metadata
- Shared background image
- Audio file(s)

All files are bundled as a ZIP archive with .osz extension.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [osu!](https://osu.ppy.sh) - The rhythm game this tool is built for
- [PySide6](https://doc.qt.io/qtforpython/) - Qt bindings for Python
- [PyInstaller](https://pyinstaller.org) - For creating standalone executables

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<p align="center">
  Made for the osu! community
</p>
