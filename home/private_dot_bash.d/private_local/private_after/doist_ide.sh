# IDE completion and upgrade

_DO_IDE_COMPLETE_FILE="$DO_IDE_DIR/ide/completion/ide-complete.bash"

if [[ ! -e $_DO_IDE_COMPLETE_FILE ]]; then
    echoe "Cannot find doist-ide completion file"
else
    # shellcheck source=/dev/null
    source "$_DO_IDE_COMPLETE_FILE"
fi

unset _DO_IDE_COMPLETE_FILE

function ide-upgrade() {
    cd "$DO_IDE_DIR" && uv tool upgrade doist-ide
}
