#!/usr/local/bin/python

## Author: vchaindz
## Company: Codenotary, Inc
## Version: 0.1

import click
import json
import requests
import urllib3
import subprocess
from prettytable import PrettyTable
import os

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_config():
    url = os.getenv("URL")
    api_key = os.getenv("API_KEY")

    if not url or not api_key:
        with open('config.json') as f:
            data = json.load(f)
            url = data["url"]
            api_key = data["api_key"]

    return url, api_key

@click.group()
def cli():
    pass

@click.command()
def raw():
    """Returns a raw digest. Can be used for pinging the instance"""
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project", headers=headers, verify=False)
    print(response.text)
    return 

@click.command()
@click.option('--perpage', default=100, help='Number of items per page')
@click.option('--page', default=1, help='Page number')
def listprojects(perpage, page):
    """Prints a list of all or part of projects"""
    url, api_key = load_config()
    headers = {'Content-Type': 'application/json', 'X-Api-Key': api_key}
    getprojecturl = url + "/api/v1/project?pageSize=" + str(perpage) + "&pageNumber=" + str(page)
    response = requests.get(getprojecturl, headers=headers, verify=False)
    data = json.loads(response.text)
    
    # Create a table with headers
    table = PrettyTable()
    table.field_names = ["Name", "Version", "Classifier", "UUID"]

    # Loop through the data and add it to the table
    for item in data:
        name = item.get('name', 'N/A')
        version = item.get('version', 'N/A')
        classifier = item.get('classifier', 'N/A')
        uuid = item.get('uuid', 'N/A')
        table.add_row([name, version, classifier, uuid])
    
    print(table)
    return

@click.command()
@click.argument('imagedigest')
def projectidbydigest(imagedigest):
    """Prints the project UUID and name by digest. The argument is the digest of the image."""
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project", headers=headers, verify=False)
    data = response.json()
    # Create a table with headers
    table = PrettyTable()
    table.field_names = ["Name", "Version", "UUID", "Digest"]

    for project in data:
        for prop in project.get('properties', []):
            if prop.get('propertyName') == 'imagedigest' and prop.get('propertyValue') == imagedigest:
                uuid = project.get('uuid')
                name = project.get('name')
                version = project.get('version')
                table.add_row([name, version, uuid, imagedigest])

    print(table)
    return

@click.command()
@click.argument('image')
def getimagedigest(image):
    """Prints the digest of an image read from Docker. The argument is the image name."""
    command = "regctl image digest " + image
    imagedigest = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Create a table with headers
    table = PrettyTable()
    table.field_names = ["Name", "Digest"]
    table.add_row([image, imagedigest.stdout])

    print(table)
    return

@click.command()
@click.argument('uuid')
@click.argument('image')
def projectsetdigest(uuid,image):
    """Sets the digest of an image to a project. The arguments are the project UUID and the image name."""
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    command = "regctl image digest " + image
    imagedigest = subprocess.run(command, shell=True, capture_output=True, text=True)
    data = {
            "groupName":"ImageDigest",
            "propertyName":"imagedigest",
            "propertyValue":imagedigest.stdout,
            "propertyType":"STRING"
           }

    headers = {
              "Content-Type": "application/json",
              "X-API-Key": api_key
              }
    urlpost = url + "/api/v1/project/" + uuid + "/property"
    create = requests.put(urlpost, headers=headers, json=data, verify=False)
    update = requests.post(urlpost, headers=headers, json=data, verify=False)

    print("Image " + image + " with digest " + imagedigest.stdout.strip('\n') + " has been added to project " + uuid)
    return

@click.command()
@click.argument('project_id')
def projectdetails(project_id):
    """Prints the details of a project. The argument is the project UUID."""
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project/" + project_id, headers=headers, verify=False)

    # Parse the JSON response
    data = json.loads(response.text)

    # Extract the desired fields
    name = data.get('name', 'N/A')
    version = data.get('version', 'N/A')
    classifier = data.get('classifier', 'N/A')
    uuid = data.get('uuid', 'N/A')
    properties = data.get('properties', [{}])

    # Initialize the pretty table
    table = PrettyTable()
    table.field_names = ["Name", "Version", "Classifier", "UUID", "PropertyValue"]

    # Loop through the properties and add rows to the table
    for prop in properties:
        property_value = prop.get('propertyValue', 'N/A')
        table.add_row([name, version, classifier, uuid, property_value])

    # Print the table
    print(table)
    return

@click.command()
@click.argument('imagedigest')
def notarizedigest(imagedigest):
    """Notarize a digest. The argument is the digest of the image."""
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project", headers=headers, verify=False)
    data = response.json()
    for project in data:
        for prop in project.get('properties', []):
            if prop.get('propertyName') == 'imagedigest' and prop.get('propertyValue') == imagedigest:
                uuid = project.get('uuid')
                data = {
                    "uuidsOf": [uuid],
                    "hashOf": [""],
                    "namesOf": [""],
                    "purlsOf": [""],
                    "newStatus": 0
                }
                headers = {
                    "Content-Type": "application/json",
                    "X-API-Key": api_key
                }  
                urlpost = url + "/api/v1/integrations/trustcenter/setStatus"
                response = requests.post(urlpost, headers=headers, json=data, verify=False)
                print("Image with digest " + imagedigest + " has been trusted")
                return

@click.command()
@click.argument('project_id')
@click.option('--trustlevel', required=True, type=int)
def notarizeproject(project_id,trustlevel):
    """Notarize a project. The arguments are the project UUID and the trustlevel. Possible values are: 
0 - Trusted
1 - Untrusted
2 - Not notarized
3 - Unsupported"""
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    data = {
           "uuidsOf": [project_id],
           "hashOf": [""],
           "namesOf": [""],
           "purlsOf": [""],
           "newStatus": trustlevel
    }
    headers = {
              "Content-Type": "application/json",
              "X-API-Key": api_key
              }
    urlpost = url + "/api/v1/integrations/trustcenter/setStatus"
    response = requests.post(urlpost, headers=headers, json=data, verify=False)
    print("Project " + project_id + " has been notarized with Trustlevel ", trustlevel)
    return



@click.command()
@click.argument('imagedigest')
@click.option('--code', is_flag=True, default=False, help='Return a code based on the trustlevel.')
def authenticatedigest(imagedigest, code):
    """Print the trustlevel - authenticate a digest. The argument is the digest of the image."""
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project", headers=headers, verify=False)
    data = response.json()

    # Initialize the pretty table
    table = PrettyTable()
    table.field_names = ["Name", "Version", "UUID", "Digest", "Trustlevel"]

    trustlevel_code = {
        "TRUSTED": 0,
        "UNTRUSTED": 1,
        "NOT NOTARIZED": 2,
        "UNSUPPORTED": 3,
    }

    code_to_return = -1  # Default code if no project matches the imagedigest

    for project in data:
        for prop in project.get('properties', []):
            if prop.get('propertyName') == 'imagedigest' and prop.get('propertyValue') == imagedigest:
                uuid = project.get('uuid')
                name = project.get('name')
                version = project.get('version')
                data = [{"uuid": uuid}]
                headers = {
                    "Content-Type": "application/json",
                    "X-API-Key": api_key
                }
                urlpost = url + "/api/v1/integrations/trustcenter/trustlevel"
                response = requests.post(urlpost, headers=headers, json=data, verify=False)
                trustlevel = json.loads(response.text)
                trustlevel = trustlevel[0]['trustlevel']
                table.add_row([name, version, uuid, imagedigest, trustlevel])

                # Update the code to return based on the trustlevel
                code_to_return = trustlevel_code.get(trustlevel.upper(), -1)
 		# If the --code flag is set, return the code
                if code:
                   print(uuid+","+name+","+imagedigest+","+trustlevel+",",code_to_return)
    
    # Print the table
    if not code:
       print(table)

    return

@click.command()
@click.argument('project_id')
@click.option('--trustlevel', required=True, type=int)
def authenticateproject(project_id, trustlevel):
    """Print the trustlevel of a project = authenticate a project. The arguments are the project UUID and the trustlevel."""
    url, api_key = load_config()

    trustlevel_code = {
        "TRUSTED": 0,
        "UNTRUSTED": 1,
        "NOT NOTARIZED": 2,
        "UNSUPPORTED": 3,
    }
    headers = {
               "Content-Type": "application/json",
               "X-API-Key": api_key
    }
    urlpost = url + "/api/v1/integrations/trustcenter/trustlevel"
    data = [{"uuid": project_id}]
    response = requests.post(urlpost, headers=headers, json=data, verify=False)
    realtrustlevel = json.loads(response.text)
    realtrustlevel = realtrustlevel[0]['trustlevel']
    # Update the code to return based on the trustlevel
    code_to_return = trustlevel_code.get(realtrustlevel.upper(), -1)
    if trustlevel == code_to_return:
       print("true")
    else:
       print("false")

    return


cli.add_command(raw)
cli.add_command(listprojects)
cli.add_command(projectdetails)
cli.add_command(getimagedigest)
cli.add_command(projectidbydigest)
cli.add_command(projectsetdigest)
cli.add_command(notarizedigest)
cli.add_command(notarizeproject)
cli.add_command(authenticatedigest)
cli.add_command(authenticateproject)

if __name__ == '__main__':
    cli()

