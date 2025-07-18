# python - GitLab backup scripts.

The scripts were generated using chatGPT then edited a few lines manually. Using python-gitlab API, these scripts loop through all workgroup and projects. Use Admin level user's credentials.

# Description
gitlab-overnight-changes.py - Run everyday from CRON to take updates done in last 24 hours.
gitlab-changes-monthly-backup.py - Run first day of every month. Will take backup of projects where changes made in last 30 days.
gitlab-mirror.py - Run manually to take mirror backup of all projects.

# Dependencies
python-gitlab API
Ubuntu: $ sudo apt install python3-gitlab
