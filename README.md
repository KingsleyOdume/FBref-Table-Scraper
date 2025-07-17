⚽ FBref Table Scraper

A sleek Flask web application that scrapes football stats tables from [FBref.com](https://fbref.com/), giving you clean, downloadable data in CSV format with a searchable and responsive UI.

---

🚀 Features

- ✅ Scrape Stats** from any FBref team/player page
- 📋 Select Table Type** (Matches, Shooting, Passing, etc.)
- 🔎 Searchable + Paginated Table** using Bootstrap Table
- 📥 Download as CSV**
- 📱 Responsive UI** with Bootstrap 5
- ☁️ Deployable to PythonAnywhere**

---

🛠 Tech Stack

- Python 3.x
- Flask
- Pandas
- BeautifulSoup4
- lxml
- Bootstrap 5
- Bootstrap Table
- Deployed via PythonAnywhere

---

🔧 Local Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/fbref-scraper.git
cd fbref-scraper
Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies
pip install -r requirements.txt
Run the Flask app
flask run
Visit
Open your browser and go to:
http://127.0.0.1:5000/submit-source
