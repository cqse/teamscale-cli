# Teamscale Precommit Command Line Client

The Teamscale precommit command line interface allows you to integrate precommit analysis in editors or IDEs such as VS Code, Emacs or Sublime, by providing findings in a standard error format that can be interpreted like compile time errors.

## Setup

1. Install ```libgit2```: https://libgit2.org

2. Install this client via pip:
 ```bash
 $ pip install teamscale-cli
 ```

3. Copy the configuration file ```config/.teamscale-precommit.config``` to the root directory of the repository you want to analyze:
 Edit it and insert all the necessary data.

4. Use this script as compile or build command in your editor or IDE. See examples in the ```config``` folder for how to accomplish this.
 Provide a file or folder within your repository as input. The general invocation looks like this:

 ```bash
 $ python -c "from teamscale_precommit_client.precommit_client import run;run()" ANY_FILE_OR_FOLDER_IN_YOUR_REPO
 ```

5. The behavior of the client can be tweaked with several arguments. Run the client without any arguments to get the usage.

