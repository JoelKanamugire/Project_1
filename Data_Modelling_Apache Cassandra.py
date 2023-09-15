# Import Python packages 
import pandas as pd
import cassandra
import re
import os
import glob
import numpy as np
import json
import csv
# checking your current working directory
print(os.getcwd())

# Get your current folder and subfolder event data
filepath = os.getcwd() + '/event_data'

# Create a for loop to create a list of files and collect each filepath
for root, dirs, files in os.walk(filepath):
    
# join the file path and roots with the subdirectories using glob
    file_path_list = glob.glob(os.path.join(root,'*'))
    #print(file_path_list)
  # initiating an empty list of rows that will be generated from each file
full_data_rows_list = [] 
    
# for every filepath in the file path list 
for f in file_path_list:

# reading csv file 
    with open(f, 'r', encoding = 'utf8', newline='') as csvfile: 
        # creating a csv reader object 
        csvreader = csv.reader(csvfile) 
        next(csvreader)
        
 # extracting each data row one by one and append it        
        for line in csvreader:
            #print(line)
            full_data_rows_list.append(line) 
# uncomment the code below if you would like to get total number of rows 
#print(len(full_data_rows_list))
# uncomment the code below if you would like to check to see what the list of event data rows will look like
#print(full_data_rows_list)

# creating a smaller event data csv file called event_datafile_full csv that will be used to insert data into the \
# Apache Cassandra tables
csv.register_dialect('myDialect', quoting=csv.QUOTE_ALL, skipinitialspace=True)

with open('event_datafile_new.csv', 'w', encoding = 'utf8', newline='') as f:
    writer = csv.writer(f, dialect='myDialect')
    writer.writerow(['artist','firstName','gender','itemInSession','lastName','length',\
                'level','location','sessionId','song','userId'])
    for row in full_data_rows_list:
        if (row[0] == ''):
            continue
        writer.writerow((row[0], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[12], row[13], row[16]))
      # check the number of rows in your csv file
with open('event_datafile_new.csv', 'r', encoding = 'utf8') as f:
    print(sum(1 for line in f))
  from cassandra.cluster import Cluster
try:    
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()
except Exception as e:
    print(e)
    # TO-DO: Create a Keyspace 
try:
    session.execute("""
    CREATE KEYSPACE IF NOT EXISTS udacity 
    WITH REPLICATION = 
    { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }"""
)

except Exception as e:
    print(e)
  # TO-DO: Set KEYSPACE to the keyspace specified above
try:
    session.set_keyspace('udacity')
except Exception as e:
    print(e)
  ## TO-DO: Query 1:  Give me the artist, song title and song's length in the music app history that was heard during \
## sessionId = 338, and itemInSession = 4
# Create table (artist_song_for_session) for query 1
# The columns are ordered by the parition key, clustering column then all of the returned values
query = "CREATE TABLE IF NOT EXISTS music_app_history_artist_and_song \
        (sessionId int, itemInSession int, artist text, song text, length float, \
        PRIMARY KEY (sessionId, itemInSession))"

try:
    session.execute(query)
except Exception as e:
    print(e) 
file = 'event_datafile_new.csv'

with open(file, encoding = 'utf8') as f:
    csvreader = csv.reader(f)
    next(csvreader) # skip header
    for line in csvreader:
        # Assign the INSERT statements into the `query` variable
        query = "INSERT INTO music_app_history_artist_and_song (sessionId, itemInSession, artist, song, length)"
        query = query + "VALUES (%s, %s, %s, %s, %s)"
        # Assign which column element should be assigned for each column in the INSERT statement.
        session.execute(query, (int(line[8]), int(line[3]), line[0], line[9], float(line[5]), ))
      ## TO-DO: Add in the SELECT statement to verify the data was entered into the table
# Perform query
query = "SELECT artist, song, length from artist_song_for_session WHERE sessionId=338 AND itemInSession=4"
rows = session.execute(query)
for row in rows:
    print(row.artist, row.song, row.length)
  # Create table (user_for_song) for query 3
# The columns are ordered by the parition key, clustering column then all of the returned values
query = "CREATE TABLE IF NOT EXISTS user_for_song "
query = query + "(song text, userId int,firstName text, lastName text, PRIMARY KEY (song, userId))"
session.execute(query)

# Insert data into table for query 3
file = 'event_datafile_new.csv'
with open(file, encoding = 'utf8') as f:
    csvreader = csv.reader(f)
    next(csvreader)
    for line in csvreader:
        query = "INSERT INTO user_for_song (song, userId, firstName, lastName)"
        query = query + "VALUES (%s, %s, %s, %s)"
        session.execute(query, (line[9], int(line[10]), line[1], line[4]))
      ## TO-DO: Query 3: Give me every user name (first and last) in my music app history who listened to the song 'All Hands Against His Own'
# Perform query 3
query = "SELECT firstName, lastName FROM user_for_song WHERE song='All Hands Against His Own'"
rows = session.execute(query)
for row in rows:
    print(row.firstname, row.lastname)    
  session.execute("drop table artist_song_for_session")
session.execute("drop table artist_song_user_for_user_session")
session.execute("drop table user_for_song")
session.shutdown()
cluster.shutdown()

                    
