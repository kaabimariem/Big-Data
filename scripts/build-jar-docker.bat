@echo off
REM Compile le JAR MapReduce via Maven dans Docker (si Maven absent localement)
echo === Compilation MapReduce via Docker ===
docker run --rm -v "%cd%\mapreduce:/project" -w /project maven:3.9-eclipse-temurin-8 mvn clean package -DskipTests -q
if %ERRORLEVEL% EQU 0 (
    echo JAR cree: mapreduce\target\ecommerce-mapreduce-1.0-SNAPSHOT.jar
) else (
    echo Echec compilation. Utilisez IntelliJ IDEA avec Maven integre.
)
