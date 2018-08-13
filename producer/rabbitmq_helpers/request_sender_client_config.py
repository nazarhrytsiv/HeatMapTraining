"""
Contains configuration variables for RequestSenderClient
"""
HOST = 'heatmaptraining_rabbit_1'
PORT = 5672
RPC_QUEUE = 'request'
CALLBACK_QUEUE = 'response'
REQUEST_SENDER_CHOICES = {
    'bitbucket_request_sender': 'BitbucketRequestSender',
    'github_request_sender': 'GithubRequestSender',
    'gitlab_request_sender': 'GitlabRequestSender'
}