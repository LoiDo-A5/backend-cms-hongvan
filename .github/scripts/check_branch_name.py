import sys

branch_name = sys.argv[1]
parts = branch_name.split('/', 1)
prefix = parts[0]

if len(parts) == 2 and prefix.startswith('revert-'):
    sys.exit(0)

accept_prefixes = ['bugfix', 'bug', 'hotfix', 'fix', 'feature', 'refactor', 'chore', 'dependabot']

if prefix not in accept_prefixes:
    print(f'::error::Branch name must be started with {accept_prefixes}.', file=sys.stderr)
    sys.exit(1)
