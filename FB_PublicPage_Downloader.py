#!/usr/bin/env python

import commands
import json
import os
import sys
import urllib
import urllib2

import dateutil.parser
import magic
import requests

########################### CUSTOMIZE THIS ###########################
page_id = "102099916530784"
access_token = "878703055534932|52kR9IPthAvwFam4AFtlUZSQDPM" # see https://developers.facebook.com/docs/facebook-login/access-tokens#apptokens
dest = os.path.expanduser("~/HONY")
website_title = "Humans of New York"
######################################################################


photoCounter = 1;
open('metaData.txt', 'w').close() #erase the contents
metaDataFileName = open("metaData.txt", 'ab');



if not os.path.exists(dest):
    os.makedirs(dest)

# read last update time, if it is available
last_update_record = dest + "/last_update_timestamp"
if os.path.exists(last_update_record):
    f = open(last_update_record, "r")
    last_update_timestamp = f.readline()
    f.close()
    last_update_time = dateutil.parser.parse(last_update_timestamp)
else:
    last_update_time = dateutil.parser.parse("1970-01-01T00:00+00:00")

# this function makes an API call with only an access_token (which
# could be just app-id|app-secret)
def fb_public_call(endpoint, params, access_token):
    params["access_token"] = access_token
    response = requests.get("https://graph.facebook.com/" + endpoint,
                            params=params)
    return response.json()

# this function downloads a photo
# return codes are defined below
SUCCESS = 0
FAILED_DOWNLOAD = 1
UNRECOGNIZED_MIME = 2
OLD_PHOTO = 255 # photo older than last update time
def handle_photo(photo, album_id):
    global photoCounter, metaDataFileName 

    # print information
    photo_id = photo["id"]
    time = dateutil.parser.parse(photo["created_time"])
    if time < last_update_time:
        return OLD_PHOTO
    time_print = time.strftime("%b %d, %Y")
    time_full = time.strftime("%Y%m%d%H%M%S")
    original_image = photo["images"][0]
    height = original_image["height"]
    width = original_image["width"]
    format_string = "date: %s   id: %s   size: %sx%s"
    print format_string % (time_print, photo_id, width,
                           height)
    # download file
    source_uri = original_image["source"]
    filename = time_full + "-" + website_title + "-" + \
               album_id + "-" + photo_id
    filepath = dest + "/" + filename

    photoName = "images/" + str(photoCounter) + ".jpg"
    print "--------Source URI : " 
    print source_uri;
    print photoName
    print photo["name"]
    print "\n" ;

    metaDataFileName.write(source_uri+"\n")
    metaDataFileName.write(photoName+".jpg"+"\n")
    metaDataFileName.write(photo["name"].encode('utf-8')+"\n")
    metaDataFileName.write("-" * 80+"\n")

    #params = { 'access_token' : ''}

    outfile = urllib2.urlopen(source_uri )
    output = open(photoName,'wb')
    output.write(outfile.read())
    output.close()

    photoCounter = photoCounter+1
    
# this function handles an album, i.e., download newly added photos
# since the last update
def handle_album(album):
    # print album info
    album_id = album["id"]
    format_string = "downloading album \"%s\" " + \
                    "(album id: %s; photo count: %s)"
    print format_string % (album["name"], album_id,
                           album["count"])
    print "-" * 80
    # retrieve photos in the album
    photos_response = fb_public_call(album["id"] + "/photos",
                                     params, access_token)

    #print "-----------Photos in an album \n"
    #print json.dumps( photos_response, indent=1)

    while True:
        for photo in photos_response["data"]:
            if handle_photo(photo, album_id) == OLD_PHOTO:
                # already encountered old photo in this album
                # no need to look further into the past
                print
                return

        if "next" in photos_response["paging"]:
            next_uri = photos_response["paging"]["next"]
            photos_response = requests.get(next_uri).json()
        else:
            break
    print
    
params = {}
# retrieve albums
albums_response = fb_public_call(page_id + "/albums", params,
                                 access_token);

#print json.dumps(albums_response, indent=1) 

while True:
    for album in albums_response["data"]:
        handle_album(album)

    if "next" in albums_response["paging"]:
        next_uri = albums_response["paging"]["next"]
        albums_response = requests.get(next_uri).json()
    else:
        break

# update feature yet to be implemented
# create a file "last_update_timestamp" for future use
f = open(last_update_record, "w")
f.write(commands.getoutput("date -u --iso-8601=seconds"))
f.close()
