<#
Create a Windows desktop shortcut (.lnk) for the Tododo app.
Usage examples (PowerShell):

# Default (uses current Python executable and main.py path below)
PS> .\create_shortcut.ps1

# Specify a custom icon (full path to .ico)
PS> .\create_shortcut.ps1 -IconLocation "D:\Xina_App\Tododo\resources\tododo.ico"

# Shortcut name
PS> .\create_shortcut.ps1 -ShortcutName "Tododo App.lnk"
#>
param(
    [string]$TargetPath = "C:\\Users\\DARREN\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
    [string]$Arguments = "D:\\Xina_App\\Tododo\\main.py",
    [string]$WorkingDirectory = "D:\\Xina_App\\Tododo",
    [string]$ShortcutName = "Tododo.lnk",
    [string]$IconLocation = ""
)

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop $ShortcutName

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $TargetPath
$shortcut.Arguments = $Arguments
$shortcut.WorkingDirectory = $WorkingDirectory
if ($IconLocation -ne "") {
    $shortcut.IconLocation = $IconLocation
}
$shortcut.Save()
Write-Host "Created shortcut: $shortcutPath"
