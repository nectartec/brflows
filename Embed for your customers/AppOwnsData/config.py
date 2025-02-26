# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

class BaseConfig(object):

    # Can be set to 'MasterUser' or 'ServicePrincipal'
    AUTHENTICATION_MODE = 'ServicePrincipal'

    # Workspace Id in which the report is present
    WORKSPACE_ID = '017CDE99-646A-4FD2-8C54-17E2E33A8BC9'
    
    # Report Id for which Embed token needs to be generated
    REPORT_ID = '1a8338f0-8a78-4d27-be71-82a121a784cc'
    
    # Id of the Azure tenant in which AAD app and Power BI report is hosted. Required only for ServicePrincipal authentication mode.
    TENANT_ID = '71029506-45c7-4577-b71e-19beb180170f'
    
    # Client Id (Application Id) of the AAD app
    CLIENT_ID = 'ec07d040-09ee-48e6-8604-3c23787e27cf'
    
    # Client Secret (App Secret) of the AAD app. Required only for ServicePrincipal authentication mode.
    CLIENT_SECRET = 'bqa8Q~iTCuy1jqrTvvFEsdFhvSEFpxACCnkJWdrW'
    
    # Scope Base of AAD app. Use the below configuration to use all the permissions provided in the AAD app through Azure portal.
    SCOPE_BASE = ['https://analysis.windows.net/powerbi/api/.default']
    
    # URL used for initiating authorization request
    AUTHORITY_URL = 'https://login.microsoftonline.com/organizations'
    
    # Master user email address. Required only for MasterUser authentication mode.
    POWER_BI_USER = ''
    
    # Master user email password. Required only for MasterUser authentication mode.
    POWER_BI_PASS = ''