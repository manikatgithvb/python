import os
import gitlab
import subprocess
from datetime import datetime, timedelta, timezone

# === CONFIGURATION ===
GITLAB_URL = 'https://abc.gitlab.com' # Replace with your GitLab instance URL
PRIVATE_TOKEN = 'impersonation_tokens' # GitLab personal access token
DEST_DIR = './latest' # Destination backup folder
USE_MIRROR = True # Set to False if you want working tree clone

# === CONNECT TO GITLAB ===
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)
today = datetime.now()
yesterday = today - timedelta(days=1)
cutoff = yesterday.strftime('%Y%m%d')
since1 = yesterday.strftime('%Y-%m-%d')

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def run_git_command(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {' '.join(cmd)}\n{result.stderr}")
    return result

def clone_or_update_project(project, group_path):
    local_group_path = os.path.join(DEST_DIR, group_path)
    ensure_dir(local_group_path)

    repo_name = f"{project.name}.git" if USE_MIRROR else project.name
    repo_path = os.path.join(local_group_path, repo_name)

    if os.path.exists(repo_path):
        print(f"[UPDATE] {repo_path}")
        cmd = ['git', 'remote', 'update'] if USE_MIRROR else ['git', 'fetch', '--all', '--prune']
        run_git_command(cmd, cwd=repo_path)
        if not USE_MIRROR:
          cmd = ['git', 'pull']
          run_git_command(cmd, cwd=repo_path)
    else:
        print(f"[CLONE] {project.ssh_url_to_repo} -> {repo_path}")
        cmd = ['git', 'clone', '--mirror', project.ssh_url_to_repo, repo_path] if USE_MIRROR else ['git', 'clone', project.ssh_url_to_repo, repo_path]
        run_git_command(cmd)

def project_has_recent_commit(project1):
    try:
        commits = project1.commits.list(since=f'{since1}T00:00:00Z', get_all=False)
        if not commits:
            print (f"[NO COMMIT] {project1.path_with_namespace}")
            return False

        latest_commit = commits[0]
        commit_time = datetime.strptime(latest_commit.created_at, '%Y-%m-%dT%H:%M:%S.%f%z')
        print(f"[LAST COMMIT] {project1.path_with_namespace} - {commit_time}")
        last_activity = commit_time.strftime('%Y%m%d')
        return last_activity >= cutoff
    except Exception as e:
        print(f"[ERROR] Could not get commit info for {project1.path_with_namespace}: {e}")
        return False

def process_group(group, parent_path=''):
    group_path = os.path.join(parent_path, group.path)

    for project in group.projects.list(all=True):
        project_detail = gl.projects.get(project.id)

        if project_detail:
            if project_has_recent_commit(project_detail):
                print(f"[RECENT] {project_detail.path_with_namespace}")
                clone_or_update_project(project_detail, group_path)
            else:
                print(f"[SKIP] {project_detail.path_with_namespace}")

    for subgroup in group.subgroups.list(all=True):
        subgroup_detail = gl.groups.get(subgroup.id)
        process_group(subgroup_detail, group_path)

def main():
    root_groups = gl.groups.list(top_level_only=True, all=True)
    for group in root_groups:
        group_detail = gl.groups.get(group.id)
        process_group(group_detail)

if __name__ == '__main__':
    main()

