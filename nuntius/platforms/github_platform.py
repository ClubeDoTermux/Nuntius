class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from github import Github
            self._client = Github(self.token)
        return self._client

    def list_repos(self, limit: int = 10):
        return [r.full_name for r in self.client.get_user().get_repos()[:limit]]

    def create_issue(self, repo: str, title: str, body: str = ""):
        r = self.client.get_repo(repo)
        issue = r.create_issue(title=title, body=body)
        return issue.html_url

    def list_issues(self, repo: str, state: str = "open"):
        r = self.client.get_repo(repo)
        return [f"#{i.number} {i.title}" for i in r.get_issues(state=state)[:10]]

    def get_repo_info(self, repo: str):
        r = self.client.get_repo(repo)
        return {
            "name": r.full_name,
            "desc": r.description,
            "stars": r.stargazers_count,
            "forks": r.forks_count,
            "language": r.language,
        }
