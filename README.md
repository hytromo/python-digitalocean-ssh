# Digital ocean -> ssh config

Installation

```
python3 -m pip install python-digitalocean-ssh
```

Running standalone, this python 3 script will help you keep your ssh config in sync with your digital ocean droplets

```bash
$ python3 -m digitalocean_ssh production

· Reading /home/alex/.config/python-digitalocean-ssh/production.json
· Parsing /home/alex/.ssh/config
· Fetching droplets from DO
· Writing into your ssh config file

✓ Done, 11 droplets synced
```

## Features

* Supports different ssh keys for each droplet, depending on the DO tags of the droplet
* Works with different configurations and can write in different sections of your ssh config
* Can be used as a module that combines DO and SSH information

## How to

### Step 1: Create the json configuration file
Save this at `~/.config/python-digitalocean-ssh/<name>.json`, where `<name>` is how you want to call it, e.g. `production` or `testing` or anything else. For this example I will use `production`.

```json
{
    "token": "DIGITAL_OCEAN_READ_ONLY_TOKEN_HERE",
    "keys": {
        "tagToKey": {
        },
        "default": {
            "key": "common",
            "priority": 0
        }
    },
    "startMark": "# DO production",
    "endMark": "# /DO production",
    "hostPrefix": "do-prod-"
}
```
*Note*: This is the simplest possible configuration file that uses the same key for every droplet and the droplet name as `Host`, for more options, read on.

1. Generate a new personal DO API read-only access token [here](https://cloud.digitalocean.com/account/api/tokens)
2. `hostPrefix` is what prefix to add in the `Host` key in your ssh config for each droplet loaded through this configuration, can be anything you want

### Step 2: Add the 2 marks in your ssh config
The above json configuration contains the `startMark` and `endMark`. These should be somewhere inside your ssh configuration and can be whatever you want (start with `#` for ssh config comments, though):
```ssh
# DO production
# /DO production
```

Between these 2 marks the script will **delete** everything and add the new entries. Be careful not to add your own hosts between these 2 marks.

<p align="center">
  <img width="460" height="300" src="https://media.giphy.com/media/l0HUldzuCa0S16SkM/giphy.gif">
</p>

### Step 3: Run the script

```bash
$ python3 -m digitalocean_ssh production

· Reading /home/alex/.config/python-digitalocean-ssh/production.json
· Parsing /home/alex/.ssh/config
· Fetching droplets from DO
· Writing into your ssh config file

✓ Done, 11 droplets synced
```

Now your ssh config will look like this:
```ssh
# DO production
Host do-prod-control-center1517024146
    # control-center1517024146
    Hostname X.X.X.X
    IdentityFile ~/.ssh/common
    User user
Host do-prod-control-center1517027030
    # control-center1517027030
    Hostname X.X.X.X
    IdentityFile ~/.ssh/common
    User user
... 9 more entries
# /DO production
```

If you have autogenerated ugly `Host` names derived from the droplet names, you can make it work with the droplet tags instead; read on.

# Use this as a module

With the configuration files at the appropriate place, you can use this as a module to create powerful python scripts:
```python
from digitalocean_ssh import DO
import sys

client = DO(True) # enable debugging

config_type = sys.argv[1] # must pass the configuration type as an argument, e.g. 'production'

config = client.get_config(config_type)
ssh_config = client.parse_ssh_config(config)
droplets = client.fetch_droplets(config)

print(droplets) # DO droplets with combined ip/tags/ssh config information
```

## I want to use a different ssh key, not `common`!

* Change the `keys.default.key` setting

## I want to use a different ssh key per droplet tag!

* Change the `keys.tagToKey` setting and add in it entries like:

```json
"control-center": {
    "key": "cc_prv",
    "priority": 7
},
"consul-server": {
    "key": "cs_prv",
    "priority": 6
},
"postgres-master": {
    "key": "common",
    "priority": 5
}
```

The final config will look like this:

```json
{
    "token": "DIGITAL_OCEAN_READ_ONLY_TOKEN_HERE",
    "keys": {
        "tagToKey": {
            "control-center": {
                "key": "cc_prv",
                "priority": 7
            },
            "consul-server": {
                "key": "cs_prv",
                "priority": 6
            },
            "postgres-master": {
                "key": "common",
                "priority": 5
            }
        },
        "default": {
            "key": "common",
            "priority": 0
        }
    },
    "startMark": "# DO production",
    "endMark": "# /DO production",
    "hostPrefix": "do-prod-"
}
```

*Important*: A droplet can have more than 1 tag, that's why there's a field called `priority` there. In the above example, if a droplet has both the `control-center` and `consul-server` tags, it will use the key with the higher priority (here `control-center`). If a droplet has no tags or its tags do not appear in `tagToKey`, it will use the default key.

For the droplets that match a specific tag, now the `Host` in the ssh config will have the name of the tag, not the droplet name:

```ssh
# DO production
Host do-prod-control-center
    # control-center1517024146
    Hostname X.X.X.X
    IdentityFile ~/.ssh/cc_prv
    User user
Host do-prod-control-center2
    # control-center1517027030
    Hostname X.X.X.X
    IdentityFile ~/.ssh/cc_prv
    User user
... more entries
# /DO production
```

This is convenient for large environments where the droplet names are autogenerated

*Note*: The droplet name is still visible as a comment in the first line of each entry

*Note*: As shown in the above example, if 2 or more droplets share the same tag, an ascending number is appended to the `Host` value.

Now you can see everything easily using ssh's tab completion, and connect anywhere:
```
$ ssh do-prod- <hit TAB key twice>

do-prod-control-center   do-prod-mongodb  do-prod-load-balancer    do-prod-nodejs2          do-prod-postgres-slave   do-prod-blog
do-prod-control-center2  do-prod-landing-page     do-prod-nodejs           do-prod-postgres-master  do-prod-redis            
```

## I have production *and* testing and I work in 10 different companies!

Simply create different configuration files under `~/.config/python-digitalocean-ssh/`, one for each use case of yours, like `production.json` and `testing.json`. It will be useful to have a different `hostPrefix` for each use case.

Also, add the different markings in your ssh config file, e.g.:

```ssh
# DO production
# /DO production

# DO testing
# /DO testing
```

Now if you run
```bash
$ python3 -m digitalocean_ssh production
```
it will go on and read from `production.json` and write in the corresponding marking inside your ssh config. And if you run
```bash
$ python3 -m digitalocean_ssh testing
```
it will go on and read from `testing.json` and write in the corresponding marking.


## Can I safely re-run the script any times I want?

Yes, provided that you haven't included any entries of yours between the markings you've specified in the configuration. Everything between the markings is deleted each time the script runs.