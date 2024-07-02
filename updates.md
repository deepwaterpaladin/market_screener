# Installing Updates

## Setup

- If not installed, install the following:

1. Install [git](https://git-scm.com/downloads)
1. Install [VSCode](https://code.visualstudio.com/download)

## Download Screener

1. Open VSCode
1. Open the integrated term`CTRL + ` (backtick)` (on widows) `CMD + ` (backtick)` (on Mac)
1. In the terminal, run the command `cd {path_to_where_you_want_application_saved}`
1. In the same terminal, run the command `git clone https://github.com/deepwaterpaladin/market_screener.git`
  - this will clone the repository where the application is stored.
  - it will also initilize a git repository on your local machine. git is a version control software that allows you to track changes 
1. Follow the steps under `Setup` in `README.md`


## Check for Updates

1. Open VSCode
1. Open the integrated term`CTRL-`` (on widows) `CMD-`` (on Mac)
1. run `git fetch` to pull updates from remote repository

## Install Updates

1. Open VSCode
1. Open the integrated term`CTRL-`` (on widows) `CMD-`` (on Mac)
1. run `git pull origin {name_of_branch}` to pull updates from remote repository
  - `name_of_branch` default is main.
