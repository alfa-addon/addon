#!/bin/bash
# 2025 (C) Alfa Development Group
# Developed by SistemaRayoXP

set -o errexit  # exit on any error
set -o pipefail # catch failures in pipelines

# Verify dependencies or exit
for cmd in xmlstarlet zip; do
    command -v "$cmd" >/dev/null || {
        echo >&2 "error: $cmd not installed"
        exit 1
    }
done

SHOW_VERSION=0
BUMP_MINOR=0
BUMP_MAJOR=0
BUMP_FEATURE=0
GENERATE_CHANGELOG=0
COMMIT_TO_GIT=0
CREATE_ZIP=0
SHOW_HELP=0
QUIET=0

if [ -z "${ADDON}" ]; then
    export ADDON='plugin.video.alfa'
fi

SCREENSHOT_PATH="$ADDON/resources/Screenshot.png"
CHANGELOG_PATH="$ADDON/changelog.txt"

while getopts "vbczqhg" opt; do
    case $opt in
    v) SHOW_VERSION=1 ;;
    b) BUMP_MINOR=1 ;;
    B) BUMP_MAJOR=1 ;;
    R) BUMP_FEATURE=1 ;;
    c) GENERATE_CHANGELOG=1 ;;
    g) COMMIT_TO_GIT=1 ;;
    z) CREATE_ZIP=1 ;;
    q) QUIET=1 ;;
    h) SHOW_HELP=1 ;;
    esac
done

if [ "$SHOW_HELP" -eq 1 ]; then
    cat <<EOF
$(basename "$0") help:
    -h Shows this help
    -b Bumps the minor add-on version by one
    -B Bumps the major add-on version by one
    -R Bumps the feature add-on version by one
    -c Update the add-on changelog and generate 'Screenshot.png'
    -g Commits any modifications to Git
    -z Creates a ZIP release of the add-on (not committed to Git)
    -v Outputs the add-on version
    -q Avoids unnecessary output (for scripting)
If multiple commands options are used, they're applied in the order displayed here
EOF
    exit 0
fi

# Make sure the path is correct
pushd "$(realpath "$(dirname "$0")/../")" >/dev/null
# Register a trap to switch back dirs on exit or error
trap 'popd &>/dev/null' EXIT

# Get current version
VERSION=$(xmlstarlet sel -t -m "//addon" -v "@version" "$ADDON/addon.xml")

if [ "$BUMP_MINOR" -eq 1 ]; then
    IFS='.' read -r X Y Z <<<"$VERSION"
    Z=$((Z + 1))
    VERSION="$X.$Y.$Z"
    xmlstarlet ed -L -u "//addon/@version" -v "$VERSION" "$ADDON/addon.xml"
fi

if [ "$BUMP_MAJOR" -eq 1 ]; then
    IFS='.' read -r X Y Z <<<"$VERSION"
    Y=$((Y + 1))
    VERSION="$X.$Y.$Z"
    xmlstarlet ed -L -u "//addon/@version" -v "$VERSION" "$ADDON/addon.xml"
fi

if [ "$BUMP_FEATURE" -eq 1 ]; then
    IFS='.' read -r X Y Z <<<"$VERSION"
    X=$((X + 1))
    VERSION="$X.$Y.$Z"
    xmlstarlet ed -L -u "//addon/@version" -v "$VERSION" "$ADDON/addon.xml"
fi

if [ "$GENERATE_CHANGELOG" -eq 1 ]; then
    LAST_TAG=$(git describe --tags --abbrev=0)
    CHANGED_FILES=$(git diff --name-only "$LAST_TAG" HEAD -- "$ADDON/channels/" |
        xargs -n1 basename |
        sed 's/\.[^.]*$//' |
        sort -u)
    ADULT_CHANGED=0
    SHOWN_FILES=()

    for entry in ${CHANGED_FILES[@]}; do
        json="${ADDON}/channels/${entry}.json"

        # check that the json exists
        [[ -f "$json" ]] || continue
        # check if an adult channel was changed
        (($ADULT_CHANGED == 0)) &&
            jq -e '.adult == true and .active == true' "$json" >/dev/null &&
            ADULT_CHANGED=1
        # check that channel is active and not adult
        jq -e '.adult == true or .active == false' "$json" >/dev/null && continue

        # if all checks passed, append the real channel name to the array
        SHOWN_FILES+=("$(jq -r '.name' "$json")")
    done

    ((ADULT_CHANGED == 1)) && SHOWN_FILES+=("+18")

    IFS=$'\n' SHOWN_FILES=($(sort <<<"${SHOWN_FILES[*]}"))

    python $(pwd)/scripts/changelog_generator.py ${SHOWN_FILES[*]} -c -v $VERSION -o $SCREENSHOT_PATH -l $CHANGELOG_PATH
fi

if [ "$COMMIT_TO_GIT" -eq 1 ]; then
    git config user.name "${GIT_USER_NAME:='Alfa Development Group'}"
    git config user.email "${GIT_USER_EMAIL:='145614550+alfa-addon@users.noreply.github.com'}"
    git add .
    git commit -q -m "Updated to version $VERSION"
    git push
fi

if [ "$CREATE_ZIP" -eq 1 ]; then
    [ "$QUIET" -eq 0 ] && echo "Zipping add-on..."
    export ZIP_FILE="${ADDON}-${VERSION}.zip"
    zip -q -r "$ZIP_FILE" "$ADDON" -x "*/__pycache__/*"
    [ "$QUIET" -eq 0 ] && echo "Zip created at $(realpath "$ZIP_FILE")" || realpath "$ZIP_FILE"
fi

if [ "$SHOW_VERSION" -eq 1 ]; then
    echo $VERSION
fi
