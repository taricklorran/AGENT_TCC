@echo off
echo Iniciando o AI Agent Worker com Dramatiq e 8 threads...

rem O correto é chamar o MÓDULO 'worker', sem a extensão '.py'
dramatiq worker --threads 1