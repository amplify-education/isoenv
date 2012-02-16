Isoenv
------

This tool is designed to work in concert with a configuration management
toolchain. Its purpose is to allow for specific configuration from many
environments to be contained in the same source control repository, but
to only deploy the configuration for the specific environment to each environment
master configuration server.

Usage
=====

The repository can contain any number of ENVIRONMENT_SPECIFIC directories.
These directories should contain subdirectories for each environment.
When the repository is compiled for a specific environment, the contents of that
environments subdirectory in all ENVIRONMENT_SPECIFIC directories will
be used in the destination directory.

For example::

    bcfg2/
    |-- Bundles
    |   `-- server.xml
    `-- Properties
        `-- ENVIRONMENT_SPECIFIC
            |-- dev
            |   `-- dev_box.xml
            |-- prod
            |   `-- prod_box.xml
            `-- stg
                `-- stg_box.xml

compiled for dev looks like::

    bcfg2/
    |-- Bundles
    |   `-- server.xml
    `-- Properties
        `-- dev_box.xml

and compiled form prod looks like::
    
    bcfg2/
    |-- Bundles
    |   `-- server.xml
    `-- Properties
        `-- prod_box.xml

If a file exists in both an ENVIRONMENT_SPECIFIC directory, and outside of one,
then the one in the ENVIRONMENT_SPECIFIC directory overrides the non-specific file.

Isoenv also includes a facility to allow combining multiple repositories (for
instance, if one of the repositories has higher security requirements than another).
In that case, the sources listed later override the earlier sources.

Testing
=======

Isoenv also includes the in_env utility, which can be used to test commands inside a
compiled environment. The arguments are similar to those of the main isoenv command,
but once the directory is compiled, the command is executed, and then the directory
is removed.

When the command is run, the environment variable $COMPILED_DIR is set and points to
the directory the repository was compiled into. Also, the working directory for the
executed command is set to the compiled directory.
