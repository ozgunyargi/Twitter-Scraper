import sys, os, json, random

from config import *
from optparse import OptionParser
from twitter_scraper import Scraper
from tqdm import tqdm
from glob import glob

def main():
    parser = OptionParser()
    parser.add_option("-m", "--mode", help='The operation that you want to execute.', type="str", dest="mode", default="")
    parser.add_option("-a", "--acc", help='The name of the account that you want to scrape.', type="str", dest="account_name", default="")
    parser.add_option("-t", "--threshold", help='The number of liker/retweeter you will scrape per tweet.', type="str", dest="threshold", default="100")
    parameters, args = parser.parse_args(sys.argv[1:])

    scraper = Scraper(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN)

    if parameters.mode == "Scrape":

        users = [user for user in parameters.account_name.split(",")]
        followings_response = scraper.scrape_followings(users)

        for user in followings_response:
            print(f"Start scraping user {user}")

            if user not in filenames:
                os.mkdir(f'{DATA_PATH}/{user}')

            with open(f'{DATA_PATH}/{user}/{user}.json', "w") as myfile:
                json.dump(followings_response[user], myfile)

            print(f"* Start scraping tweets of {user}", end= "")
            tweets = scraper.scrape_tweets(followings_response[user]["user_id"], threshold=2)
            print(" => DONE!")
            pbar = tqdm(tweets)

            for tweet in pbar:
                pbar.set_description(f"* Starting scraping likers/retweeters of tweet {tweet} => ")
                likers = scraper.scrape_likers(tweet)
                retweeters = scraper.scrape_retweeters(tweet)
                with open(f'{DATA_PATH}/{user}/{tweet}.json', "w") as myfile:
                    tweets[tweet]["liker_ids"] = likers
                    tweets[tweet]["retweeters"] = retweeters
                    json.dump(tweets[tweet], myfile)
            print(f"Finish scraping user {user}!")


    elif parameters.mode == "Autonomus":
        flag = True
        container_user_num = 5
        while True:
            if flag:
                if parameters.account_name  != "":
                    user = [parameters.account_name]
                else:
                    with open("users_to_scrape.txt", "r") as myfile:
                        with open("scraped_users.txt", "r") as scraped_users:
                            scraped_user_list = [line.strip() for line in scraped_users.readlines()]
                        users_to_scrape_list = [line.strip() for line in myfile.readlines()]
                    for indx, user_s in enumerate(users_to_scrape_list):
                        if user_s not in scraped_user_list:
                            break
                    if len(users_to_scrape_list[indx:]) >= container_user_num:
                        user = users_to_scrape_list[indx:indx+container_user_num]
                    else:
                        user = users_to_scrape_list[indx:]
                flag=False
            else:
                with open("users_to_scrape.txt", "r") as myfile:
                    with open("scraped_users.txt", "r") as scraped_users:
                        scraped_user_list = [line.strip() for line in scraped_users.readlines()]
                    users_to_scrape_list = [line.strip() for line in myfile.readlines()]
                for indx, user_s in enumerate(users_to_scrape_list):
                    if user_s not in scraped_user_list:
                        break
                if len(users_to_scrape_list[indx:]) >= container_user_num:
                    user = users_to_scrape_list[indx:indx+container_user_num]
                else:
                    user = users_to_scrape_list[indx:]
            scrape_main(scraper, user, parameters.threshold)

def scrape_main(myscraper, user_list, threshold):
    response = myscraper.scrape_followings(user_list)
    for user in response:
        print(user)
        following_id_list = response[user]["following"]["following_ids"]
        following_username_list = response[user]["following"]["following_usernames"]
        sample_size = 20
        if len(following_id_list) > sample_size:
            chosen_indx = [random.randint(0, len(following_id_list)-1) for i in range(sample_size)]
            sub_id_followings = [following_id_list[indx] for indx in chosen_indx]
            sub_username_followings = [following_username_list[indx] for indx in chosen_indx]
        else:
            sub_id_followings = following_id_list
            sub_username_followings = following_username_list
        print(f"Start scraping user {user}")
        if user not in filenames:
            os.mkdir(f'{DATA_PATH}/{user}')
        with open(f'{DATA_PATH}/{user}/{user}.json', "w") as myfile:
            json.dump(response[user], myfile)
        print(f"* Start scraping tweets of {user}", end= "")
        tweets = myscraper.scrape_tweets(response[user]["user_id"], threshold=100)
        print(" => DONE!")
        pbar = tqdm(tweets)
        for tweet in pbar:
            pbar.set_description(f"* Starting scraping likers/retweeters of tweet {tweet} => ")
            likers = myscraper.scrape_likers(tweet, threshold=int(threshold))
            retweeters = myscraper.scrape_retweeters(tweet, threshold=int(threshold))
            with open(f'{DATA_PATH}/{user}/{tweet}.json', "w") as myfile:
                tweets[tweet]["liker_ids"] = likers
                tweets[tweet]["retweeters"] = retweeters
                json.dump(tweets[tweet], myfile)
        print(f"Finish scraping user {user}!")
        with open("scraped_users.txt", "a+") as myfile:
            myfile.write(f"{user}\n")
        with open("users_to_scrape.txt", "a+") as myfile:
            for following_user in sub_username_followings:
                myfile.write(f"{following_user}\n")

if __name__ == '__main__':
    filenames = [os.path.basename(path[:-1]) for path in glob(f'{DATA_PATH}/*/')]
    main()
