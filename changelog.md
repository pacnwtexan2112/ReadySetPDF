# Changelog

All notable changes to this project will be documented in this file.

[2.3] - 2026-07-11 July 11, 2026

🚀 New Features & Enhancements

Background Processing (Multithreading): The Automation and Hot Folder tools now run on a dedicated background thread. You can now execute massive batch processes and OCR scans without freezing or locking up the main user interface. A new "Real-Time Dashboard" in the header tracks all background tasks.

Global Settings Menu: Added a dedicated ⚙️ Global Settings button to the main header, centralizing application preferences and color themes.

Universal Measurement Units: You no longer need to select units on every individual tab. You can now set your preferred unit (Inches, Millimeters, or Points) in the Global Settings, and the entire application will instantly adapt.

Custom Page Size Presets: Users can now create, name, and save unlimited custom sheet sizes (e.g., SRA3 320x450mm). These custom sizes automatically inject themselves into the standard preset dropdowns across the Resize, Monkey, Grid, and Booklet tabs.

Persistent Preferences: Application settings, themes, and custom page sizes now save securely to your local Windows AppData folder. Your preferences will persist permanently, even if you close the app, move the .exe file, or update to a newer version of the software.

🐛 Bug Fixes & Engine Upgrades

Universal Math Engine (Metric Fix): Completely overhauled the PyMuPDF geometry logic. Stripped out all localized tab math and replaced it with a centralized to_points() engine. This permanently resolves the severe metric scaling bug where Millimeter conversions were resulting in astronomical page dimensions (e.g., 5050mm).

VDP Visual Targeting Fix: Patched a critical scaling bug in the VDP Mail Merge tab where the green visual targeting box would shrink to an unusable 1/72nd of its size when processing non-inch inputs.

Standard Preset Conversion: Standard US sizes (Letter, Legal, Tabloid) now actively listen to the Global Unit setting and will safely convert and populate their exact equivalents in millimeters or points when clicked.

[2.21] - 2026-07-09
New Features & Pro Tools

OCR Text Extraction (Pro Tier): Integrated the Tesseract AI engine to unlock text from flattened client scans and rasterized PDFs.

Multiple Extraction Modes: Operators can now extract scanned text directly to a plain .txt file, a structured .csv (perfect for feeding lists directly into the VDP Mail Merge tool), or generate an archival-grade "Searchable PDF" that overlays an invisible, highlightable text layer perfectly over the original pixel artwork.

Offline AI Processing: The Tesseract engine is fully baked into the executable. All document scanning and text recognition happens 100% locally on your machine, ensuring zero cloud API calls and maximum security for sensitive client data.

[2.20] - 2026-07-06
Major Features & Core Upgrades

True Vector Color Space Conversion: Completely overhauled the color conversion engine. Exporting documents to Grayscale, Black & White, or CMYK no longer rasterizes or flattens the file.
Ghostscript Engine Integration: The industry-standard Ghostscript engine is now baked directly into the ReadySetPDF executable. Users no longer need to install external dependencies to get professional-grade color remapping.
Preserved Editability: Because color conversions are now handled mathematically at the vector level, all text remains fully highlightable and editable in Acrobat after export.
Crisp Graphics & Smaller Files: Fixed an issue where converting color spaces would cause graphics to pixelate or become blurry. Vector lines remain infinitely scalable, and file sizes remain lean.
Performance Improvements
Dual-Render Pipeline: The app now intelligently uses two different rendering methods. It continues to use high-speed rasterization for the Live Preview window to prevent UI lag while adjusting settings, but switches to the deep vector Ghostscript engine for the final production export.

## [2.19 - 2026-06-30
ReadySetPDF - Version 2.19 Changelog🚀 New Features & Core ToolsPDF Sanitizer Engine: Added an emergency "PDF Compression Sanitizer" button under the preview window. This tool safely intercepts corrupted commercial PDFs, strips away broken bounding boxes/metadata, and redraws the artwork onto a sterile canvas to instantly fix corrupted files that fail to render.Sequential Numbering & Stamping: Transformed the VDP tab into the Mail Merge/Stamp tab. Users can now generate numbered tickets (e.g., Ticket-[NUM]) or apply static watermarks/stamps without needing an external spreadsheet.Document Duplication Engine: Added the ability to specify a "Record Count" to automatically duplicate a single uploaded PDF $X$ number of times during sequential numbering generation.Excel (.xlsx) Integration: Upgraded the Mail Merge engine to natively parse both standard .csv and Microsoft Excel .xlsx files using openpyxl.Quick CMYK Macro: Added a dedicated "Quick Add: Convert to CMYK" macro button in the Color tab to instantly queue the most common prepress color conversion in a single click.🎯 VDP / Mail Merge UpgradesLive Holographic Targeting: Engineered a real-time visual bounding box on the preview canvas. As users type X/Y coordinates, a dashed blue target box dynamically updates its position. Applied fields turn into solid green confirmation boxes.Tab-Aware Rendering: The holographic targeting boxes now actively listen to the UI state and will seamlessly hide themselves if the user switches to a different tab (like Crop or Monkey) to keep the artwork view unobstructed.Page-Specific Mapping: Fixed a critical routing logic error. Mapped VDP fields now strictly bind to the specific page the user was viewing during setup (e.g., stamping an address only on the back of a 2-page postcard, rather than mirroring it across all pages).Color Conversion Fix: Restored the missing _hex_to_rgb parser, preventing the VDP engine from crashing when applying colored text.🛠️ Stability & Engine FixesBulletproof Preview Architecture: Completely rebuilt the PyMuPDF-to-Tkinter rendering pipeline.Bypassed Tkinter's native PNG parser using io.BytesIO and Pillow (.copy()) to permanently eliminate "Ghost Buffers" (blank white screens).Forced colorspace=fitz.csRGB flattening to prevent "black bar" memory stride crashes when viewing unusually sized documents (like 11x2 banners) saved in CMYK.Diagnostic Safety Nets: Wrapped the preview engine in a diagnostic try/except block. If a severely corrupted PDF breaks the engine, it will now safely abort and print the exact error message above the zoom bar instead of silently freezing the app.Static Stamp Copy Bug: Changed the default VDP generation count from 10 to 1 to prevent the engine from accidentally duplicating a document 10 times when a user simply wanted to apply a single static stamp.🎨 UI, Workflow & BrandingExport Gatekeeper: Added an intelligent fail-safe to the "Build & Save" button. If a user maps a Mail Merge field but forgets to click "Add Step to Stack", the app intercepts the export, warns the user, and offers to auto-apply the step.Windows Taskbar Native Icon Integration: Injected a unique ctypes AppUserModelID (readysetpdf.pro.prepress.2.19). Windows will now correctly display the custom ReadySetPDF icon.ico in the Taskbar instead of the generic Python logo.Asset Pathing & PyInstaller Baking: Hardened the internal directory routing using sys._MEIPASS. The app now flawlessly locates and loads ReadySetPDF logo.jpg and icon.ico regardless of where the .exe is launched from, allowing for seamless single-file distribution via PyInstaller --add-data flags.

## [2.19] - 2026-06-23
- **Added:** Native Feedback Form integrated with Formspree for bug reporting and feature requests.
- **Fixed:** Booklet spread spine-overlay issue by implementing a hard-clipping path for negative gutter offsets.
- **Fixed:** Security flag issue where saved PDFs were incorrectly labeled as "Protected" by Adobe Acrobat.
- **Improved:** Replaced tiny corner crop marks with long, perimeter edge-to-edge bleed marks for easier guillotine alignment.

## [2.18] - 2026-06-21
- **Added:** Perimeter bleed mark generation engine for Monkey and Grid impositions.

## [2.16] - 2026-06-18
- **Fixed:** Booklet spine overlap calculation.
