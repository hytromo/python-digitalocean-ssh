#!/usr/bin/env python3

import digitalocean
import sys
import json
import os.path
import functools

is_main = (__name__ == '__main__')

def error(*msg):
    messages = msg[:-1]

    if is_main:
        print('Error:', *messages)
        sys.exit(1)
    else:
        error_type = msg[-1:][0]
        raise error_type(' '.join(messages))

def printIfMain(*msg):
    if is_main:
        print(*msg)


def get_config(config_type):
    config_file_location = os.path.join(
        os.path.expanduser('~'), '.config', 'do_to_ssh_config', config_type + '.json')

    printIfMain('· Reading', config_file_location)

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

    printIfMain('· Parsing', ssh_config_path)

    with open(ssh_config_path, 'r') as file:
        index_number = 0
        for line in file:
            config_lines.append(line)
            if line.strip() == config.get('startMark'):
                marks['start'] = index_number
            elif line.strip() == config.get('endMark'):
                marks['end'] = index_number
            index_number += 1

    if (marks.get('start') is None or marks.get('end') is None):
        error('Start and/or end markings missing, add',
              config.get('startMark'), 'and', config.get('endMark'), 'in your ssh config', LookupError)

    if (marks.get('start') > marks.get('end')):
        error(config.get('startMark'), 'should come before', config.get('endMark'), LookupError)

    # delete the lines between the marks
    for i in reversed(range(marks.get('start') + 1, marks.get('end'))):
        del config_lines[i]

    return {'marks': marks, 'lines': config_lines}


def fetch_droplets(config):
    printIfMain('· Fetching droplets from DO')

    do_manager = digitalocean.Manager(
        token=config.get('token'))
    tag_to_ssh_key = config.get('keys').get('tagToKey')
    default_key = config.get('keys').get('default')

    inserted_name_to_count = {}
    droplets = []
    for droplet in do_manager.get_all_droplets():
        selected_key = None
        hostname = None
        for tag in droplet.tags:
            if tag in tag_to_ssh_key:
                thisKey = tag_to_ssh_key.get(tag)
                if selected_key is None or thisKey.get('priority') > selected_key.get('priority'):
                    selected_key = thisKey
                    hostname = tag  # best case scenario

        if selected_key is None:
            selected_key = default_key

        if hostname is None:
            hostname = droplet.name  # worst case scenario

        if hostname in inserted_name_to_count:
            inserted_name_to_count[hostname] += 1
        else:
            inserted_name_to_count[hostname] = 1

        droplets.append({
            'host': config.get('hostPrefix') + (hostname + str(('' if inserted_name_to_count[hostname] is 1 else inserted_name_to_count[hostname]))),
            'name': droplet.name,
            'ip': droplet.ip_address,
            'tags': droplet.tags,
            'identityFile': '~/.ssh/' + selected_key.get('key')
        })

    return sorted(droplets, key=functools.cmp_to_key(lambda a, b: 1 if a.get('host') > b.get('host') else -1))


def write_to_ssh_config(droplets, ssh_config):
    printIfMain('· Writing into your ssh config file')

    def add_line(insert_index, line):
        config_lines.insert(insert_index, line)

    insert_index = ssh_config.get('marks').get('start')
    config_lines = ssh_config.get('lines')
    for droplet in droplets:

        add_line(insert_index + 1, 'Host ' + droplet.get('host') + '\n')
        add_line(insert_index + 2, '    # ' + droplet.get('name') + '\n')
        add_line(insert_index + 3, '    Hostname ' + droplet.get('ip') + '\n')
        add_line(insert_index + 4, '    IdentityFile ' +
                 droplet.get('identityFile') + '\n')
        add_line(insert_index + 5, '    User user\n')

        insert_index += 5

    with open(get_ssh_config_path(), 'w') as file:
        file.writelines(config_lines)


if is_main:
    printIfMain()

    if len(sys.argv) != 2:
        error('please provide the configuration file name (e.g. production)', Exception)

    config_type = sys.argv[1]

    config = get_config(config_type)

    ssh_config = parse_ssh_config(config)
    droplets = fetch_droplets(config)

    write_to_ssh_config(droplets, ssh_config)

    printIfMain()
    printIfMain('✓ Done,', len(droplets), 'droplet' +
          ('' if len(droplets) is 1 else 's') + ' synced')
