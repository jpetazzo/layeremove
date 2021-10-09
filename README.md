# Layeremove

A (very dirty) experiment to remove layers from a Docker image.

## How to use

Requirements:

- Docker Engine
- Skopeo
- Python 3

Build a trivial Docker image:
```bash
docker build example/ -t figlet
```

Export it to an OCI directory, so that we can mess with it:
```bash
OCI_DIR=src
skopeo copy docker-daemon:figlet:latest oci:$OCI_DIR
```

Run the horrible script:
```bash
./layeremove.py $OCI_DIR
```

Copy the updated image back to the Docker Engine:
```bash
skopeo copy oci:$OCI_DIR docker-daemon:figlet:layeremove
```

Check that the image still works:
```bash
docker run figlet:layeremove
```

Check the size and layers of the original and new image:
```bash
docker images figlet
docker history figlet:latest
docker history figlet:layeremove
```

## How it works

The `layeremove.py` script will scan an OCI image, and it will remove
some layers from that image. It will layers that contain `#LAYEREMOVE#`
in their `created_by` attribute; so if you put `RUN something #LAYEREMOVE#`
in a Dockerfile, the resulting layer will be removed. You can also pass
layer hashes as extra command line arguments, e.g.:

```bash
./layeremove.py oci-src-dir sha256:abc123... sha256:def678...
```

It identifies the layers, then removes them from the *image manifest*
as well as the *image configuration*. In the image configuration, it
leaves a dummy layer in the history, which is why these layers will
still show up in `docker history`.

## Caveats

The code worked for me at least once, but there is no guarantee that
it will work for you! 🤷🏻

Make sure that the OCI directory contains only one image. Otherwise,
adapt things a bit.

The code deserves to be cleaned up a bit, but I think I'll go and have
a beer instead! 🍺
