#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

if __name__ == "__main__":
    try:
        while True:
            time.sleep(86400)  # Sleep for 24 hours at a time
    except KeyboardInterrupt:
        print("\nExiting...")

