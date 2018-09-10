from .DO import DO

import sys

client = DO(True)

client.print()

if len(sys.argv) != 2:
    client.error(
        'please provide the configuration file name (e.g. production)', Exception)

config_type = sys.argv[1]

config = client.get_config(config_type)

ssh_config = client.parse_ssh_config(config)
droplets = client.fetch_droplets(config)

client.write_to_ssh_config(droplets, ssh_config)

client.print()
client.print('✓ Done,', len(droplets), 'droplet' +
               ('' if len(droplets) is 1 else 's') + ' synced')
