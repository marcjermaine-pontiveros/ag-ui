# Agent User Interaction Protocol Documentation

The Python SDK for the [Agent User Interaction Protocol](https://ag-ui.com).

For more information visit the [official documentation](https://docs.ag-ui.com/).

## Development Setup

To install the SDK for development, clone the repository and then install it in editable mode using pip. This allows you to make changes to the SDK code and have them immediately reflected in your environment.

Navigate to the `python-sdk` directory:
```bash
cd path/to/ag-ui/python-sdk
```

Then, install the package in editable mode:
```bash
pip install -e .
```
This command installs the package from the current directory (`.`) in editable (`-e`) mode. Any changes you make to the Python files within the `ag_ui` directory will be available to other Python scripts that import this package without needing to reinstall.

Make sure you have [Poetry](https://python-poetry.org/docs/#installation) installed if you intend to manage dependencies or build the package.
