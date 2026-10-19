' Xinxin desktop entry (stop variant): close app windows and stop the local stack.
' Keep this file pure ASCII: Windows Script Host reads .vbs as ANSI.
Dim fso, sh, here
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
here = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = here
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & here & "\Xinxin-Desktop.ps1"" -Stop", 0, False
