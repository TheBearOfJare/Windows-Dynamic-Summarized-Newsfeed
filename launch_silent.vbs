Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\darkp\Documents\Windows Dynamic Summarized Newsfeed"
WshShell.Run """C:\Users\darkp\AppData\Local\Microsoft\WindowsApps\python3.11.exe"" ""main.pyw""", 0, False
