Write-Host "================================" -ForegroundColor Green
Write-Host "Protobuf �������Զ���װ�ű�" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

$protocPath = "C:\protoc"
$zipPath = "$protocPath\protoc.zip"
$url = "https://github.com/protocolbuffers/protobuf/releases/download/v29.5/protoc-29.5-win64.zip"

Write-Host "����������ļ�..." -ForegroundColor Yellow
if (Test-Path $protocPath) {
    Remove-Item -Path $protocPath -Recurse -Force
}

Write-Host "���ڴ���Ŀ¼..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $protocPath -Force | Out-Null

Write-Host "�������� protoc..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $url -OutFile $zipPath
    Write-Host "������ɣ�" -ForegroundColor Green
} catch {
    Write-Host "����ʧ��: $_" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "���ڽ�ѹ..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $zipPath -DestinationPath $protocPath -Force
    Write-Host "��ѹ��ɣ�" -ForegroundColor Green
} catch {
    Write-Host "��ѹʧ��: $_" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "����������ʱ�ļ�..." -ForegroundColor Yellow
Remove-Item -Path $zipPath -Force

Write-Host "�������û�������..." -ForegroundColor Yellow
$binPath = "$protocPath\bin"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($currentPath -notlike "*$binPath*") {
    $newPath = "$currentPath;$binPath"
    try {
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        Write-Host "��������������ɣ�" -ForegroundColor Green
    } catch {
        Write-Host "��������������Ҫ����ԱȨ�ޣ����Թ���Ա������д˽ű�" -ForegroundColor Red
    }
}

Write-Host "================================" -ForegroundColor Green
Write-Host "��װ��ɣ�" -ForegroundColor Green
Write-Host "�����������У�Ȼ����������������֤��װ��" -ForegroundColor Green
Write-Host "protoc --version" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Green

pause