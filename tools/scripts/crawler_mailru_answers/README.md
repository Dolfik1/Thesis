# Mail.ru Answers Crawler

#### This script used to catch data from Mail.ru answers.

## Instructions

### Start crawler without Docker

```bash
pip install -r requirements.txt
python crawler.py
```

### Start crawler in Docker

```bash
docker build -t mailru_answers_crawler .
docker run -d -it --name=mailru_crawler mailru_answers_crawler
```

You can execute `copy_data.sh` script, to copy parsed data from container to `results` folder.