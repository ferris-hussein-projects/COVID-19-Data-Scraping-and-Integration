from re import S
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import pandas as pd
import os
import csv
import sys
import pyodbc


start = datetime.now()

dir_path = os.getcwd() 
dir_path += '\output'

covid_url = "https://www.worldometers.info/coronavirus/"
states_url = "https://www.worldometers.info/coronavirus/country/us/"
vacc_dose_url = "https://covid.ourworldindata.org/data/internal/megafile--vaccinations-bydose.json"
vacc_url = "https://covid.ourworldindata.org/data/internal/megafile--vaccinations.json"
deaths_url = "https://covid.ourworldindata.org/data/internal/megafile--deaths.json"
hospital_url = "https://covid.ourworldindata.org/data/internal/megafile--hospital-admissions.json"
booster_url = "https://covid.ourworldindata.org/data/internal/megafile--vaccinations-boosters.json"
variants_url = "https://covid.ourworldindata.org/data/internal/megafile--variants.json"
mortality_url = "https://covid.ourworldindata.org/data/internal/megafile--excess-mortality.json"
auxiliary_url = "https://covid.ourworldindata.org/data/internal/megafile--auxiliary.json"
cases_tests_url = "https://covid.ourworldindata.org/data/internal/megafile--cases-tests.json"

cnxn = pyodbc.connect(r'Driver=SQL Server;Server=.\SQLEXPRESS;Database=covid_data;Trusted_Connection=yes;autocommit=True')
cnxn.autocommit = True

def url_processor(url, val):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    table = soup.find("table", attrs={"id": val})
    if table is None:
        #print("hi")
        table = soup.find('table', {'class': val})
    return table
    
    
def table_processor(table):
    try:
        head = table.thead.find_all("th")

        cols = []
        for i in head:
            cols.append(i.text)
        
        body = table.tbody.find_all("tr")
        data = []
        for i in range(1,len(body)):
            row = []
            for j in body[i].find_all("td"):
                row.append(j.text.replace("\n","").strip())
            data.append(row)
        df = pd.DataFrame(data,columns=cols)
    except: #column processing issues
        body = table.tbody.find_all("tr")
        data = []
        for i in range(1,len(body)):
            row = []
            for j in body[i].find_all("td"):
                row.append(j.text.replace("\n","").strip())
            data.append(row)
        df = pd.DataFrame(data)
    return df

def csv_processor(df, csv_name):
    df.to_csv(dir_path + '\\' + csv_name + '.csv')

def processCSV(all_csv):
    for csv_name in all_csv:
        this_csv = dir_path +'\\' + csv_name + '.csv'
        if csv_name == 'continents' or csv_name == 'countries' or csv_name == 'states':
            cursor = cnxn.cursor()
            with open (this_csv, 'r') as f:
                if csv_name == 'states':
                    sql = "insert into " + csv_name + "_new values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        cursor.execute(sql,tuple(row[2:16]))
                else:    
                    sql = "insert into " + csv_name + "_new values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        cursor.execute(sql,tuple(row[2:11]))
                    print("Inserted " + csv_name + '.csv')
            cnxn.commit()
            cursor.close()
        else: #all other csv
            cursor = cnxn.cursor()
            with open (this_csv, 'r') as f:
                reader = csv.reader(f)
                columns = next(reader)
                col_len = len(columns)-1
                sql = "insert into " + csv_name + "_new values (?" + ',?' * col_len + ')'
                for row in reader:
                    cursor.execute(sql,tuple(row))
                print("Inserted " + csv_name + '.csv')
            cnxn.commit()
            cursor.close()
        
all_csv = []

table = url_processor(covid_url, "main_table_countries_today")
df = table_processor(table)
continent = df.iloc[:5,:]
countries = df.iloc[6:,:]
csv_processor(continent, 'continents')
csv_processor(countries, 'countries')

#states
table = url_processor(states_url, "usa_table_countries_today")
states = table_processor(table)
csv_processor(states, 'states')

jsonData = requests.get(vacc_dose_url).json()
vacc_d = pd.DataFrame(jsonData)
csv_processor(vacc_d, 'vaccination_dose')

jsonData = requests.get(vacc_url).json()
vacc = pd.DataFrame(jsonData)
csv_processor(vacc, 'vaccination')

jsonData = requests.get(deaths_url).json()
dts = pd.DataFrame(jsonData)
csv_processor(dts, 'deaths')

jsonData = requests.get(hospital_url).json()
hos = pd.DataFrame(jsonData)
csv_processor(hos, 'hospital')

jsonData = requests.get(booster_url).json()
boos = pd.DataFrame(jsonData)
csv_processor(boos, 'booster')

jsonData = requests.get(variants_url).json()
var = pd.DataFrame(jsonData)
csv_processor(var, 'variants')

jsonData = requests.get(mortality_url).json()
mor = pd.DataFrame(jsonData)
csv_processor(mor, 'mortality')

jsonData = requests.get(auxiliary_url).json()
aux = pd.DataFrame(jsonData)
csv_processor(aux, 'auxiliary')

jsonData = requests.get(cases_tests_url).json()
ct = pd.DataFrame(jsonData)
csv_processor(ct, 'cases_tests')

print("Scraped data to CSV's.")
#DDL Step
fd = open(os.getcwd() + '\sql\ddl.sql','r')
sql = fd.read()
fd.close
cursor = cnxn.cursor()
cursor.execute(sql)
cursor.close()
print("Created intermediary table shells.")

#load data
print("Insert Starting...")
all_csv.extend(['continents', 'countries', 'states', 'vaccination_dose', 'vaccination', 'deaths',
                'hospital', 'booster', 'variants', 'mortality', 'auxiliary', 'cases_tests'])
processCSV(all_csv)
print("Insert Complete.")

#clean data using sp
cursor = cnxn.cursor()
cursor.execute('use COVID_DATA; execute dbo.clean_covid_data')
cursor.close()
print("Cleaned inserted data using stored procedure.")

#swap data
fd = open(os.getcwd() + '\sql\swap.sql','r')
sql = fd.read()
fd.close
cursor = cnxn.cursor()
cursor.execute(sql)
cursor.close()
print("Swapped intermediary tables to production.")

end = datetime.now()
print('Refresh Complete.\n')
print("--- Total Runtime: " + str(end-start) + " ---")
