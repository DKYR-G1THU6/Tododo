# Desktop Shortcut

This folder contains a PowerShell script to create a desktop shortcut for the Tododo app.

Files:
- `scripts/create_shortcut.ps1` — PowerShell script that creates a `.lnk` on your Desktop.

How to use:
1. Open PowerShell (no admin required).
2. Navigate to the project folder:

```powershell
cd D:\Xina_App\Tododo\scripts
```

3. Run the script (default values point to Python 3.13 and `main.py`):

```powershell
.\create_shortcut.ps1
```

4. To specify a custom icon (full path to an `.ico` file):

```powershell
.\create_shortcut.ps1 -IconLocation "D:\Xina_App\Tododo\resources\tododo.ico"
```

Notes:
- If you change Python executable location, pass `-TargetPath` with the path to `python.exe`.
- Shortcut name can be changed with `-ShortcutName` (e.g., `Tododo App.lnk`).
- The icon is optional — you can replace the `.ico` later by editing the shortcut properties in Windows.

Which file to change if you want to modify the icon later:
- Edit the `.ico` path when calling the script, or right-click the created shortcut on Desktop → Properties → Change Icon.

