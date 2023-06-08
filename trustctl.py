#!/usr/bin/python3

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
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project", headers=headers, verify=False)
    print(response.text)
    return 

@click.command()
def listprojects():
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project", headers=headers, verify=False)
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
@click.argument('imagedigest')
def authenticatedigest(imagedigest):
    url, api_key = load_config()
    headers = {'X-Api-Key': api_key}
    response = requests.get(url + "/api/v1/project", headers=headers, verify=False)
    data = response.json()

    # Initialize the pretty table
    table = PrettyTable()
    table.field_names = ["Name", "Version", "UUID", "Digest", "Trustlevel"]

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

    # Print the table
    print(table)

    return


cli.add_command(raw)
cli.add_command(listprojects)
cli.add_command(projectdetails)
cli.add_command(getimagedigest)
cli.add_command(projectidbydigest)
cli.add_command(projectsetdigest)
cli.add_command(notarizedigest)
cli.add_command(authenticatedigest)

if __name__ == '__main__':
    cli()

