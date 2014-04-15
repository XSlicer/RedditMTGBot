#TODO - Parse typo's

import time
import praw
import re
import urllib2
import signal, sys

# This string is sent by praw to reddit in accordance to the API rules
user_agent = ("REDDIT Bot v1.3 by /u/USERNAME")
r = praw.Reddit(user_agent=user_agent)

# Fill in the bot's username and password here
username = "USERNAME"
password = "PASSWORD"
r.login(username, password)

# Fill in the subreddit(s) here. Multisubs are done with + (e.g. MagicTCG+EDH)
subreddit = r.get_subreddit('INSERT_SUBREDDITS')

# This loads the already parsed comments from a backup text file
already_done = []
with open('magictcg_done.txt', 'r') as f:
    for i in f:
        already_done.append(i.replace("\n", ""))

# Function that does all the magic
def bot_comments():
    ids = []
    sub_comments = subreddit.get_comments()
    for comment in sub_comments:
        ids.append(comment.id)
        # Checks if the post is not actually the bot itself (since the details say [[CARDNAME]]
        if comment.id not in already_done and not str(comment.author) == username:
            # Regex Magic that finds the text encaptured with [[ ]]
            cards = re.findall("\[\[([^\[\]]*)\]\]", comment.body)
            reply = ""
            # Because a comment can only have a max length, limit to only the first 10 requets
            if len(cards) > 10: cards = cards[0:10]
            # Set removes any duplicates
            for i in set(cards):
                print i
                try:
                    # Converts obscure characters like AE to a URL-valid text
                    j = urllib2.quote(i.encode('utf-8'))
                    # Opens the Gatherer page and looks for the card ID with Regex - Replaces & because it breaks URLs
                    page = urllib2.urlopen("http://gatherer.wizards.com/Pages/Card/Details.aspx?name=%s" % j.replace("&", "%26")).read()
                    card_id = re.search("multiverseid=([0-9]*)", page).group(1)
                except AttributeError:
                    card_id = False
                    print "ERROR"
                if card_id:
                    # Builds the post
                    reply += "[%s](http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=%s&type=card&.jpg)" % (i, card_id)
                    reply += " - "
                    reply += "[Gatherer](http://gatherer.wizards.com/Pages/Card/Details.aspx?name=%s)" % j
                    reply += ", [MagicCards](http://magiccards.info/query?q=!%s)" % j
                    reply += "\n\n"
            # If a post was built before, complete it and post it to reddit
            if reply:
                reply += "^^Questions? ^^Message ^^/u/CREATOR ^^- ^^Call ^^cards ^^with ^^[[CARDNAME]] ^^- ^^Format: ^^Image ^^- ^^URL ^^to ^^Gatherer"
                # Possible advice text to advice using "AutocardAnywhere" instead
                #reply += "\n\n^^^Try ^^^the ^^^browser ^^^plugin ^^^'AutocardAnywhere' ^^^instead ^^^of ^^^the ^^^bot: ^^^Personal ^^^card-links!"
                # Posting might fail (too long, ban, reddit down etc), so cancel the post and print the error
                try:
                    comment.reply(reply)
                except Exception,e: print str(e)
            # Add the post to the list of parsed comments
            already_done.append(comment.id)
    # Finally, return the list of parsed comments (seperate from already_done)
    return ids

## Work in progress - Parses submissions
#def bot_submissions():
#    sub_ids = []
#    sub_submissions = subreddit.get_submissions()
#    for submission in sub_submissions:

# Function that backs up current parsed comments
def write_comments():
    with open("magictcg_done.txt", "w") as f:
        for i in already_done:
            f.write(str(i) + '\n')

# Function that is called when ctrl-c is pressed. It backups the current parsed comments into a backup file and then quits.
def signal_handler(signal, frame):
    write_comments()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Infinite loop that calls the function. The function outputs the post-ID's of all parsed comments.
# The ID's of parsed comments is compared with the already parsed comments so the list stays clean
# and memory is not increased. It sleeps for 15 seconds to wait for new posts.
while True:
    ids = bot()
    new_done = []
    for i in already_done:
        if i in ids:
            new_done.append(i)
    already_done = new_done[:]
    # Back up the parsed comments to a file
    write_comments()
    time.sleep(15)
