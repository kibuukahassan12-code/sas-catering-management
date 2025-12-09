@ECHO OFF
SET DIR=%~dp0
SET CLASSPATH=%DIR%gradle\wrapper\gradle-wrapper.jar

REM Find Java
if defined JAVA_HOME (
    SET "JAVA_EXE=C:\Program Files\Java\jdk-17\bin\java.exe"
) else (
    SET "JAVA_EXE=C:\Program Files\Java\jdk-17\bin\java.exe"
)

"%JAVA_EXE%" -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
IF %ERRORLEVEL% NEQ 0 EXIT /B %ERRORLEVEL%
