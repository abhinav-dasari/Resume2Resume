# 🚀 ResumeForge AI — Resume Template Builder & Auto-Extractor

**ResumeForge AI** is an intelligent Flask-based web application that automates resume parsing, template formatting, and document management. It extracts structured information from digital and scanned PDF resumes using PyMuPDF and EasyOCR fallback, organizes data into customizable templates, and supports multi-format exports (PDF, CSV, JSON) alongside full user authentication and historical document management.

---

## ✨ Key Features

- 📑 **Dual-Engine PDF Parsing & OCR**:
  - **Fast Digital Extraction**: Native text parsing via `PyMuPDF` (`fitz`) for digital PDFs.
  - **Scanned PDF Fallback**: Automatic image rendering (300 DPI) and optical character recognition via `EasyOCR` when raw text is unavailable.
- 🎯 **Smart Information Extraction**:
  - **Personal & Contact Info**: Name, Email, Phone Number, Location/Address, LinkedIn, GitHub.
  - **Technical Attributes**: Skills matrix, Programming languages, Certifications & Trainings.
  - **Structured Background**: Categorized Education (Postgraduate, Undergraduate, High School, Secondary) with CGPA/Percentages, plus Work Experience & Projects.
- 🎨 **Interactive Resume Template System**:
  - Choose from 4 built-in design layouts:
    - **Modern Minimal** (Clean single-column layout with subtle accent borders)
    - **Professional Classic** (Traditional two-column layout with dedicated sidebar)
    - **Creative Bold** (Vibrant design with gradient accents and bold section headers)
    - **Corporate Clean** (Formal, ATS-friendly structured layout)
  - Live preview and real-time editing of extracted information before exporting.
- 📤 **Multi-Format Document Export**:
  - **PDF**: Dynamically styled PDF rendering matching the selected template layout (via `xhtml2pdf` / `reportlab`).
  - **JSON**: Clean, structured JSON output for API consumption or backups.
  - **CSV**: Tabular data export suitable for ATS importing or spreadsheet analysis.
- 🔒 **User Authentication & Dashboard**:
  - Secure user signup, login, and session management using Werkzeug password hashing.
  - User history dashboard to view, reload, and re-export past resume extractions.
- 🧹 **Privacy & Storage Optimization**:
  - Automated temporary file cleanup for uploaded documents.
  - Dual database engine support (SQLite by default, PostgreSQL for production deployments).

---

## 🛠️ Tech Stack & Architecture

| Layer | Technologies Used |
| :--- | :--- |
| **Backend Framework** | Python 3.8+, Flask, Werkzeug |
| **Database & ORM** | Flask-SQLAlchemy, SQLite (Development), PostgreSQL (Production) |
| **OCR & Parsing** | PyMuPDF (`fitz`), EasyOCR, OpenCV (`opencv-python-headless`), NumPy, PIL/Pillow |
| **Data Processing** | Regex heuristics, Pandas |
| **Export Engines** | `xhtml2pdf`, `reportlab`, Python `csv` & `json` standard libraries |
| **Frontend UI** | HTML5, CSS3, JavaScript (Fetch API / Async Uploads), Jinja2 Templating |

---

## 📂 Directory Structure

```
PEP_SUM_PROJECT/
├── app.py                  # Main Flask application entry point & routes
├── models.py               # SQLAlchemy database models (User, DocumentHistory)
├── resume_templates.py     # Resume template definitions & layout metadata
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variable configuration template
├── autofill.db             # Local SQLite database (auto-generated)
├── ocr/
│   ├── __init__.py
│   └── ocr.py              # PyMuPDF + EasyOCR hybrid extraction engine
├── extractor/
│   ├── __init__.py
│   └── parser.py           # Regex & heuristic parsing rules engine
├── exports/
│   ├── __init__.py
│   └── export.py           # PDF, CSV, and JSON generation logic
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Security, file validation, and cleanup utilities
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout template
│   ├── home.html           # Landing page & file uploader
│   ├── login.html          # Authentication - Login
│   ├── register.html       # Authentication - Register
│   ├── result.html         # Live editor & template renderer
│   └── history.html        # User extraction history dashboard
├── static/                 # Static assets (CSS, JS, images)
├── uploads/                # Temporary directory for uploaded resumes
└── extracted/              # Generated export cache directory
```

---

## ⚙️ Prerequisites & System Requirements

Before running the application, ensure you have:
- **Python**: Version 3.8 or higher.
- **pip**: Package installer for Python.
- **C++ Runtime / Dependencies** (Required by PyMuPDF & EasyOCR):
  - *Windows*: Visual Studio C++ Redistributable.
  - *Linux/macOS*: Standard build tools (`gcc`/`g++`).

---

## 📥 Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd PEP_SUM_PROJECT
   ```

2. **Create and Activate a Virtual Environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the project root (you can copy `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Configure variables inside `.env`:
   ```env
   # Database Connection URL (Optional - defaults to local SQLite if omitted)
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/resume_db

   # Flask Secret Key for Session Security
   SECRET_KEY=your_super_secret_key_here
   ```

---

## 🚀 Running the Application

### 1. Development Mode
Run the application using Python:
```bash
python app.py
```
The server will start at: **`http://127.0.0.1:5000`**

### 2. Production Mode (Gunicorn)
Run using Gunicorn WSGI server:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🌐 API & Route Reference

| Endpoint | Method | Access | Description |
| :--- | :---: | :---: | :--- |
| `/` | GET | Public | Home page with resume upload & template picker |
| `/register` | GET/POST | Public | User account registration |
| `/login` | GET/POST | Public | User authentication login |
| `/logout` | GET | Authenticated | End current session |
| `/upload` | POST | Authenticated | Process PDF upload, run OCR & parser, save history |
| `/result` | GET | Authenticated | Render live editor with extracted data & template |
| `/history` | GET | Authenticated | User dashboard displaying past document extractions |
| `/history/view/<id>` | GET | Authenticated | Load a specific historical document into workspace |
| `/templates` | GET | Public | JSON API listing all available resume templates |
| `/export/json` | GET/POST | Authenticated | Export current resume data as `.json` |
| `/export/csv` | GET/POST | Authenticated | Export current resume data as `.csv` |
| `/export/pdf` | POST | Authenticated | Render and download styled PDF resume |

---

## 🧪 Usage Workflow

1. **Sign Up / Log In**: Create an account or log in to unlock uploading capabilities.
2. **Select Template**: On the home page, select your preferred resume layout style.
3. **Upload PDF Resume**: Drag and drop or upload a PDF document (supports scanned PDFs).
4. **Review & Edit**: On the results page, review the auto-extracted fields and edit any information if required.
5. **Export**: Click the download buttons to get your updated resume in **PDF**, **JSON**, or **CSV** formats.
6. **Dashboard Access**: Access the **History** page anytime to re-download or inspect previous uploads.

---

## 🛡️ Data Privacy & Security

- Passwords are securely hashed using **PBKDF2 / SHA-256** via Werkzeug.
- Uploaded resumes undergo automatic file cleanup after processing to prevent unnecessary disk retention.
- Upload file validation limits accepted files strictly to `.pdf` under 10 MB.

---

## 📝 License

This project is open-source under the MIT License. Feel free to customize and extend it for your own requirements.
