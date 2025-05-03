# PDF Certificate of Analysis (COA) to CSV Converter

**Transform raw PDF data into clean, analyzable CSVs — a lightweight Python ETL tool built for speed, accuracy, and dashboard-ready outputs.**  

---

## 🚀 About This Project

This project showcases my ability to build practical Python tools that automate data extraction and transformation tasks — turning messy inputs like scanned PDFs into structured datasets ready for analysis.  

If you need someone who can bridge raw operational data to BI dashboards or machine learning pipelines, I create solutions like this: efficient, reproducible, and business-ready.

---

## Features

✅ Automatically parses COA PDFs  
✅ Outputs consolidated CSV files  
✅ Displays real-time progress  
✅ Lightweight, local, no external services required  
✅ Ideal for integration into ETL pipelines or dashboards  

---

## Installation

### Prerequisites

- **Python 3.10.x** (or the version specified in `.python-version`)  
- Recommended: **pyenv** for Python version management ([install guide](https://github.com/pyenv/pyenv))

---

### Setup Steps

```bash
# 1️⃣ Clone this repository
git clone https://github.com/yourusername/pdf-coa-to-csv.git
cd pdf-coa-to-csv

# 2️⃣ Set the Python version (if using pyenv)
pyenv install 3.10.9          # Adjust if .python-version specifies something else
pyenv local 3.10.9

# 3️⃣ Create and activate a virtual environment
python -m venv myenv
source myenv/bin/activate     # On Windows: myenv\Scripts\activate

# 4️⃣ Install dependencies
pip install -r requirements.txt




Usage
Place your COA PDF files into the input/ directory.

Run the script:

bash
Copy
Edit
python pdftocsv.py
Check the output/ folder for the generated coa_data.csv.

The terminal will display progress as it processes each file.

Example
Input:
PDF files placed in input/

Terminal Output:

python-repl
Copy
Edit
Processing file 1 of 5: SampleCOA1.pdf
Extracting data...
Saving progress...
Processing file 2 of 5: SampleCOA2.pdf
...
Done! CSV saved to output/coa_data.csv
Generated CSV Example:

css
Copy
Edit
Sample Name, Date, Result, Units, Status
Sample A, 2024-01-15, 98.7, %, Pass
Sample B, 2024-01-15, 97.2, %, Pass
...
Why This Matters
This project demonstrates:

Custom Python ETL development

Automated data extraction from complex file types

Clean, reproducible, and version-controlled workflows

Outputs ready for analysis, reporting, or dashboard integration

If you need a developer who can design and implement Python solutions for analytics, reporting, and data engineering, this is the kind of work I deliver.

Future Improvements
Add a simple web or GUI front-end

Integrate cloud or database storage

Add error reporting and logs

Expand to handle other document types

License
MIT License.

yaml
Copy
Edit

---

Would you like me to prepare the actual `README.md` file content for copy-paste, or should I generate companion files (like `requirements.txt`) to go with it?
