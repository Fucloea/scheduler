# Scheduler Microservice

This is a simple scheduler microservice, written in FastAPI, that uses APScheduler to schedule and execute jobs.


## Installation

These steps assume that you have a conda environment set up, along with a connection to a PostgreSQL database, with the right permissions enabled in order to autocreate tables.
If you use a different environment manager, replace the conda commands with the appropriate ones for your environment manager.

1. Create the conda environment and activate it:

```bash
conda create -n scheduler python=3.12
conda activate scheduler
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Copy the .env.example file to .env and fill in database url.

4. Run the application with:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
Configure the port as you wish.

## Usage

Once the server is running, you can open the prebuilt API docs at the '/docs' endpoint in your browser.

For example, if running locally;
```
http://localhost:8000/docs
http://localhost:8000/redoc
```

## About the current code

1. The POST /jobs endpoint takes in a unique job_name and any number of job_fields. No validation is done on the job_fields.

2. The job is scheduled using APScheduler, and saved to the database. 

3. The scheduler picks up the job_fields are writes them to a log file with the same name as the job_name. This is to mimic the flow of the scheduler pushing data into a queue, if this were a full-fledged application.

4. The GET /jobs endpoint returns all the active jobs from the job_store.

5. The GET /jobs/{job_id} endpoint returns job details from the db and the next_run time from the jobstore.


## Document regarding scalability 

[Here's](<url>) the link to the google doc; regarding points to consider for scalability of this application.