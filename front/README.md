# Front facing proxy

Serves the static and media files and forwards requests to the app.

The Docker image needs to be built with the parent directory as build context.

This proxy needs to be behind another proxy which sets X-Forwarded-Proto
correctly!