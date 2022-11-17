import os
import shutil
import sys

import yaml

# https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsshell
SHEBANGS = {
    "null": "#!/bin/bash -e",
    "bash": "#!/bin/bash -eo pipefail",
    "sh": "#!/bin/sh -e",
    "python": "#!/usr/bin/env python",
}

EXTENSIONS = {
    "null": "bash",
    "bash": "bash",
    "sh": "sh",
    "python": "py",
}


input_path = sys.argv[1]
output_path = sys.argv[2]

shutil.rmtree(output_path, ignore_errors=True)

output = open(os.environ["GITHUB_OUTPUT"], "w")

output.write("files<<EOF\n")

for workflow_filename in os.listdir(input_path):
    if not workflow_filename.endswith(".yml"):
        continue

    workflow_id = os.path.basename(workflow_filename).replace(".yml", "")

    with open(f"{input_path}/{workflow_filename}", "r") as f:
        workflow = yaml.safe_load(f)

    if not workflow:
        continue

    for job_id, job in workflow.get("jobs", []).items():
        job_dirname = f"{output_path}/{workflow_id}/{job_id}"
        os.makedirs(job_dirname, exist_ok=True)

        for idx, step in enumerate(job.get("steps", [])):
            if "run" not in step:
                continue

            shell = step.get("shell", "null")
            if shell not in SHEBANGS:
                continue

            shebang = SHEBANGS[shell]
            extension = EXTENSIONS[shell]
            step_id = step.get("id", f"__run_{idx}")
            name = step.get("name")
            script = step.get("run")

            filename = f"{job_dirname}/{step_id}.{extension}"

            output.write(filename + "\n")
            with open(filename, "w") as f:
                f.write(f"{shebang}\n")
                if name:
                    f.write(f"# name: {name}\n")
                f.write("\n")
                f.write(script)
                if not script.endswith("\n"):
                    f.write("\n")

output.write("EOF\n")
