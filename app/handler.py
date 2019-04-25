#! /usr/bin/env python3

import configparser
import logging
import os
import re
import requests

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

token = os.environ['ASANA_API_TOKEN']
github_token = os.environ['GITHUB_API_TOKEN']

project_id = config.getint('DEFAULT', 'project_id')
not_started_id = config.getint('DEFAULT', 'not_started_id')
in_dev_id = config.getint('DEFAULT', 'in_dev_id')
in_pr_id = config.getint('DEFAULT', 'in_pr_id')
merged_done_id = config.getint('DEFAULT', 'merged_done_id')

asana_url = "https://app.asana.com/api/1.0/tasks"


def handler(event, context):
    logger.error('## EVENT')
    logger.error(event)
    task_id = find_task_id(event.pull_request)  # wherever the pr body is
    get_and_update_task(task_id, event.action, event.pull_request)


def find_task_id(pr_object):
    asana_match = re.compile(
        r"(https?:\/\/)(app.asana.com\/0\/{}\/)([0-9]*)".format(project_id))
    return asana_match.search(pr_object.description).group(3)


def json_headers():
    return {'content-type': 'application/json',
            'Authorization': "Bearer {}".format(os.environ['ASANA_API_TOKEN'])}


def url_headers():
    return {'content-type': 'application/x-www-form-urlencoded',
            'Authorization': "Bearer {}".format(os.environ['ASANA_API_TOKEN'])}


def get_and_update_task(task_id=os.environ["ASANA_TEST_TASK_ID"],
                        action='closed', pr={'merged': 'true'}):
    r = requests.get("{}/{}".format(asana_url, task_id),
                     headers=json_headers())
    if r.status_code == 200:
        try:
            task = r.json()['data']
            confirm_project(task)
            update_project(task, action, pr)
        except KeyError as e:
            raise Exception(
                "No data found for task {}, reason {}".format(task_id, e))

    else:
        raise Exception(
            "Received bad status code from asana, {}".format(r.status_code))


def confirm_project(task):
    if any(confirm_member(member) for member in task["memberships"]):
        return True
    raise Exception(
        "Task {} is not in on the project board in Not Started, in Dev, or in PR"
        .format(task['id']))


def confirm_member(member):
    if member['project']['id'] == project_id:
        if (member['section']['id'] in [not_started_id, in_dev_id, in_pr_id]):
            return True
    return False


def update_project(task, action, pr):
    try:
        remove_section(task)
        add_section(task, action, pr)
    except Exception as e:
        raise Exception("Updating project failed, {}".format(e))


def remove_section(task):
    for member in task['memberships']:
        do_remove_section(member, task['id'])


def do_remove_section(member, task_id):
    current_project_id = member['project']['id']
    if current_project_id == project_id:
        section = member['section']['id']
        if (section in [not_started_id, in_dev_id, in_pr_id]):
            data = {'project': project_id, 'section': section}
            r = requests.post("{}/{}/removeProject".format(asana_url,
                                                           task_id),
                              headers=url_headers(),
                              data=data)
            logger.error("remove section %s status code %s",
                         section, r.status_code)


def add_section(task, action, pr):
    task_id = task['id']
    if action in ('opened', 'edited'):
        do_add_section(task_id, in_pr_id)
    elif action == 'closed' and pr['merged']:
        do_add_section(task_id, merged_done_id)


def do_add_section(task_id, section):
    data = {'project': "{}".format(
        project_id), 'section': "{}".format(section)}
    logger.error("%s", data)
    r = requests.post("{}/{}/addProject".format(asana_url, task_id),
                      headers=url_headers(), data=data)
    logger.error("add section %s status code %s",
                 section, r.status_code)
