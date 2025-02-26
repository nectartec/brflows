import sempy.fabric as fabric
# Get the list of all workspacesworkspaces = fabric.list_workspaces()
# Filter the workspace by name and get the 
workspaces = fabric.list_workspaces()
workspace_name = "your_workspace_name"
workspace_row = workspaces[workspaces['Name'] == workspace_name]
workspace_id = workspace_row['Id'].values[0]
print(f"The workspace ID for {workspace_name} is {workspace_id}")