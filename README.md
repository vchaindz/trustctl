rename and change config.example to config.json or use env variables URL and API_KEY


**Usage**: `trustctl.py [OPTIONS] COMMAND [ARGS]..`.

**Options**:
 ` --help Show this message and exit.`

**Commands**:

- authenticatedigest
- getimagedigest
- listprojects
- notarizedigest
- projectdetails
- projectidbydigest
- projectsetdigest
- raw

**Examples**:

- List all projects: `trustctl.py listprojects`
- List all projects as json: `trustctl.py raw`
- Get image digest by container name: `trustctl.py getimagedigest codenotary/immudb:1.4.1`
- Find Project by Image Digest: `trustctl.py projectidbydigest sha256:45cc5928854df0da3dc84c32457b511683dfaecc9ad483510f380afd11750552`
- Trust Image Digest: `trustctl.py notarizedigest sha256:45cc5928854df0da3dc84c32457b511683dfaecc9ad483510f380afd11750552`
- Verify Image Digest: `trustctl.py authenticatedigest sha256:45cc5928854df0da3dc84c32457b511683dfaecc9ad483510f380afd11750552`
