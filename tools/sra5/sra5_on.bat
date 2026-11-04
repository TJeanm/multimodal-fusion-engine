@echo off
pushd "%~dp0"

.\sra5.exe -b 127.255.255.255:2010 -g fusion_sra5_sapi.grxml -p on

popd