= Teamscale Command Line Interface =

The Teamscale command line interface is used to enable integration into text editors such as VIM, Emacs or Sublime, by providing findings in a standard error format that can be interpreted like compile time errors. 

== Setup ==
Clone this repository and copy the ```.teamscale-cli.config``` to your user directory:

```cp .teamscale-cli.config ~```

Now edit it and insert all the necessary data.

Next put the teamscale-cli shell script anywhere that is on your local $PATH, so that it can easily be executed.

In your IDE you can run this as a compile command, but be sure to provide the absolute path to the file in the current editor as the first argument: 

```teamscale-cli /home/user/project/src/foo/bar.c```

This should give you output similar to:
```
AssumptionViolatedException.java:30:0: error: Avoid leaving deprecated classes / methods / fields
AssumptionViolatedException.java:21:0: error: Avoid leaving deprecated classes / methods / fields
```

