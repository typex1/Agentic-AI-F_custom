# Model Permissions Test Summary

**Date:** 2026-07-02  
**Region:** us-east-1  
**Model:** amazon.nova-lite-v1:0  
**IAM Role:** LabStack-e857ee53-58b2-4cfa-968e-4d-IdeInstanceRole-s1btKy6uI2jo  

## Results

| # | Action | Service | Status |
|---|--------|---------|--------|
| 1 | `Converse` | bedrock-runtime | ✓ Allowed |
| 2 | `ConverseStream` | bedrock-runtime | ✓ Allowed |
| 3 | `InvokeModel` | bedrock-runtime | ✓ Allowed |
| 4 | `InvokeModelWithResponseStream` | bedrock-runtime | ✓ Allowed |
| 5 | `ListFoundationModels` | bedrock | ✗ Denied |
| 6 | `GetFoundationModel` | bedrock | ✗ Denied |

## Conclusion

- All **runtime** actions (`bedrock-runtime:*`) are permitted. This covers both the Converse API (used by Strands Agents) and the legacy InvokeModel API.
- All **control-plane** actions (`bedrock:*`) are denied. The role cannot list or describe foundation models.
- The Strands Agents framework only requires `bedrock-runtime:Converse` or `bedrock-runtime:ConverseStream`, so it functions correctly with these permissions.
