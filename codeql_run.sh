#!/usr/bin/env bash

ARCH="osx64" # osx,win
CODEQL_ZIP="codeql-${ARCH}64.zip"
CODEQL_TARGET_DIR="$HOME/codeql-home"

################################################################
#                       Install CodeQl.                        #
################################################################

if [ ! -d "$CODEQL_TARGET_DIR" ]; then
    echo "CodeQl doesn't exist. Installing..."
    
    if [ -f "$CODEQL_ZIP" ]; then
        echo "$CODEQL_ZIP exists"
    else
        echo "Downloading CodeQl zip file..."
        wget "https://github.com/github/codeql-cli-binaries/releases/download/v2.13.1/codeql-${ARCH}64.zip"
        echo "Done."
    fi
    
    echo "Unzipping..."
    unzip $CODEQL_ZIP -d $CODEQL_TARGET_DIR
    echo "Done."
else
    echo "Detected CodeQL at $CODEQL_TARGET_DIR."
fi

# Test codeql works with `codeql --version`
$CODEQL_TARGET_DIR/codeql/codeql --version
if [ $? -eq 0 ]; then
    echo "Codeql works!"
else
    echo "Codeql failed."
    exit $?
fi

################################################################
#                       Clone Rules.                           #
################################################################

if [ ! -d "$CODEQL_TARGET_DIR/ql" ]; then
    echo "Cloning CodeQl rules from repo..."
    git clone https://github.com/github/codeql.git "$CODEQL_TARGET_DIR/ql"
    echo "Done."
fi

################################################################
#                        Create DB & Run Rules.                #
################################################################

if [ -d "$PWD/vuln_apps" ]; then
    
    echo "vuln_apps directory detected, Running CodeQL on vuln_apps directory"
    DIR=$(ls -1 $PWD/vuln_apps)

    for dir in $DIR
    do
        if [ -d $PWD/vuln-app-db ]; then
            echo "Vulnerable App DB already exists! deleting.."
            rm -rf $PWD/vuln-app-db
            echo "Done."
        fi
        
        echo "Creating CodeQl db of OWASP Benchmark..."
        "$CODEQL_TARGET_DIR/codeql/codeql" database create "$PWD/vuln-app-db" --source-root="$PWD/vuln_apps/$dir" -l java
        echo "Done."
        
        echo "$PWD"
        $CODEQL_TARGET_DIR/codeql/codeql database analyze -j 0 --format=sarifv2.1.0 --output="results.sarif" --sarif-add-snippets --rerun "$PWD/vuln-app-db" "~/tools/cq/codeql-repo/javascript/ql/src/Security/"
        
        echo "Done."
    done
else
    if [ -d "$PWD/owasp-benchmark-codeql-db" ]; then
        echo "OWASP Benchmark CodeQl db already exists! deleting.."
        rm -rf "$PWD/owasp-benchmark-codeql-db"
        echo "Done."
    fi
    
    echo "Creating CodeQl db of OWASP Benchmark..."
    $CODEQL_TARGET_DIR/codeql/codeql database create "owasp-benchmark-codeql-db" \
    --source-root="$PWD" -l java
    echo "Done."
    
    echo "Executing CodeQl rules on db..."
    $CODEQL_TARGET_DIR/codeql/codeql database analyze -j 0 --format=sarifv2.1.0 \
    --output="$PWD/results/codeql_owasp_benchmark.sarif" --sarif-add-snippets --rerun \
    "$PWD/owasp-benchmark-codeql-db" "$HOME/codeql-home/ql/java/ql/src/Security/CWE/"
    echo "Done."
    
    echo "Script finished successfully!"
    exit 0
fi
