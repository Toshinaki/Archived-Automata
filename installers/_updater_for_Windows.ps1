function Check-Existence {
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
		Write-Host ' Exiting...'
		exit
	}
}

$installation_bat_file = '.\installers\installing_python_libraries.bat'
Check-Existence -path $installation_bat_file -isfolder 0

$src_path1 = '\\erato.geniee.jp\share\20.運用\99.個人フォルダ\37.王\extra\MillenniumFalcon\core'
$src_path2 = '\\erato.geniee.jp\share\20.運用\99.個人フォルダ\37.王\extra\MillenniumFalcon\installers'
Check-Existence -path $src_path1 -isfolder 1
Check-Existence -path $src_path2 -isfolder 1

Write-Host 'Updating...'
Copy-Item $src_path1 -Destination '.\' -Recurse -Force
Copy-Item "$src_path2\*.txt" -Destination '.\installers' -Force
Write-Host 'Done'

Write-Host ''
Write-Host 'Installing Python libraries...'
$installation_process = & Start-Process cmd -Argument "/c .\installers\installing_python_libraries.bat" -Wait -PassThru
if ($installation_process.ExitCode -eq 0) {
	Write-Host ' Required Python libraries successfully installed'
} Else {
	Write-Host ' Installation of python libraries failed'
	Write-Host ' Consulting your administrator for a solution.'
}

Write-Host ''
Write-Host 'Updating completed!'
Read-Host -Prompt "Press any key to exit"