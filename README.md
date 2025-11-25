# pyenvalid

Beautiful validation errors for pydantic-settings.

## The Problem

When using `pydantic-settings` with required environment variables, missing or invalid values produce cryptic errors:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    port: int

settings = Settings()  # Crashes if DATABASE_URL not set
```

```python
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
database_url
  Field required [type=missing, input_value={}, input_type=dict]
api_key
  Field required [type=missing, input_value={}, input_type=dict]
```

This error is confusing because:

- It doesn't mention environment variables in a friendly way
- The `input_value={}` is misleading (it's not a dict, it's your environment)
- Hard to quickly see which variables need to be set

### Type errors

If you have fields in your config that don't have a default value, you get a type error:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    port: int

settings = Settings() # expects parameters to be passed in
```

This is not very good DX either.

## The Solution

`pyenvalid` wraps validation and provides clear, actionable error messages:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ CONFIGURATION ERROR                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ The following environment variables have issues:                         │
│                                                                          │
│   ✗ DATABASE_URL (missing)                                               │
│   ✗ API_KEY (missing)                                                    │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ Set these in your .env file or environment                               │
└──────────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install pyenvalid
```

Or with uv:

```bash
uv add pyenvalid
```

## Usage

```python
from pydantic_settings import BaseSettings
from pyenvalid import validate_settings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    port: int = 8080

settings = validate_settings(Settings)
```

That's it. If `DATABASE_URL` or `API_KEY` are missing, you get the nice error box instead of pydantic's raw error.

### With .env file

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pyenvalid import validate_settings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    secret_key: str
    database_url: str

settings = validate_settings(Settings)
```

### Custom error messages

```python
from pyenvalid import ConfigurationError, validate_settings

try:
    settings = validate_settings(Settings)
except ConfigurationError as e:
    raise ConfigurationError(
        e.errors,
        title="DATABASE ERROR",
        hint="Check your .env.local file",
    ) from None
```

### Handling errors programmatically

```python
from pyenvalid import ConfigurationError, validate_settings

try:
    settings = validate_settings(Settings)
except ConfigurationError as e:
    print(e.errors)  # [('database_url', 'missing'), ('api_key', 'missing')]
    print(e.missing_fields)  # ['database_url', 'api_key']
```

## Error Types

The error type shown is the raw pydantic error type:

| Error | Meaning |
|-------|---------|
| `missing` | Required field not set |
| `int_parsing` | Value can't be parsed as integer |
| `bool_parsing` | Value can't be parsed as boolean |
| `literal_error` | Value not in allowed options |
| `url_parsing` | Invalid URL format |

## License

[MIT](LICENSE)
