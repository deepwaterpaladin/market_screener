# market_screener

## Setup

1. run startup file `py startup.py`.
    - this should install required dependencies & create an `.env` file.
2. within the `.env` file, replace ` # *** YOUR API KEY *** ` with your FMP API key wrapped in quotes. (i.e., `"abc123"`).
3. add your `service_account.json` file from your Google developer portal.
4. open Task Scheduler on your PC:
    - under the `Actions` tab on the right side of the application, select `Create Basic Task`
    - name the task as you wish (i.e., Weekly Screeer)
    - select `Weekly` trigger
    - configure the date/time you would like the screener to run (keep in mind the screener takes approximately 200 minutes to fully execute)
    - configure the action `Start a program`
    - under `Program/script` provide the path to application.py in the root directory (i.e., `C:\User\Documents\market_screener\application.py`)
    - review the task configuration & click `Finish`
5. once the task is created, edit it's properties and select `Settings` to verify the following settings:
    - Allow task to be run on demand -- enabled
    - Run task as soon as possible after a scheduled start is missed -- enabled
    - If the running task does not end when requested, force it to stop
6. Once the above steps have been completed, the screener will run as configured.

## Data

1. [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs)
