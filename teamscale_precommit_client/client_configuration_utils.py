from teamscale_client.teamscale_client_config import TeamscaleClientConfig


def get_teamscale_client_configuration(config_file):
    """Gets a Teamscale client configuration from the provided config file or a config file in the user's home dir
    or both combined. This allows users to separate their credentials (e.g. in their home dir) from the project specific
    configurations (e.g. in the repository roots).
    """
    local_teamscale_config = None
    teamscale_config_in_home_dir = None
    try:
        local_teamscale_config = TeamscaleClientConfig.from_config_file(config_file)
    except RuntimeError:
        # Error handling below, as either of the configs (or both combined) might be ok.
        pass

    try:
        teamscale_config_in_home_dir = TeamscaleClientConfig.from_config_file_in_home_dir()
    except RuntimeError:
        # Error handling below, as either of the configs (or both combined) might be ok.
        pass

    if local_teamscale_config:
        if not teamscale_config_in_home_dir:
            _require_sufficient_configuration(local_teamscale_config)
            return local_teamscale_config
        else:
            # Use config from home dir and overwrite with values from the local config.
            # This allows users to combine two different config files as stated above.
            teamscale_config_in_home_dir.overwrite_with(local_teamscale_config)
            _require_sufficient_configuration(teamscale_config_in_home_dir)
            return teamscale_config_in_home_dir
    else:
        if not teamscale_config_in_home_dir:
            raise RuntimeError('No valid configuration found.')
        else:
            _require_sufficient_configuration(teamscale_config_in_home_dir)
            return teamscale_config_in_home_dir


def _require_sufficient_configuration(configuration):
    """Ensures the provided configuration is sufficient for precommit analysis."""
    if not configuration.is_sufficient(require_project_id=True):
        raise RuntimeError('Not all necessary parameters specified in configuration file %s' %
                           configuration.config_file)
