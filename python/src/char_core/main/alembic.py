import sys

import alembic.config


def main():
    alembic.config.main(sys.argv[1:])
