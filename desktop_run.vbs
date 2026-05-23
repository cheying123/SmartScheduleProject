' SmartSchedule 桌面版启动脚本
' 双击此文件即可启动桌面应用（无控制台窗口）
' 窗口关闭后，服务会自动退出

Dim shell, fso, projectDir, pythonw, scriptPath
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = fso.BuildPath(projectDir, ".venv\Scripts\pythonw.exe")
scriptPath = fso.BuildPath(projectDir, "desktop_app.py")

If Not fso.FileExists(pythonw) Then
    MsgBox "未找到 Python 运行环境，请确认虚拟环境已创建。" & vbCrLf & pythonw, vbCritical, "SmartSchedule 启动失败"
    WScript.Quit
End If

' 静默启动（0 = 不显示窗口）
shell.Run """" & pythonw & """ """ & scriptPath & """", 0, False
