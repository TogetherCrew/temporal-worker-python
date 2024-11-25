# temporal-worker-python

This repository contains TogetherCrew's Temporal Python workflows. Follow the steps below to set up the project locally:

## Setup Instructions

1. Configure Environment Variables
   - Copy the example environment file:

   ```bash
    cp .env.example .env
   ```

   Update the `.env` file with your own values, referencing the services defined in `docker-compose.dev.yml`.

2. Start Services
    - Use the following command to set up and run the required services:

    ```bash
    docker compose -f docker-compose.dev.yml up -d
    ```

3. Open [localhost:8080](http://localhost:8080/) and check temporal dashboard.
