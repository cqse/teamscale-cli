# Teamscale Precommit Command Line Client [![Build Status](https://travis-ci.org/cqse/teamscale-cli.svg?branch=master)](https://travis-ci.org/cqse/teamscale-cli) [![PyPI version](https://badge.fury.io/py/teamscale-cli.svg)](https://badge.fury.io/py/teamscale-cli) [![Teamscale Project](https://img.shields.io/badge/teamscale-teamscale--cli-brightgreen.svg)](https://demo.teamscale.com/activity.html#/teamscale-cli)
The [Teamscale](https://teamscale.com) precommit command line interface allows you to integrate precommit analysis in editors or IDEs such as VS Code, Emacs or Sublime, by providing findings in a standard error format that can be interpreted like compile time errors.


## Installation

1. Install ```libgit2``` (https://libgit2.org) on all platforms except Windows
    - On macOS use `brew install libgit2`.
    - Not necessary on Windows as ```libgit2``` is already packaged with the ```pygit``` dependency.

2. Install this client via pip:
 ```bash
 $ pip install teamscale-cli
 ```

3. Copy the configuration file ```config/.teamscale-precommit.config``` to the root directory of the repository you want to analyze. Edit it and insert all the necessary data. You can find your personal access token by opening Teamscale and clicking on your Avatar in the top right corner.

4. Use this script as compile or build command in your editor or IDE. See below for more information and a couple of examples on how to accomplish this. Provide a file or folder within your repository as input. The general invocation looks like this:

 ```bash
 $ teamscale-cli ANY_FILE_OR_FOLDER_IN_YOUR_REPO
 ```

5. The behavior of the client can be tweaked with several arguments. Run the client with the ```-h``` argument to get the usage.

### Problems
- If python is not finding the name ConverterMapping try uninstalling the python-configparser package and install the configparser via pip/pip3

## How to perform precommit analysis

When invoked, the precommit analysis client uploads the current changes from your Git repository to the Teamscale server and project you provided in the settings. The client then waits until Teamscale has analyzed these changes, and comes back with findings.
The findings will be printed to `stdout` in a pretty standard format similar to gcc findings:

`Path to file:line number:Column: (warning|error): Message`

This allows you to use the highlighting capabilities of your editors to mark the findings inline or to jump to the findings from the precommit output. For your convenience, we've provided sample configurations for some editors and IDEs.

### Sublime

Add a new *Build System* under `Tools > Build System`. Locate `config/teamscale-precommit.sublime-build` in this repo. Copy and paste the snippet and modify the arguments to fit your needs.

### Xcode

Add a new *Build Phase* (`New Run Script Phase`) to your project. Enter the following command as shell script in that phase (see screenshot):

```bash
teamscale-cli ${SRCROOT} --fail-on-red-findings
```

![Configuring the Build Phase in Xcode](config/xcode_1.png)

As you're on a Mac, make sure to use the correct Python version in that snippet, which might be `python3`. The option `--fail-on-red-findings` will fail your Xcode build if new RED findings were found. You might decide to drop that flag. If you've done it right, Xcode will show all findings inlined as seen on the following screenshot:

![Teamscale Findings in Xcode](config/xcode_2.png)

### VS Code

Add a new task (`Terminal -> Configure Tasks`) and name it `Teamscale Precommit Analysis` or similar. VS Code will open a sample `tasks.json` for you to edit. Locate `config/teamscale-precommit-vscode-task.json` in this repo. Copy and paste the snippet and modify to your needs (e.g. `python` vs. `python3`).

### Vim

Locate `config/teamscale.vim` and put in into `~/.vim/compiler`. Modify to your needs (e.g. `python` vs. `python3`).
This should allow you to do `:compiler teamscale` and `:make %`. Then you should be able to use your usual workflow (e.g. `:cn`) to go through the findings.

### QTCreator
In order to use the precommit Analysis in QTCreator you need to add a new Kit (Teamscale does **not** have to be the default one)  
Go to `Projects` -> `Manage Kits...` -> `Kits` -> `Add`  

![New Teamscale Kit](config/qtcreator_1.png)

The only thing important here to configure is that the compiler is gcc as this will be used to parse the output of the precommit analysis.

Next you need to add the actual run config. Go to `Projects` -> `Teamscale` -> `Build` and remove all default `Build` and `Clean Steps` (there should be a small x when hovering over them)  
Then go to `Projects` -> `Teamscale` -> `Run`, and add a new `Run Configuration` (After doing so you can remove the default, as the Kit needs at least one). You can also rename the run config to, for example,
**Precommit**

![Precommit](config/qtcreator_2.png)

Then configure it as follows:  
```
Executable: python3 (or python)  
Command line arguments: -c "from teamscale_precommit_client.precommit_client import run;run()" --log-to-stderr %{CurrentProject:Path}
```

Note that the flag **--log-to-stderr** is mandatory, otherwise QTCreator will not recognize the findings.  
The environment variable `%{CurrentProject:Path}` can be changed to `%{CurrentDocument:FilePath}` for example, which will make the precommit analysis only fetch findings for the currently opened file.  
For other possible environment variables click on the little **A->B** button (Marked with a red box in the picture above).  
The last parameter has to be either a folder or specific file for which the precommit analysis should be run, so here you can add as many different precommit analyses configuration as you wish.  
If you want to see the different options of the precommit analysis itself, just run it with the `-h` flag.

## More details

### How does change detection work?

The client detects changes by querying your Git repository for its current status. The following change types will be considered:

- Modified files
- Renamed files
- Files added to the index
- Deleted files that were in the index

New files that are not in the index will be ignored.

### Which findings should be fetched?

By default, the precommit analysis client will fetch new findings in the changes you've made as well as findings that have existed in code you have modified. You can tweak this behavior using the following flags:

```
  --exclude-findings-in-changed-code
                        Determines whether to exclude findings in changed code
                        (default: False)
  --fetch-existing-findings
                        When this option is set, existing findings in the
                        specified file are fetched in addition to precommit
                        findings. (default: False)
  --fetch-existing-findings-in-changes
                        When this option is set, existing findings in all
                        changed files are fetched in addition to precommit
                        findings. (default: False)
  --fetch-all-findings
                        When this option is set, all existing findings in the
                        repo are fetched in addition to precommit findings.
                        (default: False)
```

Be cautious using these flags as there might be many findings in your code base.

### Other command line options

```
  --fail-on-red-findings
                        When this option is set, the precommit client will exit
                        with a non-zero return value whenever RED findings were
                        among the precommit findings. (default: False)
  --omit-links-to-findings
                        By default, each finding includes a link to the
                        corresponding finding in Teamscale. Setting this
                        option omits these links. (default: False)
  --verify
                        Path to different certificate file.  See requests' verify
                        parameter in http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
                        Other possible values: True, False (default: True)
  --path-prefix PATH_PREFIX
                        Path prefix on Teamscale as configured with "Prepend repository identifier" or "Path prefix transformation"
```

## Limits

The precommit analysis has some builtin limits, whose goal is to prevent denial of service of the Teamscale server:

- Files uploaded for precommit analysis must be less than 1 MB in size.
- At most 20 files can be uploaded for precommit analysis (can be changed on the server).
- Precommit analysis uploads might only be done once every 5 seconds per user (can be changed on the server).
