# ElectionEmailWrangling

## Overview
This scripts in this repository were originally created in Spring 2024 as part of a team project for the course Tools for Data Science, taught by Lance Galletti. I and a team of four others worked on a project for a client researching misinformation in Senate campaign emails. As the first team to work on this project, we wished to create infrastructure for wrangling and analyzing campaign emails and to undertake a preliminary analysis of trends amongst these emails. My work on this project focused largely on gathering and cleaning data from campaign emails, using the Gmail API, and from the Federal Election Commmission's (FEC) candidate database. I include the relevant scripts for this task here, as an example of my prior work. See below for details about my implementations and for instructions about how to use these scripts yourself.

## Data Wrangling

### Emails
We used the Gmail API to parse the emails sent to the project's email account and save relevant email information (Date, Sender, Subject, Body) to a Pandas dataframe. To do this, we used Google Cloud APIs to create an authentication token, and then we wrote functions and scripts to query the Gmail API and parse the results. We used [this tutorial](https://thepythoncode.com/article/use-gmail-api-in-python) as a guide. The functions we wrote are in [`scripts/gmail_functions.py`](scripts/gmail_functions.py). 

### Candidates
To create a database of active Senate candidates, we used the Federal Election Commission's (FEC) candidate database. They maintain an API that allows one to query information about any active candidate. We wrote functions to gather information (name, state, party, etc.) about each candidate and stored these results in a Pandas dataframe. To match emails to candidates, we used fuzzy string matching (specifically the partial token sort ratio from TheFuzz package) on the candidate's name and a cleaned version of the sender's email address for each email. For each email, we assigned the candidate whose name was most similar to the email address. This matcher is not perfect, but it does accurately assign most emails to the correct candidate. These functions are in the file [`scripts/fec_functions.py`](scripts/fec_functions.py).

### Cleaning and Merging
The file [`scripts/runme.py`](scripts/runme.py) calls the functions in the files explained above to do the following tasks:
1. Query the Gmail API for the desired number of emails
2. Query the FEC API for all active Senate candidates in 2024.
3. Assign candidates to emails using fuzzy string matching and merge in candidate information for each email.
4. Remove non-campaign related emails. This is a manual process. We filter out emails from Google and emails from Secure and Prosper (a rightwing email newsletter that is not tied to a particular candidate).
5. Saves the resulting Pandas dataframe as a csv file.

## Getting Started

This section explains the necessary set-up and tasks to run our data wrangling query. Rerunning this query will update the [`data/updated_full_data.csv`](data/updated_full_data.csv) dataset, including any emails received since the last query. Once you have run the query, you can simply rerun each of the DataAnalysis files to obtain results for the updated dataset.

1. Prerequisites

    i. First, make sure you install any required packages and libraries, listed in the imports of [`scripts/runme.py`](scripts/runme.py), [`scripts/fec_functions.py`](scripts/fec_functions.py), and [`scripts/gmail_functions.py`](scripts/gmail_functions.py). 

    ii. Second, you need the login information for this project's gmail account. This information is in the project summary, which you should have access to. Make sure that you can login to the account in your web browser. Whenever we reference gmail authentication, you should be authenticating with this account.

    iii. Finally, you will need to obtain the necessary credentials for each API. For the Gmail API, follow the tutorial linked in Resource 2 to obtain a `credentials.json` file and place it in the [`scripts`](./scripts/) folder. There is already one in the folder from Team A Spring 2024; for long-term use of this code, please create your own. For the FEC API, go to the FEC website linked in Resource 3 and request a personal API key. Replace the API KEY currently in [`scripts/run_me.py`](scripts/run_me.py) with your own.

2. Making sure that your current working directory is the [`scripts`](./scripts/) folder, run the file [`scripts/runme.py`](scripts/runme.py). This will take some time, as the script has to authenticate a Gmail service object, parse every email, and access the FEC database. You may need to authenticate the email in a web browser; make sure that you use the project's gmail account. You can click "Allow" for any permissions it requests. Once this is done, a progress bar will appear tracking the email parsing process.

3. Once the script finishes, [`data/updated_full_data.csv`](data/updated_full_data.csv) will be updated. You can now analyze the dataset yourself!

## Resources

1. Gmail API: https://developers.google.com/gmail/api/guides
2. Tutorial for Gmail API: https://thepythoncode.com/article/use-gmail-api-in-python
3. FEC API: https://api.open.fec.gov/developers/
4. TheFuzz: https://github.com/seatgeek/thefuzz
