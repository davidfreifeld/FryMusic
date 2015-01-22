#!/usr/bin/python
# -*- utf-8 -*-

from getpass import getpass
from gmusicapi import Mobileclient
import sqlite3 as lite


def saveAlbumDatabase():
    """ Logs into the google music api and 
    gets all of the songs """

    api = Mobileclient()
    
    # Log in to google music account
    pw = getpass()
    api.login('fryguy1326@gmail.com', pw)

    # Get the list of all song dictionaries
    library = api.get_all_songs()

    # Store the album/artist pairs in a set
    albumList = []
    trackList = []
    for track in library:
        albumList.append((track['album'], track['artist']))
        trackList.append((track['album'], track['artist'], track['title']))
    albumSet = set(albumList)
    trackSet = set(trackList)

    # Connect to the database and write the album, artist pairs
    con = lite.connect('frymusic.db')

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

        # Get the albums from the database and print
        cur.execute("SELECT rowid, cAlbumTitle, cArtist FROM Albums")

        rows = cur.fetchall()

        for row in rows:
            print "%s) %s | %s" % (row[0], row[1], row[2])
    

if __name__ == "__main__":
    saveAlbumDatabase()    
