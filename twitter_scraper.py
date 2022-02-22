from config import *
from tqdm import tqdm
import sys, os, glob, time, requests, json

sys.path.append('Lib\site-packages')

import tweepy

class Scraper():
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, bearer_token):

        # TOKEN AUTHENTICATION
        self.consumer_k = consumer_key
        self.consumer_s = consumer_secret
        self.access_token = access_token
        self.access_token_s = access_token_secret
        self.bearer_token = bearer_token

        # INITIATE THE ENVIROMENT
        self.client = tweepy.Client(self.bearer_token, self.consumer_k, self.consumer_s, self.access_token, self.access_token_s, wait_on_rate_limit = True)

    def scrape_followings(self, username):

        print("* Collecting user information ", end="")
        response = self.client.get_users(usernames=username, user_fields = ["public_metrics"])
        users_id = [data.id for data in response.data]
        data_dict = {}
        print("=> DONE")
        pbar = tqdm(users_id)
        for indx, id in enumerate(pbar):
            pbar.set_description(f"* Scraping the followers of {username[indx]} ")
            following_ids = []
            following_usernames = []
            for page_response in tweepy.Paginator(self.client.get_users_following, id, max_results=1000):
                following_ids += [following_response.id for following_response in page_response.data]
                following_usernames += [following_response.username for following_response in page_response.data]
                break
            data_dict[username[indx]] = {"user_id": id,
                                         "user_metadata": response.data[indx].public_metrics,
                                         "following": {"following_ids": following_ids,
                                                       "following_usernames": following_usernames}
                                        }

        print("   => DONE")

        return data_dict

    def scrape_user_metadata(self, username):
        metadata_response = self.client.get_user(username=username, user_fields = ["created_at","public_metrics"])

        metadata_dict = {"user_id" : metadata_response.data.id,
                         "created_at": metadata_response.data.created_at,
                         "metrics": metadata_response.data.public_metrics}

        return metadata_dict

    def scrape_tweets(self, id, threshold = 10):

        tweet_dict = {}
        counter = 0
        flag = False
        for page_response in tweepy.Paginator(self.client.get_users_tweets, id, tweet_fields=["public_metrics", "created_at"], exclude=["retweets", "replies"]):
            if page_response.meta["result_count"] != 0:
                for tweet in page_response.data:
                    if counter < threshold:
                        tweet_dict[tweet.id] = {"metrics": tweet.public_metrics,
                                                "created_at": tweet.created_at.strftime("%Y/%m/%d, %H:%M:%S") }
                    else:
                        flag=True
                        break
                    counter += 1
            if flag:
                break
        return tweet_dict

    def scrape_commenters(self, tweet_id):

        query = f"conversation_id:{tweet_id}"

        tweet_responses = self.client.search_all_tweets(query=query, max_results = 500, start_time="2010-11-06T00:00:00+00:00", tweet_fields="author_id")
        oldest_id = tweet_responses.meta["oldest_id"]
        count = tweet_responses.meta["result_count"]
        commenters = [tweet_responses.data[i].author_id for i in range(len(tweet_responses.data))]

        while True:

            tweet_responses = self.client.search_all_tweets(query=query, max_results = 500, until_id = oldest_id, tweet_fields="author_id")
            count = tweet_responses.meta["result_count"]
            if count == 0:
                break

            oldest_id = tweet_responses.meta["oldest_id"]
            commenters += [tweet_responses.data[i].author_id for i in range(len(tweet_responses.data))]
            print(count)

        print(len(commenters))


    def scrape_likers(self, tweet_id, threshold = 100):
        like_ids = []
        for page_response in tweepy.Paginator(self.client.get_liking_users, tweet_id):
            if page_response.meta["result_count"] != 0:
                like_ids += [like.id for like in page_response.data]
                if len(like_ids) >= threshold:
                    break
        return like_ids

    def scrape_retweeters(self, tweet_id, threshold = 100):
        retweeter_ids = []
        for page_response in tweepy.Paginator(self.client.get_retweeters, tweet_id):
            if page_response.meta["result_count"] != 0:
                retweeter_ids += [retweeter.id for retweeter in page_response.data]
                if len(retweeter_ids) >= threshold:
                    break
        return retweeter_ids

def main():

    myscraper = Scraper(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN)

    filenames = [os.path.basename(path[:-1]) for path in glob.glob(f'{DATA_PATH}/*/')]
    followings_response = myscraper.scrape_followings(starting_user)


    for user in followings_response:
        print(f"Start scraping user {user}")

        if user not in filenames:
            os.mkdir(f'{DATA_PATH}/{user}')

        with open(f'{DATA_PATH}/{user}/{user}.json', "w") as myfile:
            json.dump(followings_response[user], myfile)

        print(f"* Start scraping tweets of {user}", end= "")
        tweets = myscraper.scrape_tweets(followings_response[user]["user_id"], threshold=2)

        pbar = tqdm(tweets)
        print(" => DONE!")

        for tweet in pbar:
            pbar.set_description(f"* Starting scraping likers/retweeters of tweet {tweet} => ")
            likers = myscraper.scrape_likers(tweet)
            retweeters = myscraper.scrape_retweeters(tweet)
            with open(f'{DATA_PATH}/{user}/{tweet}.json', "w") as myfile:
                tweets[tweet]["liker_ids"] = likers
                tweets[tweet]["retweeters"] = retweeters
                json.dump(tweets[tweet], myfile)

        print(f"Finish scraping user {user}!")

if __name__ == '__main__':

    starting_user = ["kanyewest", "adriaen_s"]
    main()
