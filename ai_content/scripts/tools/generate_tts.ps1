param(
    [string]$Text = "Meet the next evolution of developer speed.",
    [string]$OutFile = "c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output\audio\test_vo.wav"
)

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile($OutFile)
$synth.Speak($Text)
$synth.Dispose()
Write-Host "TTS Generated: $OutFile"
