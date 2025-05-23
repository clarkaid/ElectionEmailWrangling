#CS 506 Election Narratives Team A
#Author: Aidan Clark
#4/13/24
#This is our main set of code for gathering, wrangling, and cleaning email campaign data
#To see the functions that we use, go to fec_functions.py and gmail_functions.py

#This code makes use of two APIs
#Gmail API --> You'll have to set up credentials and save them as credentials.json
#Useful instructions (and some of our source code): https://thepythoncode.com/article/use-gmail-api-in-python

#Federal Election Commission API --> This gives us candidate data, funding, etc.
#You'll need to get your own API Key: https://api.open.fec.gov/developers/

FEC_API_KEY = 0 #Get your own key and fill it in here!

#Imports

from gmail_functions import * #Our gmail functions
from fec_functions import * #Our FEC functions

import pandas as pd
import tqdm

#Returns a dataframe of parsed emails with matched candidate information
#Be wary of candidate matching-- it uses fuzzy string matching and is not 100% correct
def wrangle_emails():
    #First, we need to gather our emails:

    #Authenticate and get Gmail Service Object. May prompt you to authenticate in the web browser
    #Use the email account with the emails that you want to scrape
    service = gmail_authenticate()
    #Troubleshooting: Try deleting token.pickle or checking credentials on Gmail API website

    #Get message Ids
    #Can limit to particular name/topic using a passed in query
    #Max_emails is approximate upper bound
    messageIds = search_messages(service, query = "", max_emails = 4000)

    #Access these emails and save relevant information to a dataframe
    emails_df = pd.DataFrame(columns = ["Date", "Sender", "Subject", "Body"])

    for msg in tqdm.tqdm(messageIds):
        data = df_read_message(service, msg)
        emails_df.loc[len(emails_df)] = data

    #To absolutely ensure that we don't have the same email twice, drop duplicate rows
    emails_df.drop_duplicates(subset = ("Date", "Sender", "Subject", "Body"))

    #Parse email bodies for links
    emails_df["Links"] = emails_df["Body"].apply(find_links)

    #Cleaning emails
    emails_df = emails_df[emails_df["Body"] != "No Body Found"] #Filtering out emails whose bodies we can't parse
    #Spam/ Not related to a particular candidate
    emails_df = emails_df[emails_df["Sender"] != "Google <no-reply@accounts.google.com>"]
    emails_df = emails_df[emails_df["Sender"] != "\"Secure & Prosper\" <today@secureandprosper.com>"]

    #Now, we want to identify each email as coming from a particular candidate
    #For that, we need a dataframe of active Senate candidates

    candidate_df = get_candidates(FEC_API_KEY) #Candidate info

    relevant = ["name", "candidate_id", "party_full", "incumbent_challenge_full", "state",
                "has_raised_funds"]
    
    #Dropping irrelevant columns
    candidate_df = candidate_df.drop(candidate_df.columns.difference(relevant), axis = 1)

    candidate_df = candidate_df.rename(columns = {"name": "full_name"})

    #Now, let's match emails to candidates

    emails_df['candidate_name'] = emails_df['Sender'].apply(lambda x: improved_name_matcher(x, candidate_df))

    #Now, let's add in candidate information for each email

    joined_df = emails_df.merge(candidate_df, how = "left", left_on = "candidate_name", right_on = "full_name")
    joined_df.fillna(value = "No Candidate Found") 
    #Any emails that couldn't be matched, or that don't have a valid email address

    #Notice that this df may include values like:
    #No Body Found
    #No Candidate Found
    #No Funding Found
    #Depending on the analysis you want to do, you should filter these out. We usually do in our analysis
    return joined_df


df = wrangle_emails()
df.to_csv("../data/updated_full_data.csv")