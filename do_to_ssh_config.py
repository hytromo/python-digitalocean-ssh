#!/usr/bin/env python3

import digitalocean
import sys
import json
import os.path
import functools


def error(*msg):
    print('Error:', *msg)
    sys.exit(1)


def get_config():
    if len(sys.argv) != 2:
        error('please provide the configuration file name (e.g. production)')

    config_type = sys.argv[1]
    config_file_location = os.path.join(
        os.path.expanduser('~'), '.config', 'do_to_ssh_config', config_type + '.json')

    print('· Reading', config_file_location)

    with open(config_file_location, 'r') as f:
        config = json.load(f)

    return config


def get_ssh_config_path():
    return os.path.join(os.path.expanduser('~'), '.ssh', 'config')


def parse_ssh_config(config):
    marks = {'start': None, 'end': None}
    config_lines = []
    # find the mark position
    ssh_config_path = get_ssh_config_path()

    print('· Parsing', ssh_config_path)

    with open(ssh_config_path, 'r') as file:
        indexNumber = 0
        for line in file:
            config_lines.append(line)
            if line.strip() == config.get('startMark'):
                marks['start'] = indexNumber
            elif line.strip() == config.get('endMark'):
                marks['end'] = indexNumber
            indexNumber += 1

    if (marks.get('start') is None or marks.get('end') is None):
        error('Start and/or end markings missing, add',
              config.get('startMark'), 'and', config.get('endMark'), 'in your ssh config')

    if (marks.get('start') > marks.get('end')):
        error(config.get('startMark'), 'should come before', config.get('endMark'))

    # delete the lines between the marks
    for i in reversed(range(marks.get('start') + 1, marks.get('end'))):
        del config_lines[i]

    return {'marks': marks, 'lines': config_lines}


def fetch_droplets(config):
    print('· Fetching droplets from DO')

    doManager = digitalocean.Manager(
        token=config.get('token'))
    tagToSshKey = config.get('keys').get('tagToKey')
    defaultKey = config.get('keys').get('default')

    insertedNameToCount = {}
    droplets = []
    for droplet in doManager.get_all_droplets():
        selectedKey = None
        hostName = None
        for tag in droplet.tags:
            if tag in tagToSshKey:
                thisKey = tagToSshKey.get(tag)
                if selectedKey is None or thisKey.get('priority') > selectedKey.get('priority'):
                    selectedKey = thisKey
                    hostName = tag  # best case scenario

        if selectedKey is None:
            selectedKey = defaultKey

        if hostName is None:
            hostName = droplet.name  # worst case scenario

        if hostName in insertedNameToCount:
            insertedNameToCount[hostName] += 1
        else:
            insertedNameToCount[hostName] = 1

        droplets.append({
            'host': config.get('hostPrefix') + (hostName + str(('' if insertedNameToCount[hostName] is 1 else insertedNameToCount[hostName]))),
            'name': droplet.name,
            'ip': droplet.ip_address,
            'identityFile': '~/.ssh/' + selectedKey.get('key')
        })

    return sorted(droplets, key=functools.cmp_to_key(lambda a, b: 1 if a.get('host') > b.get('host') else -1))


def write_to_ssh_config(droplets, ssh_config):
    print('· Writing into your ssh config file')

    def addLine(insertIndex, line):
        config_lines.insert(insertIndex, line)

    insertIndex = ssh_config.get('marks').get('start')
    config_lines = ssh_config.get('lines')
    for droplet in droplets:

        addLine(insertIndex + 1, 'Host ' + droplet.get('host') + '\n')
        addLine(insertIndex + 2, '    # ' + droplet.get('name') + '\n')
        addLine(insertIndex + 3, '    Hostname ' + droplet.get('ip') + '\n')
        addLine(insertIndex + 4, '    IdentityFile ' +
                droplet.get('identityFile') + '\n')
        addLine(insertIndex + 5, '    User user\n')

        insertIndex += 5

    with open(get_ssh_config_path(), 'w') as file:
        file.writelines(config_lines)


if __name__ == '__main__':
    config = get_config()

    ssh_config = parse_ssh_config(config)
    droplets = fetch_droplets(config)

    write_to_ssh_config(droplets, ssh_config)

    print()
    print('✓ Done,', len(droplets), 'droplet' +
          ('' if len(droplets) is 1 else 's') + ' added')
