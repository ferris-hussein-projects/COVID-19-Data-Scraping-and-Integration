# COVID-19-Data-Scraping-and-Integration

## Overview
This script scrapes COVID-19 data from various online sources, processes it into structured CSV files, and loads the data into an SQL Server database. The data includes case numbers, deaths, hospitalizations, vaccination rates, and variants. The script also includes SQL execution to create intermediary tables, clean data using stored procedures, and swap the intermediary tables into production.

## Prerequisites
Before running the script, ensure you have the following installed:
- Python 3.x
- SQL Server with `COVID_DATA` database
- Necessary stored procedures (`dbo.clean_covid_data` and swap SQL script)

## Setup
1. Install dependencies using pip:
   ```sh
   pip install requests beautifulsoup4 pandas pyodbc
   ```
2. Ensure the SQL Server is running and accessible.
3. Update the database connection string if necessary:
   ```python
   cnxn = pyodbc.connect(r'Driver=SQL Server;Server=\\SQLEXPRESS;Database=covid_data;Trusted_Connection=yes;autocommit=True')
   ```
4. Ensure the `sql/ddl.sql` and `sql/swap.sql` scripts exist in the appropriate directory.

## Script Breakdown
### 1. Scraping Data
- Extracts HTML tables from:
  - `https://www.worldometers.info/coronavirus/` (global data)
  - `https://www.worldometers.info/coronavirus/country/us/` (US state-level data)
- Extracts JSON data from Our World in Data for vaccinations, deaths, hospitalizations, variants, and excess mortality.
- Stores scraped data into Pandas DataFrames.

### 2. Processing Data
- Uses `BeautifulSoup` to parse HTML tables.
- Extracts column headers and table rows into DataFrames.
- Saves extracted data as CSV files in the `output` directory.

### 3. Loading Data into SQL Server
- Creates intermediary tables using `sql/ddl.sql`.
- Loads CSV files into intermediary tables.
- Executes `dbo.clean_covid_data` stored procedure to clean data.
- Swaps intermediary tables into production using `sql/swap.sql`.

## Running the Script
To execute the script:
```sh
python script.py
```
Upon execution, the script will:
1. Scrape data and save CSV files.
2. Create intermediary database tables.
3. Load data into SQL Server.
4. Clean the data using a stored procedure.
5. Swap intermediary tables to production.
6. Display runtime statistics.

## Expected Output
- CSV files stored in `output/`
- SQL tables populated in `COVID_DATA` database
- Log messages indicating progress and completion

