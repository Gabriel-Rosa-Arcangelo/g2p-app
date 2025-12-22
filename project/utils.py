import requests


def get_github_commits(repo_owner, repo_name, token, branch='main'):
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?sha={branch}"
    headers = {"Authorization": f"token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        commits = response.json()
        return commits
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub commits: {e}")
        return None


