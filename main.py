from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
from scraper import scrape_premier_league, fetch_html_with_playwright
import io
from fastapi.responses import FileResponse


app = FastAPI()
templates = Jinja2Templates(directory="templates")



@app.get("/")
def root():
    return {"message": "FBref Premier League API. Use /scrape, /matches, or /submit-source"}

@app.post("/scrape")
def run_scraper():
    success = scrape_premier_league()
    if success:
        return {"status": "success", "message": "Scraping completed and matches.csv saved."}
    else:
        return {"status": "error", "message": "No data scraped."}

@app.get("/matches")
def get_matches():
    if not os.path.exists("matches.csv"):
        return JSONResponse(content={"error": "matches.csv not found. Run /scrape first."}, status_code=404)

    try:
        df = pd.read_csv("matches.csv")
    except pd.errors.EmptyDataError:
        return JSONResponse(content={"error": "matches.csv is empty. Run /scrape to get data."}, status_code=404)

    df_clean = df.where(pd.notnull(df), None)
    result = df_clean.to_dict(orient="records")
    return JSONResponse(content=result)



@app.get("/submit-source", response_class=HTMLResponse)
def submit_source_form(request: Request):
    return templates.TemplateResponse("submit_source.html", {"request": request})

@app.post("/process-source", response_class=HTMLResponse)
def process_source(request: Request, url: str = Form(...), table_type: str = Form(...)):
    if not url.startswith("https://fbref.com/"):
        return templates.TemplateResponse("submit_source.html", {
            "request": request,
            "error": "Invalid URL. Only FBref.com links are allowed."
        })

    try:
        html = fetch_html_with_playwright(url)

        tables = pd.read_html(io.StringIO(html), match=table_type)
        if not tables:
            raise ValueError(f"No table found for table type: {table_type}")

        df = tables[0]

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [' '.join(col).strip() for col in df.columns.values]

        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df.dropna(how='all', inplace=True)
        df_clean = df.where(pd.notnull(df), None)

        df_clean.to_csv("custom_data.csv", index=False)

        table_html = df_clean.to_html(classes="table table-bordered table-striped table-hover", index=False, border=0)

        return templates.TemplateResponse("result_table.html", {
            "request": request,
            "table_html": table_html,
            "table_type": table_type,
            "url": url
        })

    except Exception as e:
        print("⚠️ ERROR in /process-source:", str(e))
        return templates.TemplateResponse("submit_source.html", {
            "request": request,
            "error": f"Failed to scrape data: {str(e)}"
        })


@app.get("/download-csv")
def download_csv():
    csv_path = "custom_data.csv"
    if os.path.exists(csv_path):
        return FileResponse(csv_path, media_type='text/csv', filename="fbref_data.csv")
    else:
        return JSONResponse(content={"error": "CSV file not found"}, status_code=404)
