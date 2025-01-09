after extracting this folder and you are in it's directory, start by running the following command:
```bash
   heroku login
```
then enter your credentials to login to heroku on the web.

```bash
   heroku container:push web -a magic-pillow
```
This will definitely take some time, so be patient.

```bash
   heroku container:release web -a magic-pillow
```

```bash
   heroku open -a magic-pillow
```

This will open the browser and navigate to the deployed app.