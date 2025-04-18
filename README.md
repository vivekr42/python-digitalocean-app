# DEVELOPMENT (LOCAL) SETUP

## 1. BUILD DOCKER IMAGE

```
docker-compose -f docker-compose.dev.yml up --build
```

- If you want to quit the project then run

  ```
  docker-compose -f docker-compose.dev.yml down
  ```

## 2. RUN PROJECT/SERVER

- Go inside container `docker exec -it {app_container_name} /bin/bash`:

```
docker exec -it ai_tutor_app /bin/bash
```

- It is mandatory to run server at `0.0.0.0:8080` from container, otherwise your project won't be available at `127.0.0.1:8000` on your host machine:

Run below command to run the server:

```
gunicorn -w 4 -k aiohttp.GunicornWebWorker --bind 0.0.0.0:8080 main:app
```

## 3. START EXPLORING PROJECT

Now go to "http://localhost:8080/" not "http://0.0.0.0:8080/"

