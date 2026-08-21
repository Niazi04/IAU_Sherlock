# IAU Sherlock - A RAG chatbot

**🇬🇧 EN** | [🇮🇷 FA](README_FA.md)

This is my bachelors final project revolving around **Retrieval-Augmented Generation (RAG)**

In this project, I implemented a full featured RAG chatbot.

## Features

- RAG-based question answering for IAU policies
- Multi-lingual support (using Nvidia's multilingual models)
- Vector storage with Qdrant
- Document ingesting service
- Dockerized for easy deployment
- Swagger API documentation
- Sample front-end for testing
- Sample Qdrant snapshot for testing

## Quick Start

### Create you working directory clone the project
```bash
mkdir IAU_RAG
cd IAU_RAG

git clone https://github.com/Niazi04/IAU_Sherlock.git .
```

### Environment variables

The project uses environment variables for configuration. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Now edit the `.env` file with your API credentials. The most important values are:

```
LLM_API_URL=    # Your llm provider. I used Nvidia (its free)
LLM_MODEL_NAME= # LLM - Must me multilingual. I used nvidia/nemotron-3-ultra-550b-a55b
LLM_API_KEY=    # LLM API KEY
EMBEDDING_SERVICE_URL= # Embedding provider. I used Nvidia (its free)
NVIDIA_API_KEY= # Embedding api key. use model nvidia/nemotron-3-embed-1b
UI_API_KEY=     # Your custom X-API-KEY used by the front-end and swagger testing
```
You can check the models mentiond, from build.nvidia.com/models

Get your API key and continue

Set a strong custom API key for UI_API_KEY (front-end & Swagger use this)

### Run the docker container
```docker
docker compose -f 'docker-compose.dev.yml' up -d --build
```
**NOTE:** Make sure that yout docker engine is running!

**NOTE:** The images and requirements will be use a mirror. If you are outside of Iran, you can safely remove the mirrors

## Setting up Qdrant
Docker will handle Qdrant. However you do need some sample points (data) to start and test the project.

You have to first embed the data, then attatch the appropriate payload to each embedding and finally upset the whole thing to Qdrant.

Lucky for you, you can use the `faq/mine/file` endpoint which automated the whole flow.
First headover to `http://localhost:8000/docs`. Now all you have to do, is to upload the
data under `docs\data.json`. Set an appropriate name for the collection. and hit execute.

Once done, go to your `.env` file and upadted `FAQ_COLLECTION_NAME` to whatever name you gave to your collection.

Restart the container and you are all set.


## Test the app
You have two options to play with the project
1. **swagger**

    once your container is build, head to http://localhost:8000/docs
    
    There you will see all the available endpoints and you can even create your own front-end for this project

2. **my sample Front-End**

    In the project directory look for `sample_frontend`. Inside js\config.js, insert you UI_API_KEY like so:
    ```js
     apiKey: "YOu_API_KEY"
    ```

    From there open `index.html` in your browser. You can now chat with and ask questions regarding IAU policies.

**Note For Iranians:** You have to use a VPN to connect to NVIDIA services. If you are using another provider that has not banned Irans IP, you can safely turn off your VPN.


## Frequently Asked Questions (FAQs)

1. How can I upload my own data to Qdrant?

   Answer: you have to create a json dataset similar to `docs\data.json`

   Once ready, head over to the swagger UI and ingest your data via `faq/mine/file` endpoint.

   Then make sure to update your env file.

   Restart the server, and you are set.

2. I can not connect to the UI
   
   Answer: This is probably a `UI_API_KEY` mismatch. Check that.

   * The key in `.env` matches `sample_frontend/js/config.js`

   * Your API provider is accessible (try pinging the endpoint)

   The container is running: ```docker compose ps```

## Additional Details

Tech Stack
- Backend: FastAPI (Python)

- LLM: nvidia/nemotron-3-ultra-550b-a55b

- Embeddings: nvidia/nemotron-3-embed-1b

- Vector DB: Qdrant

- Deployment: Docker