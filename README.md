# Twitter-Scraper

This repository allows users to make scrape operations by using the owners' keys.

## Usage
- You may enter your own keys, obtained from tweeter, into `config.py` and save the file later. Open terminal and change current working directory as cloned repository. Then, enter the following template:
```
python main.py -m <MODE> -a <ACCOUNT NAME> -t <INTEGER>
```
- There are couple of modes that you can use:
  - First mode is called `Scrape`. This mode allows you only to scrape the target account at a time. Scraped informations are metadata of the target account, tweets, accounts that like the tweet, accounts that retweet the tweet.
  - Second mode is called `Autonomus` in which target account becomes the starting point of the scrape process and keeps scraping other users' pages by choosing from the followings' of the current account.
  
  *NOTE*:
  Please do no use to install requirements that are defined in the `requirements.txt` file to use this repository.
 
