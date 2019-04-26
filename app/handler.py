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

asana_url = "https://app.asana.com/api/1.0/tasks"
token = os.environ['ASANA_API_TOKEN']
github_token = os.environ['GITHUB_API_TOKEN']

not_started_id = config.getint('DEFAULT', 'not_started_id')
in_dev_id = config.getint('DEFAULT', 'in_dev_id')
in_pr_id = config.getint('DEFAULT', 'in_pr_id')
merged_done_id = config.getint('DEFAULT', 'merged_done_id')


def handler(event, context):  # pylint:disable=unused-argument
    logger.error('## EVENT')
    logger.error(event)
    # https://developer.github.com/v3/activity/events/types/#pullrequestevent
    asana_ids = find_asana_ids(event['pull_request'])
    get_and_update_task(asana_ids, event['action'], event['pull_request'])


def find_asana_ids(pr_object):
    regex = re.compile(
        r"(https?:\/\/app.asana.com\/0\/([0-9]*)\/([0-9]*))")
    match = regex.search(pr_object['description'])
    return {'task_id': match.group(3), 'project_id': match.group(2)}


def json_headers():
    return {'content-type': 'application/json',
            'Authorization': "Bearer {}".format(os.environ['ASANA_API_TOKEN'])}


def url_headers():
    return {'content-type': 'application/x-www-form-urlencoded',
            'Authorization': "Bearer {}".format(os.environ['ASANA_API_TOKEN'])}


def get_and_update_task(ids={'task_id': os.environ["ASANA_TEST_TASK_ID"],
                             'project_id': config.getint('TEST', 'project_id')},
                        action='closed', pr={'merged': 'true', 'html_url': 'http://testing.com'}):
    project_id = int(ids['project_id'])
    task_id = ids['task_id']
    r = requests.get("{}/{}".format(asana_url, task_id),
                     headers=json_headers())
    if r.status_code == 200:
        try:
            task = r.json()['data']
            add_github_link(task, pr['html_url'])
            confirm_project(task, project_id)
            update_project(task, project_id, action, pr)
        except KeyError as e:
            raise Exception(
                "No data found for task {}, reason {}".format(task_id, e))

    else:
        raise Exception(
            "Received bad status code from asana, {}".format(r.status_code))


def find(f, array):
    for item in array:
        if f(item):
            return item


def add_github_link(task, url):
    github_field = find(
        lambda field: field["name"] == "GitHub PR", task['custom_fields'])
    if github_field:
        data = {'data': {'custom_fields': {}}}
        data['data']['custom_fields'][github_field["id"]] = url
        requests.put("{}/{}".format(asana_url,
                                    task["id"]), headers=json_headers(), json=data)
        logger.error("updating github field %s with %s",
                     github_field["id"], url)


def confirm_project(task, project_id):
    if any(confirm_member(member, project_id) for member in task["memberships"]):
        return True
    raise Exception(
        "Task {} is not on the project board {} in Not Started, in Dev, or in PR"
        .format(task['id'], project_id))


def confirm_member(member, project_id):
    if member['project']['id'] == project_id:
        if (member['section']['id'] in [not_started_id, in_dev_id, in_pr_id]):
            return True
    return False


def update_project(task, project_id, action, pr):
    try:
        remove_section(task, project_id)
        add_section(task, project_id, action, pr)
    except Exception as e:
        raise Exception("Updating project failed, {}".format(e))


def remove_section(task, project_id):
    for member in task['memberships']:
        do_remove_section(member, task['id'], project_id)


def do_remove_section(member, task_id, project_id):
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


def add_section(task, project_id, action, pr):
    task_id = task['id']
    if action in ('opened', 'edited'):
        do_add_section(task_id, project_id, in_pr_id)
    elif action == 'closed' and pr['merged']:
        do_add_section(task_id, project_id, merged_done_id)
        mark_completed(task_id)


def do_add_section(task_id, project_id, section):
    data = {'project': "{}".format(
        project_id), 'section': "{}".format(section)}
    r = requests.post("{}/{}/addProject".format(asana_url, task_id),
                      headers=url_headers(), data=data)
    logger.error("add section %s status code %s",
                 section, r.status_code)


def mark_completed(task_id):
    data = {'completed': 'true'}
    r = requests.put("{}/{}".format(asana_url, task_id),
                     headers=url_headers(), data=data)
    logger.error("marking complete task %s status code %s",
                 task_id, r.status_code)
