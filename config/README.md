# Configuration of precommit analysis.

In order to be able to perform precommit analysis, you need to put the config file `.teamscale-precommit.config`
into the root of the repository you want to analyze.
Then, change the configuration in that file (e.g. url to Teamscale, project id etc.) to match your setting.

# Configuration as build step in editors like Sublime or VS Code

The precommit client will print the fetched findings to `stdout` in a format similar to gcc findings:

`Path to file:line number:Column: (warning|error): Message`

This allows you to use the highlighting capabilities of your editors to mark the findings inline.

For your convenience, this folder contains example configurations for builds in the following editors:

- Sublime
- VS Code
