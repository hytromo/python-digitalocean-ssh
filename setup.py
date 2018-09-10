import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='do_to_ssh_config',
    version='0.0.4',
    author='Alexandros Solanos',
    author_email='solanosalex@gmail.com',
    description='Combine DO droplets with your ssh configuration',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/hytromo/digital-ocean-to-ssh-config',
    packages=setuptools.find_packages(),
    install_requires=[
        'python-digitalocean',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
