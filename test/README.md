# Documentation Test Folder

This folder contains the files needed for running tests the ESP-IDF documentation building system.

Tests are divided into three categories: build tests, unit tests and integration tests:

## Build Tests
These tests only check that we are able to build docs without warnings for different configs.

Tests can be run from `build_tests/build_all.sh`

## Unit Tests

The Sphinx IDF extensions are unit-tested in [test_sphinx_idf_extensions.py](unit_tests/test_esp_extensions.py)

The Wokwi diagram and CI synchronization tools are unit-tested in [test_wokwi_tool.py](unit_tests/test_wokwi_tool.py)

## Integration Tests
Due to the thight integration with Sphinx some functionality is difficult to test with simple unit tests.

 To check that the output from the Sphinx build process is as expected [test_docs.py](test_docs.py) builds a test subset of the documentation, found in the [en](en/) folder. The HTML output is then checked to see that it contains the expected content.

# Running Tests

## Running with pytest (recommended)

Install development dependencies:
```bash
pip install -e ".[dev]"
# or
pip install -r requirements-dev.txt
```

Run all unit tests:
```bash
pytest test/unit_tests/ -v
```

Run specific test file:
```bash
pytest test/unit_tests/test_wokwi_tool.py -v
```

Run with coverage report:
```bash
pytest test/unit_tests/test_wokwi_tool.py -v --cov=esp_docs.generic_extensions.docs_embed.tool.wokwi_tool --cov-report=term-missing
```

## Running individual test files

Both [test_esp_extensions.py](unit_tests/test_esp_extensions.py) and [test_docs.py](unit_tests/test_docs.py) are run as part of the CI pipeline.

It's also possible to run the tests locally by running the following commands:

* `python test/unit_tests/test_esp_extensions.py`
* `python test/unit_tests/test_docs.py`
* `python test/unit_tests/test_wokwi_tool.py`

Note that [test_docs.py](unit_tests/test_docs.py) tries to build a test subset of the documentation, and thus requires your environment to be set up for building documents. See [Documenting Code](https://docs.espressif.com/projects/esp-idf/en/latest/contribute/documenting-code.html) for instructions on how to set up the `build_docs` environment.