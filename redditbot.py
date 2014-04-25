#TODO - Parse typo's
#TODO2 - Create more functions (e.g. post building into a function)

import time
import praw
import re
import urllib2
import signal, sys

# This string is sent by praw to reddit in accordance to the API rules
user_agent = ("REDDIT Bot v1.4 by /u/USERNAME")
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
            # Because a comment can only have a max length, limit to only the first 30 requests
            if len(cards) > 30: cards = cards[0:30]
            # Set removes any duplicates
            for i in set(cards):
                print i
                i = i.split('/')[0]
                # Converts obscure characters like AE to a URL-valid text
                j = urllib2.quote(i.encode('utf-8'))
                # Checks if a card exists
                card_id = card_check(i, j)
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

# This function is nearly the same as comment parsing, except it takes submissions (should be combined later)
def bot_submissions():
    sub_ids = []
    sub_subs = subreddit.get_new(limit=5) 
    for submission in sub_subs:
        sub_ids.append(submission.id)
        if submission.id not in already_done:
            cards = re.findall("\[\[([^\[\]]*)\]\]", submission.selftext)
            reply = ""
            if len(cards) > 30: cards = cards[0:30]
            for i in set(cards):
                print i
                i = i.split('/')[0]
                j = urllib2.quote(i.encode('utf-8'))
                card_id = card_check(i, j)
                if card_id:
                    reply += "[%s](http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=%s&type=card&.jpg)" % (i, card_id)
                    reply += " - "
                    reply += "[Gatherer](http://gatherer.wizards.com/Pages/Card/Details.aspx?name=%s)" % j
                    reply += ", [MagicCards](http://magiccards.info/query?q=!%s)" % j
                    reply += "\n\n"
            if reply:
                reply += "^^Questions? ^^Message ^^/u/xslicer ^^- ^^Call ^^cards ^^with ^^[[CARDNAME]] ^^- ^^Format: ^^Image ^^- ^^URL ^^to ^^Gatherer"
                try:
                    submission.add_comment(reply)
                except Exception,e: print str(e)
            already_done.append(submission.id)
    return sub_ids

# Function that checks if the requested card exist and returns the card id (card id is unneccesary 
# for linking since the gatherer will also link the image with it's name, but this is still valid
# to check if the card exists).
def card_check(card, enc_card):
    try:
        # Opens the Gatherer page and looks for the card ID with Regex - Replaces & because it breaks URLs
        page = urllib2.urlopen("http://gatherer.wizards.com/Pages/Card/Details.aspx?name=%s" % enc_card.replace("&", "%26")).read()
        return re.search("multiverseid=([0-9]*)", page).group(1)
    except AttributeError:
        print "ERROR"
        return False

# Function that backs up current parsed comments
def write_done():
    with open("magictcg_done.txt", "w") as f:
        for i in already_done:
            f.write(str(i) + '\n')

# Function that is called when ctrl-c is pressed. It backups the current parsed comments into a backup file and then quits.
def signal_handler(signal, frame):
    write_done()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Infinite loop that calls the function. The function outputs the post-ID's of all parsed comments.
# The ID's of parsed comments is compared with the already parsed comments so the list stays clean
# and memory is not increased. It sleeps for 15 seconds to wait for new posts.
while True:
    ids = bot_comments()
    time.sleep(5)
    sub_ids = bot_submissions()
    new_done = []
    # Checks for both comments and submissions
    for i in already_done:
        if i in ids:
            new_done.append(i)
        if i in sub_ids:
            new_done.append(i)
    already_done = new_done[:]
    # Back up the parsed comments to a file
    write_done()
    time.sleep(10)
