import os
import sys


root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root)
os.chdir(root)


import shutil
import subprocess

def check_update():
    # 1. Prefer system git CLI if available (faster, reliable, no binary/C-extension dependencies)
    git_bin = shutil.which("git")
    if git_bin:
        try:
            res_inside = subprocess.run(
                [git_bin, "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                check=False
            )
            if res_inside.returncode == 0 and res_inside.stdout.strip() == "true":
                subprocess.run([git_bin, "fetch", "origin"], capture_output=True, text=True, check=False)
                pull_res = subprocess.run(
                    [git_bin, "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if pull_res.returncode == 0:
                    out = pull_res.stdout.strip()
                    if "Already up to date" in out or "Already up-to-date" in out:
                        print("Already up-to-date")
                    else:
                        print(f"Update succeeded: {out}")
                    return
                else:
                    msg = pull_res.stderr.strip() or pull_res.stdout.strip()
                    print(f"[Update note] Fast-forward not possible ({msg}). Keeping current local version.")
                    return
        except Exception as e:
            print(f"[Update] Git CLI check failed: {e}")

    # 2. Fallback to pygit2 if installed
    try:
        import pygit2
        pygit2.option(pygit2.GIT_OPT_SET_OWNER_VALIDATION, 0)

        repo = pygit2.Repository(os.path.abspath(os.path.dirname(__file__)))
        branch_name = repo.head.shorthand

        remote_name = 'origin'
        remote = repo.remotes[remote_name]
        remote.fetch()

        local_branch_ref = f'refs/heads/{branch_name}'
        local_branch = repo.lookup_reference(local_branch_ref)

        remote_reference = f'refs/remotes/{remote_name}/{branch_name}'
        remote_commit = repo.revparse_single(remote_reference)

        merge_result, _ = repo.merge_analysis(remote_commit.id)

        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            print("Already up-to-date")
        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            local_branch.set_target(remote_commit.id)
            repo.head.set_target(remote_commit.id)
            repo.checkout_tree(repo.get(remote_commit.id))
            repo.reset(local_branch.target, pygit2.GIT_RESET_HARD)
            print("Fast-forward merge succeeded.")
        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
            print("[Update] Local modifications detected. Keeping local changes.")
        return
    except Exception as e:
        # Graceful notice if pygit2 is not installed and git was not available
        print(f"[Update] Skipped automatic repository update ({e}). Continuing to launch Fooocus...")


check_update()
from launch import *
