param([string]$JobsFile,[int]$Limit=0)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
$asTask=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op,[Type]$type) {
  $task=$asTask.MakeGenericMethod($type).Invoke($null,@($op))
  $task.GetAwaiter().GetResult()
}
$engine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$jobs=Get-Content -LiteralPath $JobsFile -Raw -Encoding UTF8 | ConvertFrom-Json
$count=0
foreach($job in $jobs) {
  if(Test-Path -LiteralPath $job.out){continue}
  $file=Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($job.image)) ([Windows.Storage.StorageFile])
  $stream=Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder=Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap=Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $result=Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
  $lines=@($result.Lines | ForEach-Object { @{text=$_.Text;words=@($_.Words | ForEach-Object { @{text=$_.Text;x=$_.BoundingRect.X;y=$_.BoundingRect.Y;width=$_.BoundingRect.Width;height=$_.BoundingRect.Height} })} })
  @{id=$job.id;text=$result.Text;lines=$lines;engine='Windows.Media.Ocr zh-Hans-CN'} | ConvertTo-Json -Depth 8 -Compress | Set-Content -LiteralPath $job.out -Encoding UTF8
  $stream.Dispose();$bitmap.Dispose()
  $count++
  if($count % 10 -eq 0){Write-Output "OCR completed $count"}
  if($Limit -gt 0 -and $count -ge $Limit){break}
}
Write-Output "OCR finished $count"
