# Azure OpenAI Migration Guide

This document describes the changes made to migrate from OpenAI API to Azure OpenAI.

## Overview

The application now supports **Azure OpenAI** as an LLM provider in addition to the existing OpenAI, Google Gemini, and Anthropic Claude providers.

## Changes Made

### 1. Dependencies
- **Added**: `openai>=1.0.0` to `requirements.txt`
  - This package is required for Azure OpenAI integration with LangChain

### 2. Configuration (`src/utils/config.py`)
Added new Azure OpenAI configuration fields:
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI resource endpoint
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: The name of your deployed model
- `AZURE_OPENAI_API_VERSION`: API version (default: `2024-02-15-preview`)
- `AZURE_OPENAI_TEMPERATURE`: Temperature setting (default: 0.7)
- `AZURE_OPENAI_MAX_TOKENS`: Maximum tokens (default: 2000)

Updated `DEFAULT_LLM_PROVIDER` to support `"azure-openai"` option.

### 3. LLM Service (`src/services/llm_service.py`)
- **Imported**: `AzureChatOpenAI` from `langchain_openai`
- **Added**: Support for `"azure-openai"` provider in `_get_model()` method
- **Updated**: Documentation to reflect Azure OpenAI support

### 4. Health Check (`src/api/health.py`)
- Added Azure OpenAI to the `llm_providers` check in `/health/info` endpoint
- Added `default_llm_provider` to system info response

### 5. Environment Files
- **`.env`**: Added Azure OpenAI configuration with placeholders
- **`.env.conf.template`**: Added Azure OpenAI template configuration
- **Updated**: `DEFAULT_LLM_PROVIDER` to `azure-openai`

## How to Use Azure OpenAI

### Step 1: Get Azure OpenAI Credentials

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to **Keys and Endpoint**
4. Copy:
   - **Endpoint** (e.g., `https://your-resource-name.openai.azure.com/`)
   - **Key 1** or **Key 2**

### Step 2: Deploy a Model

1. In Azure OpenAI Studio, go to **Deployments**
2. Create a new deployment (e.g., `gpt-4`, `gpt-35-turbo`)
3. Note the **deployment name**

### Step 3: Update Environment Variables

Edit your `.env` file:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_TOKENS=2000

# Set Azure OpenAI as default provider
DEFAULT_LLM_PROVIDER=azure-openai
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test the Configuration

Run the application and check the health endpoint:

```bash
# Start the application
python run.py

# Check system info (in another terminal)
curl http://localhost:8000/api/v1/health/info
```

You should see:
```json
{
  "llm_providers": {
    "azure-openai": true,
    ...
  },
  "default_llm_provider": "azure-openai"
}
```

## API Version Compatibility

The default API version is `2024-02-15-preview`. Other supported versions include:
- `2024-02-15-preview`
- `2023-12-01-preview`
- `2023-05-15`

Refer to [Azure OpenAI API versions](https://learn.microsoft.com/azure/ai-services/openai/reference) for the latest versions.

## Provider Options

The application now supports the following LLM providers:

| Provider | Value in `.env` |
|----------|-----------------|
| OpenAI | `openai` |
| Azure OpenAI | `azure-openai` |
| Google Gemini | `google` |
| Anthropic Claude | `anthropic` |

Set `DEFAULT_LLM_PROVIDER` to your preferred provider.

## Benefits of Azure OpenAI

1. **Enterprise Features**: VNet support, managed identity, private endpoints
2. **Compliance**: Data residency, compliance certifications
3. **Integration**: Native Azure ecosystem integration
4. **SLA**: Enterprise-grade SLA and support
5. **Content Safety**: Built-in content filtering

## Switching Between Providers

You can switch providers at runtime by:

1. **Environment variable**: Change `DEFAULT_LLM_PROVIDER` and restart the application
2. **Programmatically**: Pass the `provider` parameter when initializing `LLMService`:
   ```python
   from src.services import LLMService
   
   # Use Azure OpenAI
   llm = LLMService(provider="azure-openai")
   ```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check your API key is correct
2. **404 Not Found**: Verify deployment name matches your Azure deployment
3. **Invalid API Version**: Update `AZURE_OPENAI_API_VERSION` to a supported version
4. **Endpoint URL**: Ensure endpoint ends with `/` and includes `https://`

### Logs

Check application logs for detailed error messages:
```bash
# Set log level to DEBUG in .env
LOG_LEVEL=DEBUG
```

## Security Notes

⚠️ **Never commit your `.env` file with real credentials!**

- The `.env` file is in `.gitignore`
- Use `.env.conf.template` as a reference
- Rotate keys immediately if exposed
- Consider using Azure Key Vault for production

## Related Documentation

- [Azure OpenAI Service Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [LangChain Azure OpenAI Integration](https://python.langchain.com/docs/integrations/chat/azure_chat_openai)
- [Azure OpenAI Quickstart](https://learn.microsoft.com/azure/ai-services/openai/quickstart)
