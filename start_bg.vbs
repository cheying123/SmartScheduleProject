' SmartSchedule 后台启动脚本
' 双击此文件即可在后台静默启动服务
' 浏览器访问 http://localhost:5000

Dim shell, fso, projectDir, pythonw, backendDir
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录（项目根目录）
projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = fso.BuildPath(projectDir, ".venv\Scripts\pythonw.exe")
backendDir = fso.BuildPath(projectDir, "backend")

' 检查 pythonw.exe 是否存在
If Not fso.FileExists(pythonw) Then
    MsgBox "未找到 pythonw.exe，请确认虚拟环境已创建。" & vbCrLf & pythonw, vbCritical, "SmartSchedule 启动失败"
    WScript.Quit
End If

' 以后台方式启动（0 = 不显示窗口）
shell.Run """" & pythonw & """ app.py", 0, False

' 等待服务启动后打开浏览器
WScript.Sleep 3000
shell.Run "http://localhost:5000"
