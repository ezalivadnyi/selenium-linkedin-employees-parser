Chrome seem to crash in Docker containers on certain pages due to too small **/dev/shm**. So you may have to fix the small /dev/shm size:   

```sudo mount -t tmpfs -o rw,nosuid,nodev,noexec,relatime,size=512M tmpfs /dev/shm```
