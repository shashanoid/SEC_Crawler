import datetime
import feedparser
import time
from iexfinance import Stock
import requests
import bs4
import smtplib
import openpyxl
import xml.etree.ElementTree as ET
import http.client, urllib.request, urllib.parse, urllib.error, base64
from pymsgbox import *

import re
from twilio.rest import TwilioRestClient
import io
import itertools as IT

symbols = []
biotechs = []

stocks_sent = []
CompanyNameList = []
TickerList = []
ProcessedList = []
ReportingOwnerRelationshipList = []
TransactionSharesList = []
PricePerShareList = []
TotalValueList = []
transactionCodeList = []
DorIList = []
portfolio = []
bought_price = []
stocks_sent = []
checked = []
#----------------------------------------------------------------------------------#
#PULL FROM STOCK SCREEN EXCEL AND CURRENT PORTFOLIO

wb = openpyxl.load_workbook(filename = 'stock_screenv2.xlsx')
sheet = wb.active

print('Getting info from cells ...')
for row in range(2, sheet.max_row + 1):
    company_name      = sheet['A' + str(row)].value
    ticker            = sheet['B' + str(row)].value
    CompanyNameList.append(company_name)
    TickerList.append(ticker)
wb.save('stock_screenv2.xlsx')

print('Adding biotech tickers ...')
res = requests.get('https://www.biopharmcatalyst.com/calendars/fda-calendar')
soup = bs4.BeautifulSoup(res.text, 'lxml')

for symbol in soup.find_all('td', class_= 'js-td--ticker'):
    symbol = symbol.get_text().replace('\n','')
    try:
        if symbol not in symbols:
            symbols.append(symbol)
            ticker = Stock(symbol)
            company_name = ticker.get_company_name()
            CompanyNameList.append(company_name)
            TickerList.append(ticker)
    except:
        print('Had some fucked up hero ticker: ',symbol)
        pass

lower = [x.lower() for x in CompanyNameList]
lower = [x.replace('.com', ' com') for x in lower]
lower = [x.replace('.', '') for x in lower]
lower = [x.replace(',', '') for x in lower]
lower = [x.replace('-', ' ') for x in lower]
lower = [x.replace('\xa0', ' ') for x in lower]
if '&amp;' in lower:
    lower = lower.replace('&amp;', '&')
if '&#39;' in lower:
    lower = lower.replace('&#39;', "'")            

 
with open('portfolio.txt', 'r') as f:
    stocks = f.readlines()
    for item in stocks:
        item = item.strip()
        portfolio.append(item)

with open('bought_price.txt', 'r') as f:
    price = f.readlines()
    for item in price:
        item = item.strip()
        bought_price.append(item)
        
print('Complete.',len(lower),'stocks being monitored\n') 

def eight_k():
    eight_dic = {
        'Item 1.03': 'Bankruptcy or Receivership',
        'Item 1.04': 'Mine Safety - Reporting of Shutdowns and Patterns of Violations',
        'Item 2.04': 'Triggering Events That Accelerate or Increase a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement',
        'Item 2.05': 'Costs Associated with Exit or Disposal Activities',
        'Item 2.06': 'Material Impairments',
        'Item 3.01': 'Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard; Transfer of Listing',
        'Item 4.02': 'Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review',
        'Item 5.04': 'Temporary Suspension of Trading Under Registrant"s Employee Benefit Plans',
        'Item 6.04': 'Failure to Make a Required Distribution',}
    a = feedparser.parse('http://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-k&company=&dateb=&owner=include&start=0&count=100&output=atom')
    time.sleep(2)
    today = datetime.datetime.today()
    for entry in range(0,99):
        try:
            company_name = a.entries[entry].title.lower()
            company_summary = a.entries[entry].summary
            for key in eight_dic:
                
                if key in company_summary:
                    last25 = slice(-25, None)
                    
                    if company_name[last25] not in stocks_sent:
                        day = a.entries[entry].updated
                        day = day.split('T')
                        t = day[0]
    
                        if t in str(today):
                            try:
                               cik = company_name[company_name.find("(")+1:company_name.find(")")]
                               stocks_sent.append(company_name[last25])    
                               headers = {'Ocp-Apim-Subscription-Key': 'GETYOUROWNSUBSCRIPTIONKEY',}
                               params = urllib.parse.urlencode({})
                               conn = http.client.HTTPSConnection('services.last10k.com')
                               conn.request("GET", "/v1/company/"+cik+"/ticker?%s" % params, "{body}", headers)
                               responsed = conn.getresponse()
                               with responsed as response:
                                   html_content = response.read()
                                   ticker = html_content
                               ticker = str(ticker)
                               ticker = ticker.replace("b","")                          
                               ticker = ticker.replace('"','')  
                               ticker = ticker.replace("'","")  
                               ticker = ticker.replace(" ","")
                               ticker = ticker.upper()
                               symbol = ticker
                               conn.close()
                               desc = eight_dic.get(key)
                               ticker = Stock(ticker)
                               current_price = ticker.get_price()
                               message = company_name+'\n'+symbol+'\n$'+str(current_price)+'\n\n'+key+'\n'+desc
                               confirm(text=message, title='Short Option', buttons=['OK'])
                               print(key,'\n',desc,'\n~~~~~~~~~~~~~~~~~~~~')
                            except:
                               print('research fail: ',company_name)   
                               pass
        except:
            print('da fuk? Re 8k')
            pass
#----------------------------------------------------------------------------------#
#COMMUNICATION FUNCTIONS

def email(symbol, address, current_price, company_name, message):
    today = datetime.datetime.today()
    today = today.strftime('%m/%d/%Y %I:%M %p')
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login('YOUREMAILADDRESS@gmail.com', 'YOURPASSWORD')
    print(smtpObj.sendmail('adamthemormon@gmail.com',\
                     'YOURFRIEND@gmail.com; SECONDFRIEND@gmail.com; YOUDONTHAVEATHIRDFRIEND@gmail.com,\
                     'Subject: ' + ' | SEC FILING: (' + str(tradingSymbol) + ')'+  str(company_name) + '.\n ' +
                     str(company_name) + '(' + str(tradingSymbol) +')' + ' @ ' + str(current_price) + 'has triggered a notification ' + str(today) + ' due to a Form 4 SEC filing that was just published:\n\n' + str(link) + '\n'+nsymbol, address, current_price, company_name, message+'\n\nYou are receiving this b/c you requested to do so from reddit.com/user/TheSuicideBot/. Neither this email address or Reddit account are routinely monitored, but respond to either for feedback or to be removed and it will eventually be processed.\n\nThis script strictly monitors and notifes folk of SEC Form 4 filings. It is not reliable, not a professional recommendation, and dont blame me for your poor life decisions of lack of due diligence. Please verify at the least that the notification is for the appropriate company as this script may not 100% match the right company (ex Johnson LLC v Johnson Inc). \n\n As I write this, the intent of the script was to notify you of an Officer who purchased stocks under his own volition and not as a benefit or other financial whatever.'))
    smtpObj.quit()
    
#----------------------------------------------------------------------------------#
#SCAN EDGAR AND SCRAPE XML

def scrape_xml(link,company_name):
    TotalValue = 0
    transactionCodeList = []
    DorIList = []
    TitleList = []
    today = datetime.datetime.today()
    today = today.strftime('%m/%d/%Y %I:%M %p')
    headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
    "accept-encoding": "gzip, deflate, sdch",
    "accept-language": "en-US,en;q=0.8",
    }
    
    explain = {'P' : 'Open market or private purchase of non-derivative or derivative security',
                'S' : 'Open market or private sale of non-derivative or derivative security',
                'V' : 'Transaction voluntarily reported earlier than required',
                'A' : 'Grant, award or other acquisition',
                'D' : 'Disposition to the issuer of issuer equity securities',
                'F' : 'Payment of exercise price or tax liability by delivering or withholding securities incident to the receipt of a security issued',
                'I' : 'Discretionary transaction resulting in acquisition or disposition of issuer securities',
                'M' : 'Exercise or conversion of derivative security exempted Derivative Securities Codes',
                'C' : 'Conversion of derivative security',
                'E' : 'Expiration of short derivative position',
                'H' : 'Expiration of long derivative position with value received',
                'O' : 'Exercise of out-of-the-money derivative security',
                'X' : 'Exercise of in-the-money or at-the-money derivative security',
                'G' : 'Bona fide gift',
                'L' : 'Small acquisition',
                'W' : 'Acquisition or disposition by will or the laws of descent and distribution',
                'Z' : 'Deposit into or withdrawal from voting trust',
                'J' : 'Other',
                'K' : 'Transaction in equity swap or instrument with similar characteristics',
                'U' : 'Disposition pursuant to a tender of shares in a change of control transaction',
    }                

    res = requests.get(link, headers=headers)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    for a in soup.find_all('a'):
        if a.getText()[-4:] == '.xml':
            address = 'http://www.sec.gov' + a['href']
            res = requests.get(address, headers=headers, timeout=None)
            tree = ET.fromstring(res.content)
            try:
                isOfficer = tree.find('reportingOwner/reportingOwnerRelationship/isOfficer').text
                if not isOfficer:
                    isOfficer = 'I shot the Deputy'
            except:
                isOfficer = "0"
                pass
            transactionCode = tree.findall('nonDerivativeTable/nonDerivativeTransaction/transactionCoding/transactionCode')
            if not transactionCode:
                try:
                    transactionCode = tree.findall('derivativeTable/derivativeTransaction/transactionCoding/transactionCode')
                except:
                    transactionCode = "0"
                    pass
            
            tradingSymbol = tree.find('issuer/issuerTradingSymbol')
            ticker = tradingSymbol.text.lower()
            symbol = str(ticker.upper())
            print(company_name.title() + ' (' + symbol + ') at ' + str(today))

            transactionShares = tree.findall('nonDerivativeTable/nonDerivativeTransaction/transactionAmounts/transactionShares/value')

            if transactionShares == None:
                try:
                    transactionShares = tree.findall('derivativeTable/derivativeTransaction/transactionAmounts/transactionShares/value')
                except:    
                    transactionShares = []
                    pass

            transactionPricePerShare = tree.findall('nonDerivativeTable/nonDerivativeTransaction/transactionAmounts/transactionPricePerShare/value')
            
            if transactionShares == None:
                try:
                    transactionShares = tree.findall('derivativeTable/derivativeTransaction/transactionAmounts/transactionPricePerShare/value')
                except:    
                    transactionShares = []
                    pass

            DorI = tree.findall('nonDerivativeTable/nonDerivativeTransaction/ownershipNature/directOrIndirectOwnership/value')

            if not DorI:
                try:
                    DorI = tree.findall('derivativeTable/derivativeTransaction/ownershipNature/directOrIndirectOwnership/value')               
                except:
                    DorI = []
                    pass
            
            for price, shares, direct, code in zip(transactionPricePerShare, transactionShares, DorI, transactionCode):
                if explain[code.text]:
                    #direct.text == 'D' and 
                    print('Shares: ',shares.text)
                    TotalValue = TotalValue + float(shares.text)*float(price.text)
                    print('Total value: ',TotalValue)
                    shares = shares.text
                    
                else:
                    pass
                
            for code in transactionCode:
                transactionCodeList.append(code.text)
            for item in DorI:
                DorIList.append(item.text)
            
            
                
            if '2' in isOfficer:
                print ('Director purchase')
            elif '1' in isOfficer:
                print ('Officer purchase')

            elif '0' in isOfficer:
                print ('Neither Officer or Director')
            elif isOfficer != '1' or '2' or '0':
                print('Officer overboard --- or maybe more!', isOfficer)
            if 'D' in DorIList:
                print('Direct Purchase')
            elif 'I' in DorIList:
                print('Indirect Purchase')
            else:
                print('D or I value fubar')

            print('Transaction codes: ' + str(transactionCodeList))
            
            for key in explain:
                if key in transactionCodeList:
                    print(explain.get(key))
                    
            print ('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

            if 'P' in transactionCodeList:
            #and ticker not in portfolio:
                #isOfficer == str(1) and    and TotalValue > 10000  and 'D' in DorIList 
                
                with open('portfolio.txt', 'a') as f:
                    f.write(ticker + '\n')
                ticker = Stock(ticker)
                current_price = str(ticker.get_price())
                with open('bought_price.txt', 'a') as f:
                    f.write(current_price + '\n')
                message = 'Buy Opportunity\n' + company_name.capitalize() + '\nTicker symbol: ' + symbol + '\n\nCurrent price: $'+ current_price + '\n\nOfficer: ' + isOfficer + '\n Total Value: '+str(TotalValue)
                print(address)
                print(message)
                if confirm(text='Want to email with your friends?', title='Insider Buy!', buttons=['YES', 'NO']) == 'YES':
                    email (symbol, address, current_price, company_name, message)
                    print('~~~~~~~~~~~~~~~~\nemail!!!!\n~~~~~~~~~~~~~~~~~~~~~~~')

def edgar_feed(url):
    try:
        d = feedparser.parse(url)
        time.sleep(2)
        for entry in range(0,99):
            company_name = d.entries[entry].title.lower()
            company_name = company_name.split('- ')
            company_name = company_name[1].split(' (')
            company_name = company_name[0]
            company_name = company_name.replace('.com', ' com')
            company_name = company_name.replace('.', '')
            company_name = company_name.replace(',', '')
            if '&amp;' in company_name:
                company_name = company_name.replace('&amp;', '&')
            if '&#39;' in company_name:
                company_name = company_name.replace('&#39;', "'")            
            end = ['inc' , '& co' , 'corp', 'lp', 'llc', 'co', 'plc', 'lp', 'corporation', 'fund', 'incorporated', 'ltd', 'trust']
            if company_name.split()[-1] in end:
                company_name = company_name.split()[:-1]
                company_name = ' '.join(company_name)
            for s in lower:
                if company_name in s and d.entries[entry].title[0:1:] == '4': 
                    link = d.entries[entry].link
                    last50 = slice(-50, None)
                    if link[last50] not in stocks_sent:
                      scrape_xml(link,company_name)
                      stocks_sent.append(link[last50])
                else:
                    pass
    
    except Exception as e:
       pass

print ('monitoring feed...')
run_counter = 0
url = 'http://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&dateb=&owner=only&start=0&count=100&output=atom'
def job():
    global run_counter
    run_counter += 1
    time.sleep(2)
    if run_counter % 25 == 0:
        print ('Completed ' + str(run_counter) + ' passes.')
        print ('--------------')

    edgar_feed(url)
    eight_k()

while True:
    job()
    