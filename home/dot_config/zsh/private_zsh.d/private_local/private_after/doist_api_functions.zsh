# API helper functions for Doist products

function tdapi() {
    : First you need to create a session with authentication to the todoist api
    : http --session=td -A bearer -a "$TD_API_TOKEN" https://api.todoist.com/api/v1/projects
    local url=$1
    shift
    if [[ $url != http* ]]; then
        if [[ $url != /* ]]; then
            url="/${url}"
        fi
        if [[ $url == /api* ]]; then
            url="https://api.todoist.com${url}"
        else
            url="https://api.todoist.com/api${url}"
        fi
    fi
    http --session-read-only=td "${url}" "${@}"
}

function twistapi() {
    : First you need to create a session with authentication to the twist api
    : http --session=twist -A bearer -a "$TWIST_TOKEN" https://api.twist.com/api/v3/users/get_session_user
    local url=$1
    shift
    if [[ $url != http* ]]; then
        if [[ $url != /* ]]; then
            url="/${url}"
        fi
        if [[ $url == /api* ]]; then
            url="https://api.twist.com${url}"
        else
            url="https://api.twist.com/api${url}"
        fi
    fi
    http --session-read-only=twist "${url}" "${@}"
}
