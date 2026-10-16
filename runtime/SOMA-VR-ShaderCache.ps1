# Update only the cached edge-glow fragment. SOMA ships translated GLSL as well
# as HPSL source; editing HPSL alone does not update that cached shader.
# Append first, then atomically replace the index: an interrupted write cannot
# make the old index refer to incomplete shader data. No unrelated offsets move.
function Update-SomaVrOutlineCache([string]$GameDirectory) {
    $ErrorActionPreference = 'Stop'
    Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility')
    $indexPath = Join-Path $GameDirectory '_shadersource\shadercache.xml'
    $bankPath = Join-Path $GameDirectory '_shadersource\shadersource.hpss'
    if (!(Test-Path -LiteralPath $indexPath) -or !(Test-Path -LiteralPath $bankPath)) { return }
    $xmlText = [IO.File]::ReadAllText($indexPath)
    $document = New-Object Xml.XmlDocument
    $document.PreserveWhitespace = $true
    $document.LoadXml($xmlText)
    $bank = [IO.File]::ReadAllBytes($bankPath)
    $encoding = New-Object Text.UTF8Encoding($false,$true)
    $additions = New-Object IO.MemoryStream
    $changed = 0
    $branch = @'
    // SOMA_VR_REMOTE_RIM_HM
    if(aColor.w > 1.5) {
        float facing = clamp(dot(normalize(px_vNormal), -normalize(px_vVertexPos)),0.0,1.0);
        float rim = pow(1.0-facing,2.0);
        // Keep front-facing flat targets visible.
        out_vColor = vec4(aColor.rgb*(0.20+2.0*rim),0.0);
        return;
    }

'@
    foreach ($entry in $document.SelectNodes('/ShaderCache/Cache/Shader')) {
        $vertex = $entry.GetAttribute('ShaderType') -eq '0' -and $entry.GetAttribute('Name').StartsWith('deferred_base_vtxMaterialType_EdgeGlow')
        $fragment = $entry.GetAttribute('ShaderType') -eq '1' -and $entry.GetAttribute('Name').StartsWith('game_edge_glow')
        if (!$vertex -and !$fragment) { continue }
        $start = [int]$entry.GetAttribute('SourceStart')
        $end = [int]$entry.GetAttribute('SourceEnd')
        if ($start -lt 0 -or $end -le $start -or $end -gt $bank.Length) { throw 'Invalid edge-glow shader cache range.' }
        $source = $encoding.GetString($bank,$start,$end-$start)
        if ($source.Contains('SOMA_VR_REMOTE_RIM_HM')) { continue }
        if (!$source.Contains('uniform cEdgeGlowArguments') -or !$source.Contains('vec4 aColor')) { throw 'Unrecognized edge-glow shader contract.' }
        if ($vertex) {
            $marker = $source.IndexOf('gl_Position = px_vPosition;')
            if ($marker -lt 0 -or !$source.Contains('px_vNormal')) { throw 'Unrecognized edge-glow vertex shader.' }
            $shell = @'
    // SOMA_VR_REMOTE_RIM_HM
    if(aColor.w > 1.5) {
        vec3 vrWorldNormal = (transpose(a_mtxView)*vec4(normalize(px_vNormal),0.0)).xyz;
        px_vPosition += a_mtxViewProjection*vec4(vrWorldNormal*0.003,0.0);
    }
'@
            $source = $source.Insert($marker,$shell)
        } else {
            $source = [regex]::Replace($source,'(?s)// SOMA_VR_REMOTE_RIM_HL.*?return;\s*}', '')
            $marker = $source.IndexOf('const float kGlowEdgeSharpness')
            if ($marker -lt 0) { throw 'Unrecognized edge-glow fragment shader.' }
            $source = $source.Insert($marker,$branch)
        }
        $bytes = $encoding.GetBytes($source)
        $entry.SetAttribute('SourceStart',[string]($bank.Length+$additions.Length))
        $additions.Write($bytes,0,$bytes.Length)
        $entry.SetAttribute('SourceEnd',[string]($bank.Length+$additions.Length))
        $changed++
    }
    if (!$changed) { $additions.Dispose(); return }
    # This branch runs only when the index points at an unpatched fragment.
    # Save this exact index and bank prefix; never restore over a later game update.
    $previousReceipt = $null
    if ((Test-Path -LiteralPath ($indexPath+'.soma-vr-receipt.json')) -and (Test-Path -LiteralPath ($indexPath+'.soma-vr-original'))) {
        $candidate = [IO.File]::ReadAllText($indexPath+'.soma-vr-receipt.json') | ConvertFrom-Json
        if ($candidate.PatchedHash -eq (Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant()) { $previousReceipt = $candidate }
    }
    if (!$previousReceipt) { [IO.File]::Copy($indexPath,$indexPath+'.soma-vr-original',$true) }
    $hash=[Security.Cryptography.SHA256]::Create()
    try { $bankHash=[BitConverter]::ToString($hash.ComputeHash($bank)).Replace('-','').ToLowerInvariant() } finally { $hash.Dispose() }
    $originalHash=(Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $stream = [IO.File]::Open($bankPath,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {
        if ($stream.Length -ne $bank.Length) { throw 'Shader cache changed while preparing the update. Please retry.' }
        [void]$stream.Seek(0,[IO.SeekOrigin]::End)
        $extra=$additions.ToArray();$stream.Write($extra,0,$extra.Length);$stream.Flush($true)
    } finally { $stream.Dispose();$additions.Dispose() }
    $temporary=$indexPath+'.'+[Guid]::NewGuid().ToString('N')+'.tmp'
    try {
        $document.Save($temporary)
        $receipt=@{IndexHash=$originalHash;BankLength=$bank.Length;BankHash=$bankHash;PatchedHash=(Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()}
        if ($previousReceipt) { $receipt.IndexHash=$previousReceipt.IndexHash; $receipt.BankLength=$previousReceipt.BankLength; $receipt.BankHash=$previousReceipt.BankHash }
        [IO.File]::WriteAllText($indexPath+'.soma-vr-receipt.json',($receipt | ConvertTo-Json),$encoding)
        [IO.File]::Replace($temporary,$indexPath,[NullString]::Value)
    } finally { if(Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary } }
    Write-Output 'VR target outline shader cache updated.'
}
