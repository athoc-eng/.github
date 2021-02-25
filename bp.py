#!/usr/bin/env python

import json, requests, argparse, urllib.parse as urlparse
from urllib.parse import parse_qs

parser = argparse.ArgumentParser()
parser.add_argument("--Token", help="Access Token")
parser.add_argument("--GH_API_URL", help="Access Token", default="https://api.github.com")
parser.add_argument("--Organization", help="GitHub Organization")
parser.add_argument("--Action", help="Set or Delete Branch Protection", default="set")
parser.add_argument("--Repos", help="Comma separated list. If empty or null, all repos will be considered")
args = vars(parser.parse_args())

def get_auth_token():
    return args["Token"]


def make_api_url(*arguments):
    return '/'.join((args["GH_API_URL"], 'repos', *arguments))


def make_api_headers():
    APPLICATION_HEADER_VALUE='application/vnd.github.loki-preview+json'
    return {
        'Authorization': 'token {:s}'.format(get_auth_token()),
        'Accept': APPLICATION_HEADER_VALUE,
    }


def get_branches(target_repo):   
    repo_branches = [] 
    url = make_api_url(target_repo, 'branches')
    results = requests.get(url, headers=make_api_headers())
    if results.status_code != 200:
        raise Exception("Exception Occurred: " + str(results.status_code) + ": " + results.reason + ": " + results.text)
    else:
        for result in results.json():
            if result["name"] in ["main", "release"]:
                repo_branches.append(result["name"])
    
    return repo_branches


def get_protection(target_repo, branch):   
    url = make_api_url(target_repo, 'branches', branch, 'protection')
    result = requests.get(url, headers=make_api_headers())
    if result.status_code != 200:
        raise Exception("Exception Occurred: " + str(result.status_code) + ": " + result.reason + ": " + result.text)

    return result.json()


def set_protection(target_repo, branch, data=None):
    url = make_api_url(target_repo, 'branches', branch, 'protection')
    if data is None:
        data = {
            'required_status_checks': None,
            'restrictions': {
                'users': [],
                'teams': [],
            },
        }
    result = requests.put(url, headers=make_api_headers(), json=data)
    if result.status_code != 200:
        raise Exception("Exception Occurred: " + str(result.status_code) + ": " + result.reason + ": " + result.text)
    


def delete_protection(target_repo, branch):
    url = make_api_url(target_repo, 'branches', branch, 'protection')
    result = requests.delete(url, headers=make_api_headers())
    if result.status_code != 204:
        raise Exception("Exception Occurred: " + str(result.status_code) + ": " + result.reason + ": " + result.text)

    return result


def get_repos():
    gh_repos = []
    if args["Repos"] != None:
        # gh_repos = [args["Organization"] + "/" + s for s in args["Repos"].split(',')]
        gh_repos = args["Repos"].split(',')
    else:
        url = args["GH_API_URL"] + "/orgs/" + args["Organization"] + "/repos?type=all&per_page=100"        
        results = requests.get(url, headers=make_api_headers())
        if results.status_code != 200:
            raise Exception("Exception Occurred: " + str(results.status_code) + ": " + results.reason + ": " + results.text)  

        for result in results.json() :
            if result["name"] != ".github":
                gh_repos.append(result["full_name"])

    return gh_repos
    
    
def getPageCount(itemCount, limit):
    pageCount = 0
    if itemCount < limit:
        pageCount = 1
    else:
        rem = itemCount % limit
        if rem > 0:
            pageCount = (itemCount // limit) + 1
        else:
            pageCount = (itemCount // limit)
    
    return pageCount      


def getAllRepos():
    limit = 100
    gh_repos = []
    if args["Repos"] != None:
        gh_repos = args["Repos"].split(',')
    else:
        url = args["GH_API_URL"] + "/orgs/" + args["Organization"] + "/repos?type=all&per_page=1"
        repoCntResult = getRepoResults(url)
        parsed = urlparse.urlparse(repoCntResult.links.get("last")["url"])
        repoCount = int(parse_qs(parsed.query)["page"][0])
        pageCount = getPageCount(repoCount, limit)
        for pageNum in range(pageCount):
            pageNum = pageNum + 1
            url = args["GH_API_URL"] + "/orgs/" + args["Organization"] + "/repos?type=all&per_page=" + str(limit) + "&page=" + str(pageNum)
            results = getRepoResults(url)
            for result in results.json():
                if result["name"] != ".github":
                    gh_repos.append(result["full_name"])

    return gh_repos     

def getRepoResults(url):
    results = requests.get(url, headers=make_api_headers())
    if results.status_code != 200:
        raise Exception("Exception Occurred: " + str(results.status_code) + ": " + results.reason + ": " + results.text)  

    return results

def main():    
    print("Entering Main function inside Python")
    try:
        print("Action: " + args["Action"])
        repos = getAllRepos()
        f = open('bp.json',)
        data = json.load(f)
        for repo in repos:
            print("Repo: " + repo)
            branches = get_branches(repo)
            for branch in branches:
                if args["Action"] == "set":
                    print("Setting Branch Protection for " + branch)
                    set_protection(repo, branch, data)
                    print("Set Branch Protection Succesfully for " + branch)
                elif args["Action"] == "delete":
                    print("Deleting Branch Protection for " + branch)
                    delete_protection(repo, branch)
                    print("Deleted Branch Protection Succesfully for " + branch)                
    
    except:
        raise


if __name__ == "__main__":
    main()
