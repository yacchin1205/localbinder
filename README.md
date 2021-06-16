# localbinder

A Command Line Tool to launch Jupyter Notebook Server based on a MyBinder URL locally

# How to run

The image of this tool is available on [Docker Hub](https://hub.docker.com/repository/docker/yacchin1205/localbinder). You can start the same Jupyter Notebook Server as `mybinder-url` on localhost with the following command.

```
$ docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -it yacchin1205/localbinder <mybinder-url>
```

The command will display a URL like `http://127.0.0.1:8888/?token=...`, so open it in your browser.

If you wanted to launch https://mybinder.org/v2/gh/NII-cloud-operation/Jupyter-LC_docker/openhouse-2021-demo locally, you could run the command as follows:

```
$ docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -it yacchin1205/localbinder https://mybinder.org/v2/gh/NII-cloud-operation/Jupyter-LC_docker/openhouse-2021-demo
```
