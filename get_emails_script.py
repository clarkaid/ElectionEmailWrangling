#Get Emails Script
#CS506 Election Narratives Team A
# Author: Aidan Clark
#3/23/24
#Script for accessing the Gmail API and saving campaign emails into a dataframe

#Importing necessary packages

#Our custom Gmail API functions. See gmail_functions.py for details
from gmail_functions import *

import pandas as pd
import tqdm

#Authenticate and Get Gmail Service Object. May prompt you to authenticate in the web browser
service = gmail_authenticate()
#Troubleshooting: Try deleting token.pickle or checking credentials on Gmail API website

#Get message Ids
#Can limit to particular name/topic using a passed in query
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

emails_df.to_csv("emails_df.csv")


