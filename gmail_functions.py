#Gmail Functions
#CS 506 Election Narratives Team A
#Author: Aidan Clark
#A set of functions to use the Gmail API to process campaign emails
#Some of these functions are modified versions of functions from this article:
# https://thepythoncode.com/article/use-gmail-api-in-python

#Loading necessary libraries
#For authentication:
from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
from google.auth.transport.requests import Request 
import pickle 
import os.path 

#For decoding:
from base64 import urlsafe_b64decode

#For body parsing
import re
import requests
from bs4 import BeautifulSoup

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] 
our_email = "_____@gmail.com" #Fill in your email here!


#Authenticates access to the gmail and returns a Gmail service object
def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


#Using query as a filter and the gmail service object, returns the message ids of all the emails that match query
#Returns max_emails-- max_emails should be a multiple of 100 or whatever number emailsPerPage is set to
def search_messages(service, query, max_emails):
    emailsPerPage = 100
    max_pages = max_emails // emailsPerPage
    page_counter = 1
    result = service.users().messages().list(userId='me',q=query, maxResults = emailsPerPage).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while ('nextPageToken' in result):
        page_token = result['nextPageToken']
        page_counter += 1
        if page_counter > max_pages:
            break #Ensures that we only get the specified number of emails
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token, maxResults = emailsPerPage).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
            
    return messages

#Takes a gmail service object and its parts attribute and recursively searches for email body
#Returns decoded email body
def df_parse_parts(service, parts):
    #There can be a lot of information in parts-- we want bodies
    if parts:
        for part in parts:
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")

            #Body of an email may be recursively hidden inside the data structure
            #So, check if there are parts inside our current part
            if part.get("parts"):
                # recursively call this function when we see that a part
                # has parts inside
                df_parse_parts(service, part.get("parts"))

            #If we find plain text or html
            if mimeType == "text/plain":
                # if the email part is text plain
                #save file
                if data:
                    text = urlsafe_b64decode(data).decode()
                    return text
                
            #Html text email
            elif mimeType == "text/html":
                print("html")
                return urlsafe_b64decode(data)
                    
    return "No Body Found" #Not sure if this will ever happen, but I want to make sure we have a failsafe

#Takes a service object and a message id and extracts info from the email, to be appended to a Pandas df
#Returns list: [Date, Sender, Subject, Body]
def df_read_message(service, message):
    #Using our service object, access the API to get the message object for the specified message id
    msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()

    # Because life is annoying, parts can be the message body, or attachments.
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")

    if headers:
        #Iterating through basic email info
        for header in headers:
            name = header.get("name") #Name of current attribute
            value = header.get("value") #Value of current attribute

            #If current attribute is "from"
            if name.lower() == 'from':
                sender = value
                
            #If current attribute is subject
            if name.lower() == "subject":
                subject = value

            #If current attribute is date
            if name.lower() == "date":
                date = value

    body = df_parse_parts(service, parts) #Recurses through email structure looking for body

    return {"Date": date, "Sender": sender, "Subject": subject, "Body": body}

#Takes a string representing an email body and uses a regex to find all the urls in the body
#Returns a list of strings
def find_links(s):
    return re.findall(r"(?P<url>https?://[^\s]+)", s)

#Takes a list of urls and returns a list of the website titles of those links
def get_website_titles(link_list):
    titles = []
    for url in link_list:
        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.text, 'html.parser')
        title = soup.find('title')
        titles.append(title.get_text())

    return titles