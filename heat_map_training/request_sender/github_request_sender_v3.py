"""
Contains GithubRequestSender class that provides implementation of
interface for sending API requests
to web-based hosting services for version control in RestAPI
"""
from heat_map_training.request_sender.github_request_sender_base import \
    GithubRequestSenderBase  # pylint: disable=import-error
from heat_map_training.utils.helper import format_date_to_int

GITHUB_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def match_branch_to_commit(branch_list, sha):
    """
    Gets all branches which commit belongs to in a list
    :param branch_list:
    :param sha:
    :return:
    """
    matched_branches = [k for k in branch_list if sha in branch_list[k]]
    if matched_branches:
        return matched_branches
    return "unknown"


class GithubRequestSenderV3(GithubRequestSenderBase):
    """
    Class that provides implementation of interface for sending API requests
    to web-based hosting services for version control using GitHub
    """

    def __init__(self, owner, repo, token='', query=False):
        GithubRequestSenderBase.__init__(self,
                                         base_url="https://api.github.com",
                                         owner=owner,
                                         repo=repo,
                                         token=token,
                                         query=query)
        self.repos_api_url = f'/repos/{self.owner}/{self.repo}'

    # returns a dict in which the key is sha of commit
    # and the value is existing branch it belongs to
    def _get_existing_commit_branch_map(self, list_of_branches):
        result = {}
        if self.get_commits_by_branch(list_of_branches[0]) is None:
            return None
        for branch in list_of_branches:
            for item in self.get_commits_by_branch(branch):
                result.setdefault(branch, set([])).add(item['hash'])
        return result

    # returns plain list of all branches of a repository
    def _get_list_of_branches(self):
        return [d[k] for d in self.get_branches() for k in d if not self.get_branches() is None]

    # returns dict of all commits with key as 'sha' and value as master
    def _get_dict_of_commits(self):
        dict_of_commits = {}
        all_commits = self.get_commits()
        if all_commits is None:
            return None
        for commit in all_commits:
            dict_of_commits.update({commit['hash']: 'master'})
        return dict_of_commits

    # gets all pull requests of repository
    def _get_pull_requests(self):
        endpoint = '/pulls?state=all'
        return self._request(endpoint)

    # gets all pull requests of a repository and
    # returns a dict from parsed branch and a matching commit
    def _get_branches_from_pull_request(self, pull_requests):
        if pull_requests is None:
            return None
        commits_and_branches = {}
        for item in pull_requests:
            commits_and_branches.setdefault(item['head']['label']
                                            .replace(self.owner + ':', ''),
                                            set([])).add(item['head']['sha'])
        return commits_and_branches

    # returns concatenated dict of branches
    # from both pull requests and existing branches with commits
    def _get_complete_commit_branch_map(self):
        existing_branches = self._get_existing_commit_branch_map(self._get_list_of_branches())
        pull_request_branches = self._get_branches_from_pull_request(self._get_pull_requests())
        for key in pull_request_branches:
            for item in pull_request_branches[key]:
                for value in existing_branches.values():
                    if item in value:
                        value.remove(item)
        for key in pull_request_branches:
            for item in pull_request_branches[key]:
                existing_branches.setdefault(key, set([])).add(item)
        return existing_branches

    def get_repo(self):
        """
        Gets information about repository
        in dict format with response body and status code

        :return: dict,
        :raise NotImplementedError
        :Example:
        {
            "repo_name": "repository name",
            "creation_date": "date",
            "owner": "repository owner",
            "url": "repository url"
        }
        """

        response = self._request(self.repos_api_url)
        repo = {
            'id': response['id'],
            'repo_name': response['name'],
            'creation_date': format_date_to_int(response['created_at'],
                                                GITHUB_TIME_FORMAT),
            'owner': response['owner']['login'],
            'url': response['url']
        } if response is not None else None
        return repo

    def get_branches(self):
        """
        Gets list of branches in a repository
        in dict format with response body and status code

        :return: dict
        :raise NotImplementedError
        :Example:
        [
            {
                "name": "branch name"
            },
            ...
        ]
        """
        endpoint = '/branches'
        response = self._request(endpoint)
        return list(map(lambda x: {'name': x['name']}, response))

    def get_commits(self):
        """
        Gets information about all commits in repository
        in dict format with response body and status code

        :return: dict
        :raise NotImplementedError
        :Example:
        [
            {
                "hash": "commit hash",
                "author": "commit author",
                "message": "commit message",
                "date": "date when committed converted to int"
                "branch": "branch which commit belongs to"
            },
            ...
        ]
        """
        endpoint = '/commits'
        response = self._request(endpoint)
        branches = self._get_complete_commit_branch_map()
        response = response.json()
        return [{
            'hash': commit['sha'],
            'author': commit['commit']['author']['name'],
            'message': commit['commit']['message'],
            'date': format_date_to_int(commit['commit']['author']['date'],
                                       GITHUB_TIME_FORMAT),
            'branch': match_branch_to_commit(branches, commit['sha'])
        } for commit in response] if response is not None else None

    def get_commits_by_branch(self, branch_name):
        """
        Gets information about commits of a specific branch
        in dict format with response body and status code

        :param branch_name: string
        :return: dict
        :raise NotImplementedError
        :Example:
        [
            {
                "hash": "commit hash",
                "author": "commit author",
                "message": "commit message",
                "date": "date when committed converted to int"

            },
            ...
        ]
        """
        assert isinstance(branch_name, str), "Branch name must be str, received other"
        endpoint = f'/commits?sha={branch_name}'
        response = self._request(endpoint)
        return list(map(lambda x: {
            'hash': x['sha'],
            'author': x['commit']['author']['name'],
            'message': x['commit']['message'],
            'date': format_date_to_int(x['commit']['author']['date'],
                                       GITHUB_TIME_FORMAT)
        }, response)) if response is not None else None

    def get_commit_by_hash(self, hash_of_commit):
        """
        Gets information about the commit by hash
        in dict format with response body

        :param hash_of_commit: string
        :return: dict
        :raise NotImplementedError
        :Example:
        {
            "hash": "commit hash",
            "author": "commit author",
            "message": "commit message",
            "date": "date when committed converted to int"
            "branch": "branch which commit belongs to"
        }
        """
        assert isinstance(hash_of_commit, str), "Hash of commit must be str, received other"
        endpoint = f'/commits/{hash_of_commit}'
        response = self._request(endpoint)
        branches = self._get_complete_commit_branch_map()
        return {
            'hash': response['sha'],
            'author': response['commit']['author']['name'],
            'message': response['commit']['message'],
            'date': format_date_to_int(response['commit']['author']['date'],
                                       GITHUB_TIME_FORMAT),
            'branch': match_branch_to_commit(branches, response['sha'])
        } if response is not None else None

    def get_contributors(self):
        """
        Gets information about all contributors to repository
        in dict format with response body

        :return: dict
        :raise NotImplementedError
        :Example:
        [
             {
                 "name": "contributor name",
                 "number_of_commits": "number of commits",
                 "email": "contributor email",
                 "url": "contributor url"
             },
             ...
        ]
        """
        endpoint = '/contributors'
        response = self._request(endpoint)
        return list(map(lambda x: {
            'name': x['login'],
            'number_of_commits': x['contributions'],
            'email': x['login'],
            'url': x['url']
        }, response)) if response is not None else None


client = GithubRequestSenderV3('Lv-323python', 'learnRepo', '97f896b3656a56ab6f8c647d6c63ee53279ff1e1')
print(client.get_repo())