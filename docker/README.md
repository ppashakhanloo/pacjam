# Debloating Docker-Image Builders

## Builders
| Category | Common Apps (debian-buster) | VLC only (debian-jessie) |
| --- | --- | --- |
| Shell-based | Dockerfile.buster | Dockerfile.jessie-vlc |
| XWindow (SSH + X11Fowarding) | Dockerfile.buster.x11forwarding | Dockerfile.jessie-vlc.x11forwarding |
| XWindow (XWindow + VNC) | Dockerfile.buster.vnc | Dockerfile.jessie-vlc.vnc |


## How to Build

Usage:
```
docker build -t petablox/debloat-builder:<TAG> -f <DOCKERFILE>
```

### Pre-defined Tags
| Dockerfile | Tag |
| --- | --- |
| Dockerfile.buster | buster |
| Dockerfile.buster.x11forwarding | buster-x11-ssh |
| Dockerfile.buster.vnc | buster-x11-vnc |
| Dockerfile.jessie-vlc | jessie-vlc |
| Dockerfile.jessie-vlc.x11forwarding | jessie-vlc-x11-ssh |
| Dockerfile.jessie-vlc.vnc | jessie-vlc-x11-vnc |


### How to use

#### Bash-shell
...

#### SSH+X11Forwarding
0. XWindow client must be running on the remote host. (Linux: XWindow, MacOS: XQuartz, and Windows: Xming)

1. Run the docker
Usage:
```
docker run -p <custom-ssh-port>:22 -d --name <container-name> petablox/debloat-builder:<TAG>
```

Example: ssh server will be mapped to port 2020 and container-name is my-test
```
docker run -p 2020:22 -d --name my-test petablox/debloat-builder:buster-x11-ssh
```

(Optional) If you want to use your ssh-keys of the host machine for cloning github-repo in the container,
please mount your ~/.ssh to /home/aspire/.ssh.

```
docker run -p 2020:22 -v ~/.ssh:/home/aspire/.ssh -d --name my-test petablox/debloat-builder:buster-x11-ssh
```

2. Connect the docker-container through ssh with x11-forwarding

From a remote machine (e.g., your laptop or PC)
```
ssh -p 2020 -Y aspire@fir07.seas.upenn.edu
```

From the host machine (e.g., fir07.seas.upenn.edu)
```
ssh -p 2020 aspire@localhost
```

#### XWindow + VNC
The docker exposes VNC port (5901) and Web-VNC port (6901). You must give a mapping to external ports which are not conflict to other dockers.

1. Run the docker

Usage:
```
docker run -p <vnc-port>:5901 -p <web-vnc-port>:6901 --name <container-name> petablox/debloat-builder:<TAG>
```

Example: Expose VNC-Port=5901 and Web-VNC-Port=6901
```
docker run -p 5901:5901 -p 6901:6901 -d --name my-test petablox/debloat-builder:buster-x11-vnc
```

2. Connect to the docker

- Using VNC client: fir07.seas.upenn.edu:1

- Through Web-browser: http://fir07.seas.upenn.edu:6901/?password=vncpassword

3. VNC Options

- VNC\_PW: Change VNC's login password (default=vncpassword)
- VNC\_RESOLUTION: Change VNC's screen resolution (default=1280x1024)

