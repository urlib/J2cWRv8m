@echo off
%~d0
cd %~dp0
cd ../
set panel_path=%cd%
echo %panel_path%

if "%1%" == "start" (
	goto panel_start
) else if "%1%" == "stop" (
	goto panel_stop
) else if "%1%" == "restart" (
	goto panel_restart
) else if "%1%" == "reload" (
	goto panel_reload
) else if "%1%" == "status" (
	goto panel_status
) else if "%1%" == "logs" (
	goto panel_logs
) else if "%1%" == "default" (
	goto panel_default
) else if "%1%" == "open" (
	goto panel_open
) else if "%1%" == "close" (
	goto panel_close
) else (
	python tools.py cli
)
goto panel_end
cmd /c dir


:panel_close
echo True>%panel_path%\data\close.pl
goto panel_end


:panel_open
set close_path=%panel_path%\data\close.pl
del %close_path%
goto panel_end

:panel_start
net start btTask
net start btPanel
goto panel_end

:panel_stop
net stop btTask
net stop btPanel
goto panel_end

:panel_reload
for /f "skip=3 tokens=4" %%i in ('sc query btPanel') do set "zt=%%i" &goto :next
:next
if /i "%zt%"=="RUNNING" (
    net stop btPanel
    net start btPanel
) else (
    net start btPanel
)
goto panel_end

:panel_restart
for /f "skip=3 tokens=4" %%i in ('sc query btTask') do set "zt=%%i" &goto :next
:next
if /i "%zt%"=="RUNNING" (
    net stop btTask
    net start btTask
) else (
    net start btTask
)

for /f "skip=3 tokens=4" %%i in ('sc query btPanel') do set "zt=%%i" &goto :next
:next
if /i "%zt%"=="RUNNING" (
    net stop btPanel
    net start btPanel
) else (
    net start btPanel
)
goto panel_end

:panel_status
goto panel_end

:panel_default
echo %panel_path%
set /p port=<%panel_path%\data\port.pl
set /p password=<%panel_path%\data\default.pl

echo.
echo ==================================================================
echo BT-Panel default info!
echo ==================================================================

for /f "tokens=4" %%a in ('route print^|findstr 0.0.0.0.*0.0.0.0') do (
 set IP=%%a
)
echo 宝塔面板地址： http://%IP%:%port%
python tools.py username
echo password：%password%
echo.
echo PS:如果面板无法访问
echo 请在安全组放行以下端口(8888,3389,888,80,443,20,21)
echo ==================================================================
echo.
goto panel_end


:panel_logs
tail %panel_path%\logs\error.log 

:panel_end

