function Get-Existence {
	[CmdletBinding()]
	param(
		[string]$path,
		[boolean]$isfolder
	)

	$exists = $true
	if ($isfolder) {
		Write-Host "Checking for folder: $path"
		if (-Not (Test-Path -Path $path)) {
			$exists = $false
			Write-Host " Folder $path does not exist."
		}
	} Else {
		Write-Host "Checking for file: $path"
		if (-Not (Test-Path -Path $path -PathType Leaf)) {
			$exists = $false
			Write-Host " File $path does not exist."
		}
	}
	if ($exists) {
		Write-Host ' Done'
	} Else {
		Write-Host ' Asking your administrator for a complete installation package.'
		Write-Host ' Exiting...'
		exit
	}
}

function Find-Folder {
	[Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null
	[System.Windows.Forms.Application]::EnableVisualStyles()
	$browse = New-Object System.Windows.Forms.FolderBrowserDialog
	$browse.SelectedPath = "C:\"
    $browse.ShowNewFolderButton = $false
	$browse.Description = "Select a directory"
	
	$loop = $true
	while($loop)
	{
		if ($browse.ShowDialog() -eq "OK")
		{
			$loop = $false
		}
	}
	return $browse.SelectedPath
}


Write-Host 'Checking for installation-package integrity...'
$root_path = Resolve-Path -Path '..'
$installers_path = '.'
if ((Get-WmiObject win32_operatingsystem | Select-Object osarchitecture).osarchitecture -eq "64-bit")
{
	$anaconda_installer = Get-ChildItem -Path $installers_path -Name -File -Include *Anaconda*64*
}
else
{
    $anaconda_installer = Get-ChildItem -Path $installers_path -Name -File -Include *Anaconda* -Exclude *64*
} 
$requirements = "$installers_path\requirements.txt"
$requirements2 = "$installers_path\requirements2.txt"
$ui_path = Resolve-Path -Path "$root_path\UI"
$cmder_path = "$root_path\UI\cmder"
Get-Existence -path $installers_path -isfolder 1
Get-Existence -path "$installers_path\$anaconda_installer" -isfolder 0
Get-Existence -path $requirements -isfolder 0
Get-Existence -path $requirements2 -isfolder 0
Get-Existence -path "$root_path\core" -isfolder 1
Get-Existence -path "$root_path\data" -isfolder 1
Get-Existence -path "$root_path\depository" -isfolder 1
Get-Existence -path $ui_path -isfolder 1
Get-Existence -path $cmder_path -isfolder 1
# Get-Existence -path "$cmder_path\config\user_profile.cmd" -isfolder 0

$requirements = Resolve-Path -Path $requirements
$requirements2 = Resolve-Path -Path $requirements2

Clear-Host
Write-Host '************************************' -foreground yellow
Write-Host '**  ' -foreground yellow -nonewline
Write-Host 'Welcome to AUTOMATA' -foreground green -nonewline
Write-Host '  **' -foreground yellow
Write-Host '************************************' -foreground yellow
Write-Host ''
Write-Host 'This is a project for automation for everything, everybody.'
Write-Host 'Please make sure you are ' -nonewline
Write-Host 'CONNECTED' -foreground red -nonewline
Write-Host ' to internet during the installation.'
Write-Host ''
Write-Host 'Start installation? [y/n]' -nonewline
$ifcontinue = Read-Host
if ($ifcontinue -eq 'y') {
	Write-Host ''
	Write-Host 'Starting installation!'
	Write-Host ''
	Write-Host '************************************'
	Write-Host 'Step 1. Items below are going to be installed:'
	Write-Host ' 1. Anaconda'
	Write-Host ' 2. Autoit (optional)'
	Write-Host ' 3. required Python libraries'
	Read-Host -Prompt 'Press any key to start...'

	Write-Host 'Step 1.1. Installing Anaconda...'
	Write-Host ' Checking for Anaconda installation...'
	if (Get-Command conda -errorAction SilentlyContinue)
	{
		$anaconda_path = $env:path.split(';') | Select-String -Pattern 'anaconda' | Select-Object -First 1
		Write-Host ' Anaconda is already installed. Do you want to reinstall it? [y/n]'
        $reinstall = Read-Host
        if ($reinstall -eq 'y') {
			Write-Host '  Removing current installation of Anaconda...'
			$anaconda_uninstaller = Get-ChildItem -Path $anaconda_path -Name -File -Include *uninstall*Anaconda*
			$uninstall_anaconda = & Start-Process "$anaconda_path\$anaconda_uninstaller" -NoNewWindow -Wait -PassThru
			if ($uninstall_anaconda.ExitCode -eq 0) {
			    Write-Host '  Successfully removed Anaconda.'
            } Else {
                Write-Host '  Failed to removed Anaconda. Please remove it manually.'
			}
		}
	} else {
		Write-Host ' Did not find Anaconda.'
		Write-Host '  If you have already installed Anaconda, input "y" to select its folder;'
		Write-Host '  or input "n" to start installation: [y/n]'
		$installed = Read-Host
		if ($installed -eq 'y') {
			$anaconda_path = Find-Folder
		} else {
			Write-Host ' Starting installation...'
			Write-Host ' Select a folder for installation: ' -foreground Red
			$target_folder = Find-Folder
			$anaconda_path = "$target_folder\Anaconda"
			md $anaconda_path
			Write-Host " Path for installation created! Please select path for installation: $anaconda_path"
			$installation_process = & Start-Process "$installers_path\$anaconda_installer" -NoNewWindow -Wait -PassThru
			if ($installation_process.ExitCode -eq 0) {
				Write-Host '  Anaconda installation completed.'
			} Else {
				Write-Host '  Installation failed'
				Write-Host '  Consulting your administrator for a solution.'
				Write-Host 'Exiting...'
				exit
			}
		}
	}

	Write-Host ''
	Write-Host 'Step 1.2. Installing Autoit...'
	Write-Host ' This installation is optional, do you want to install it? [y/n]'
	$install_autoit = Read-Host
	if ($install_autoit -eq 'y') {
		Write-Host ' Starting installation...'
		$autoit_installer = Get-ChildItem -Path $installers_path -Name -File -Include *autoit*
		$installation_process2 = & Start-Process "$installers_path\$autoit_installer" -NoNewWindow -Wait -PassThru
		if ($installation_process2.ExitCode -eq 0) {
			Write-Host '  Autoit installation completed.'
		} Else {
			Write-Host '  Installation failed'
			Write-Host '  Consulting your administrator for a solution.'
			Read-Host -Prompt 'Press any key to continue to next step...'
		}
	}

	Write-Host ''
	Write-Host 'Step 1.3. Installing Python libraries...'
	$installation_bat_file = @"
@echo off
cd $anaconda_path\Scripts
call .\activate.bat
call conda create --name AUTOMATA --file $requirements -y
cd $anaconda_path\envs\AUTOMATA\Scripts
call activate AUTOMATA
call pip install -r $requirements2
python -c "import numpy, pandas, scipy, requests, selenium, browser_cookie3, gspread, oauth2client, pyautogui, win32com"
"@
	Out-File -FilePath "$installers_path\install_python_libraries.bat" -InputObject $installation_bat_file -Encoding default
	$installation_process3 = & Start-Process cmd -Argument "/c .\installers\install_python_libraries.bat" -Wait -PassThru
	if ($installation_process3.ExitCode -eq 0) {
		Write-Host ' Required Python libraries successfully installed'
	} Else {
		Write-Host ' Installation of python libraries failed'
		Write-Host ' Consulting your administrator for a solution.'
		Read-Host -Prompt 'Press any key to continue to next step...'
	}

	Write-Host ''
	Write-Host '************************************'
	Write-Host 'Step 2. Preparing UI. Currently supporting:'
	Write-Host ' 1. Command-line UI (cmder)'
	Read-Host -Prompt 'Press any key to start...'
	
	Write-Host 'Step 2.1. preparing cmder...'
	$startup_cmd = @"
	
cd $anaconda_path\Scripts
call .\activate.bat
call activate AUTOMATA
cd $ui_path
python cli.py
"@
	Out-File -FilePath "$cmder_path\config\user_profile.cmd" -InputObject $startup_cmd -Encoding default -Append

	$Shell = New-Object -ComObject WScript.Shell
	$ShortCut = $Shell.CreateShortcut("$root_path\Automata (command-line).lnk")
	$ShortCut.TargetPath = "$cmder_path\Cmder.exe"
	$ShortCut.Save()
	Write-Host ' done'

	Write-Host ''
	Write-Host '************************************'
	Write-Host 'Installation completed! Thank you for your patience.'
	Read-Host -Prompt "Press any key to exit"
}