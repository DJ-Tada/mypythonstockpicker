#!/usr/bin/env zsh
# Central script to manage common env flags for helper scripts.
# Set AUTO_APPROVE=1 or AUTO_APPROVE=true in your shell to make helper scripts non-interactive.

AUTO_APPROVE_VAL=${AUTO_APPROVE:-}
if [[ -n "$AUTO_APPROVE_VAL" ]]; then
  case "${AUTO_APPROVE_VAL,,}" in
    1|true|yes|y)
      export AUTO_APPROVE=1
      ;;
    *)
      export AUTO_APPROVE=0
      ;;
  esac
else
  export AUTO_APPROVE=0
fi
