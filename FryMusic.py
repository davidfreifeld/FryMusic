#!/usr/bin/python
# -*- utf-8 -*-

from getpass import getpass
from gmusicapi import Mobileclient
import sqlite3 as lite
import re
import glob

def mobileClientLogin(api):
    """ Logs into the google music account and 
    returns the username input by the user """

    # Log in to google music account
    usernameEmail = raw_input("Username: ")
    pw = getpass()
    api.login(usernameEmail, pw)

    # Get the username (i.e. drop @gmail.com if it's there)
    regexUN = re.compile(r"((.*)@gmail.com)|(.*)")
    regexResult = regexUN.match(usernameEmail)
    username = usernameEmail
    if (regexResult.group(2)):
        username = regexResult.group(2)
        
    return username


def getMaxDBNumber(username):
    """ Find the current maximum database number in 
    the directory"""
    
    # Find all this user's db files in the directory
    dbfiles = glob.glob(username+"[.][0-9]*[.]db")
    regexDBNum = re.compile(username+"[.]([0-9]*)[.]db")
    maxNumber = 0
    for dbfile in dbfiles:
        regResult = regexDBNum.match(dbfile)
        fileNumber = int(regResult.group(1))
        if (fileNumber > maxNumber):
            maxNumber = fileNumber
    return maxNumber


def getAlbumAndTrackSet(library):
    """ Store the album/artist pairs in a set """

    albumList = []
    trackList = []
    for track in library:
        albumList.append((track['album'], track['artist']))
        trackList.append((track['album'], track['artist'], track['title']))
    albumSet = set(albumList)
    trackSet = set(trackList)
    return (albumSet, trackSet)


def saveLibraryToDatabase(dbName, albumSet, trackSet):
    """ Saves the user's google play songs and albums to 
    an SQLite database """   

    con = lite.connect(dbName)

    with con:

        cur = con.cursor()

        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("DROP TABLE IF EXISTS Tracks")
        cur.execute("DROP TABLE IF EXISTS Albums")

        cur.execute("""CREATE TABLE Albums(cAlbumTitle TEXT, cArtist TEXT, 
                       PRIMARY KEY(cAlbumTitle, cArtist))""")

        cur.execute("""CREATE TABLE Tracks(cAlbumTitle TEXT, cArtist TEXT, 
                       cTrackTitle TEXT, PRIMARY KEY(cAlbumTitle, cArtist, 
                       cTrackTitle), FOREIGN KEY(cAlbumTitle, cArtist) 
                       REFERENCES Albums(cAlbumTitle, cArtist))""")
        
	# Insert all the albums and tracks into the database tables                
        for album in albumSet:
            cur.execute("INSERT INTO Albums VALUES(:album, :artist)", {"album": album[0], "artist": album[1]})
        
        for track in trackSet:
            cur.execute("INSERT INTO Tracks VALUES(:album, :artist, :title)", 
                {"album": track[0], "artist": track[1], "title": track[2]})

        return dbName


def getAllTracks(dbName):
    """ Returns a list of tuples of tracks in the db """

    con = lite.connect(dbName)

    with con:

        cur = con.cursor()
        cur.execute("SELECT cAlbumTitle, cArtist, cTrackTitle FROM Tracks")
        rows = cur.fetchall()
        return rows


def getAllAlbums(dbName):
    """ Returns a list of tuples of albums in the db """

    con = lite.connect(dbName)

    with con:

        cur = con.cursor()
        cur.execute("SELECT rowid, cAlbumTitle, cArtist FROM Albums")
        rows = cur.fetchall()
        return rows


def getNewTracks(username, currentNumber, previousNumber=-1):
    """ Returns a set of tracks that exist in the current database
    but not the previous one """

    if (previousNumber == -1):
        previousNumber = currentNumber - 1

    currentDBName = username + '.' + str(currentNumber) + '.db'
    prevDBName = username + '.' + str(previousNumber) + '.db'

    currentTrackSet = set(getAllTracks(currentDBName))
    prevTrackSet = set(getAllTracks(prevDBName))

    newTrackSet = currentTrackSet - prevTrackSet

    return newTrackSet


def printAlbums(dbName):
    """ Prints a list of all albums in the database """

    rows = getAllAlbums(dbName)
    for row in rows:
        print "%s) %s | %s" % (row[0], row[1], row[2])

def printTracksFromSet(trackset):
    """ Prints a list of the tracks from the given set """

    for track in trackset:
        print "%s | %s | %s" % (track[0], track[1], track[2])
   

if __name__ == "__main__":
    # Get the gmusic client and log in
    api = Mobileclient()
    username = mobileClientLogin(api)
        
    # Get the list of all song dictionaries
    library = api.get_all_songs()

    # Get the sets of albums and tracks
    (albumSet, trackSet) = getAlbumAndTrackSet(library)

    # Find out the number of the most recently saved db
    maxNumber = getMaxDBNumber(username)

    # Connect to the database and write the album, artist pairs
    dbName = username + '.' + str(maxNumber+1) + '.db'
    saveLibraryToDatabase(dbName, albumSet, trackSet)

    # Read the albums from the database and print
    printAlbums(dbName)
