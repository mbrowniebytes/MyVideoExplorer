for /f "tokens=2,3,4,5,6 usebackq delims=:/ " %%a in ('%date% %time%') do echo %%c-%%a%%b-%%d%%e