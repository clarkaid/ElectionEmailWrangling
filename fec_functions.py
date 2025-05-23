#FEC Functions
#CS 506 Election Narratives Team A
#Author: Aidan Clark
#4/13/24
#This is a set of functions for accessing Senate candidate data from the Federal Election Commmission API
#To use these, you'll need an API key and the FEC documentation: https://api.open.fec.gov/developers/

#Imports
import requests #For working with API
import pandas as pd
import json #Our results come back as jsons
from thefuzz import fuzz #Popular fuzzy string matching package
from thefuzz import process
import time

#Takes an API key and, using the FEC API and paging through if necessary, returns a pandas dataframe
#with information about all active Senate candidates
def get_candidates(MY_API_KEY):
    api_link = "https://api.open.fec.gov/v1/candidates/"

    #Parameters for API call
    params = {
    "page": 1,
    "per_page": 100,
    "election_year": 2024, #Only candidates running in 2024
    "is_active_candidate": True, #Only active candidates
    "office": "S", #Only Senate candidates
    "sort": "name",
    "sort_hide_null": False,
    "sort_null_only": False,
    "sort_nulls_last": False,
    "api_key": MY_API_KEY
    }

    more_pages = True #Boolean to stop paging through
    fec_df = pd.DataFrame() #Dataframe to store candidate info
    #Pages through candidate list and adds records to fec_df
    while more_pages:
        r = requests.get(api_link, params) #Make API call

        if r.status_code == 200:
            #Call was successful
            params["page"] = params["page"] + 1 #Next call will go to next page

            #Check whether next call will go beyond total number of pages
            if params["page"] > r.json()["pagination"]["pages"]:
                more_pages = False

            recs = r.json()['results'] #Access candidate data part of json
            recs_df = pd.json_normalize(recs) #Convert json to df
            fec_df = pd.concat([fec_df, recs_df], ignore_index = True)

        else:
            #Call failed, stop making calls
            more_pages = False


        #time.sleep(10) #So as to not exceed our API rate limit
    return fec_df


#Takes an API key and returns a dataframe with candidate id, name, and total receipts for the 2024 election cycle
#Receipts are the amount of money that a candidate has received
def get_receipts(MY_API_KEY):
    link = "https://api.open.fec.gov/v1/candidates/totals/"

    params = {
        "page": 1,
        "per_page": 100,
        "cycle": 2024, #Only data for 2024,
        "office": "S", #Only Senate candidates
        "is_active_candidate": True, #Only active candidates-- maybe look into this more later
        "election_full": False,
        "sort": "name",
        "sort_hide_null": False,
        "sort_null_only": False,
        "sort_nulls_last": False,
        "api_key": MY_API_KEY
    }

    more_pages = True #Boolean to stop paging through
    receipts_df = pd.DataFrame() #Dataframe to store candidate info
    #Pages through candidate list and adds records to fec_df
    while more_pages:
        r = requests.get(link, params) #Make API call

        if r.status_code == 200:
            #Call was successful
            params["page"] = params["page"] + 1 #Next call will go to next page

            #Check whether next call will go beyond total number of pages
            if params["page"] > r.json()["pagination"]["pages"]:
                more_pages = False

            recs = r.json()['results'] #Access candidate data part of json
            recs_df = pd.json_normalize(recs) #Convert json to df
            receipts_df = pd.concat([receipts_df, recs_df], ignore_index = True)

        else:
            #Call failed, stop making calls
            print("Call failed")
            more_pages = False

        time.sleep(10) #Useful to avoid going past rate limits


    trimmed_df = receipts_df.drop(receipts_df.columns.difference(["candidate_id", "name", "receipts"]), axis = 1)

    return trimmed_df
    

#Takes the two dataframes (candidates and receipts) from the previous two functions
#Merges on candidate id, removes duplicates on candidate id, drops irrelevant columns
#Returns resulting df
def mergeCleanCandidate(candidates_df, receipts_df):
    joined_df = candidates_df.merge(receipts_df, how = "left", on = "candidate_id")
    joined_df = joined_df.fillna(value = "No Funding Found")

    joined_df = joined_df.drop_duplicates(subset = ["candidate_id"]) #Drop duplicates on candidate_id

    relevant = ["name", "candidate_id", "party_full", "incumbent_challenge_full", "state",
                "has_raised_funds", "receipts"]
    #Dropping irrelevant columns
    joined_df = joined_df.drop(joined_df.columns.difference(relevant), axis = 1)

    #Renaming as needed
    joined_df = joined_df.rename({"party_full": "party", "incumbent_challenge_full": "incumbent_challenge",})

    return joined_df



#Takes an email address and the candidates dataframe
#Uses fuzzy string matching to find the most likely candidate corresponding to that address
def improved_name_matcher(email, candidates_df):
    #There are some email addresses that sometimes elude matching. 
    #We'll store a dictionary of the ones that we notice
    #Note 4/13/24: These emails were put here before we started only looking at the email address
    #Our string matcher would almost certainly still match these, but it doesn't hurt to ensure that!
    
    known_emails = {
        "<info@email.bobcasey.com>": "CASEY, ROBERT P. JR.",
        "<info@hungcaoforva.com>": "CAO, HUNG",
        "info@lisabluntrochester.com": "BLUNT ROCHESTER, LISA",
        "info@e.tammybaldwin.com": "BALDWIN, TAMMY",
        "josh@hawleyformo.com": "HAWLEY, JOSHUA DAVID SEN",
        "info@action.rosenfornevada.com>": "ROSEN, JACKY"
    }
    for x in known_emails:
        if x in email:
            return known_emails[x]
    
    #First, remove any irrelevant parts of the email, including the sender name before the address
    #We remove this because often emails are sent "from" someone who is not the actual candidate
    #Useful place for next analysis: who are these other people?
    try:
        email = email.upper().split("<", 1)[1]
    except:
        return "No Candidate Found"
    
    #All words, punctuation, symbols that don't have anything to do with the candidate's NAME
    useless = ["INFO@", "TEAM@", ".COM", ".ORG", "CONTACT@", "REPLY@", "TEAM", "<", ">", "@", ",", "\"",
               "CONGRESS", "SENATE", "SENATOR", "UPDATE", "EMAIL", "2024", "ALERT", "WHITE HOUSE", "CAMPAIGN", 
               "REELECTION", "TRUMP", "REPUBLICAN", "DEMOCRAT", "POLL", "BALLOT", "BREAKING", "CRITICAL", "OFFICIAL",
               "MANAGER"]
    for x in useless:
        email = email.replace(x, "")

    #The scorer we're using does a couple different things
    # partial --> compares substrings, which is good, since the name might only be a small part of the substring
    # token sort --> sorts tokens alphabetically, so the different orders do not matter
    return process.extractOne(email, candidates_df['full_name'], scorer = fuzz.partial_token_sort_ratio)[0]