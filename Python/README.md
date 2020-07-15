## Python Mattermost commands

### memeslash.py

Create a `/meme` command thats sends an in-channel response depending on the activation phrase provided. The database of possible activation phrases and responses can be created via the same `/meme` command and it is stored in a JSON file for persistence across service restarts.

```
usage: Mattermost handle slash command to post meme URLs [-h] [--host HOST]
                                                         [--port PORT]
                                                         [--token TOKEN]
                                                         [--persistence PERSISTENCE]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           Host to bind. (default: localhost)
  --port PORT           Host to bind. (default: 10000)
  --token TOKEN         Token to match. (default: )
  --persistence PERSISTENCE
                        Name of the file containing the dictionary of meme
                        URLs. (default: persistence.json)
```

The inline help of the slash command is:

```
Show a configurable response in channel

Commands:

- /meme help
shows this help

- /meme list
shows the list of activation phrases

- /meme add KEY VALUE
add KEY as activation phrase that will show VALUE, possibly overriding a previous entry

- /meme del KEY
delete the activation phase KEY

- /meme PHRASE
show a response partially matching the given PHRASE
```
