import os
import gitlab
import subprocess
import time
from datetime import datetime

# === CONFIGURATION ===
today = datetime.now().strftime('%Y%m%d')
GITLAB_URL = 'https://abc.gitlab.com' # Replace with your GitLab instance URL
PRIVATE_TOKEN = 'impersonation_tokens' # Create a personal access token with API + read_repository scopes
DEST_DIR = f'./gitlab-fullbackup-{today}' # Destination folder for backup
GIT_CLONE_CMD = ['git', 'clone', '--mirror']

# === CONNECT TO GITLAB ===
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def clone_project(project, group_path):
    local_group_path = os.path.join(DEST_DIR, group_path)
    ensure_dir(local_group_path)
    repo_path = os.path.join(local_group_path, f"{project.name}")

    if "simulations" in repo_path:
        print(f"[SKIP] {repo_path} skipped.")
        return

    if os.path.exists(repo_path):
        print(f"[SKIP] {repo_path} already exists.")
        return

    print(f"[CLONE] {project.ssh_url_to_repo} -> {repo_path}")
    subprocess.run(GIT_CLONE_CMD + [project.ssh_url_to_repo, repo_path])
    time.sleep(2)

def process_group(group, parent_path=''):
    group_path = os.path.join(parent_path, group.path)
    
    # Clone all projects in this group
    for project in group.projects.list(all=True):
        project_detail = gl.projects.get(project.id)
        clone_project(project_detail, group_path)

    # Process subgroups recursively
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

