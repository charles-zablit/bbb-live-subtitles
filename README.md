# bbb-live-subtitles
BBB plugin for automatic subtitles in conference calls

# Subtitling of BBB Participants
This project is to subtitle BBB participants each individually.

# Installation:
Requirements:
Works with BigBlueButton 2.2.x and Ubuntu 16.04
Working kaldi-model-server
When working with different machines (see Usage) the configuration of the redis server must be changed to allow access.
## Configure Redis to Accept Remote Connections
To accept remote connections change the configuration file
```Shell
sudo nano /etc/redis/redis.conf
```
change the line `bind 127.0.0.1` and add the IP Adress of the server(eg. 192.168.0.1): `bind 127.0.0.1 192.168.0.1`.
Save the file and restart the redis server
```Shell
sudo /etc/init.d/redis-server restart
```
You can now test the access from another machine with `redis-cli` for example:
```Shell
redis-cli -h 192.168.0.1 -p 6379
```

## Clone and Install
At first create a directory and clone the projects into it:
```Shell
mkdir ~/projects
cd ~/projects
git clone https://www.github.com/uhh-lt/bbb-live-subtitles
```
Create kaldi-model-server and follow the [instructions](https://github.com/uhh-lt/kaldi-model-server#installation)

After these steps create a python virtual environment and start it
```Shell
cd ~/projects/bbb-live-subtitles
virtualenv -p python3 bbb_env
source bbb_env/bin/activate
```
Install the dependencies
```Shell
pip3 install redis jaspion pymongo
```

# Usage
To use this project you can run every script on independent machines or all on the same.
All the scripts need to run before the participant joins the conference.
At first you need to start `esl_to_redis.py`. This module creates a connection to the freeswitch Software through [ESL](https://freeswitch.org/confluence/display/FREESWITCH/Event+Socket+Library) and writes every information about the media bugs into the information redis channel.
The next to start is `check_redis_and_start_upload.py`. This module checks the redis information channel for started bugs and starts the file upload onto the asr channel.
The `kaldi_starter.py` module is in my configuration on another machine (could also run on the same machine) and starts for media bug an own kaldi instance. Kaldi sends the recognized speech into a asr redis channel.
With the `mongodbconnector.py` module the ASR Data is send into the mongodb database. To see the subtitle the participant needs to start the subtitle function on BBB and activate the subtitles.